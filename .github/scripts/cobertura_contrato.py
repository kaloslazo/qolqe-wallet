"""Cobertura de la API: qué prueban nuestros escenarios y qué prueba Schemathesis, a partir de los logs de la app.

Uso:
  python .github/scripts/cobertura_contrato.py \
      --openapi reportes/schemathesis/openapi.json \
      --log-api reportes/log-api.txt --log-contrato reportes/schemathesis/log-contrato.txt \
      --junit-contrato reportes/schemathesis/junit-*.xml \
      --md docs/cobertura-contrato.md

Cada línea del log de uvicorn ("PUT /api/limites/alertas/7 HTTP/1.1" 422) se lleva a su operación del OpenAPI
(PUT /api/limites/alertas/{alerta_id}). Por operación se comparan los códigos HTTP que provocó cada suite y se
cruzan con los hallazgos del JUnit de Schemathesis. Una brecha es un código o un hallazgo que solo vio Schemathesis:
un caso que a nuestros escenarios les falta.
"""
import argparse
import glob
import html
import json
import re
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

METODOS = ("get", "post", "put", "delete", "patch")
LINEA_LOG = re.compile(r'"(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) HTTP/[\d.]+" (\d{3})')
CURL = re.compile(r"curl -X (\w+) .*?https?://[^/\s']+(/[^\s'?]*)")
HALLAZGO = re.compile(r"^- (?:(ST\d+) )?(.+)$", re.M)
RESPUESTA = re.compile(r"^\[(\d{3})\]", re.M)
# rutas que no son del producto
FUERA = re.compile(r"^/api/(pruebas|salud)")
ANSI = re.compile(r"\x1b\[[0-9;]*m")


@dataclass
class Operacion:
    metodo: str
    ruta: str
    api: Counter = field(default_factory=Counter)
    contrato: Counter = field(default_factory=Counter)
    hallazgos: list = field(default_factory=list)  # (código ST o "", título, status de la respuesta)

    @property
    def nombre(self):
        return f"{self.metodo} {self.ruta}"

    @property
    def solo_contrato(self):
        """Códigos HTTP que provocó Schemathesis y ninguno de nuestros escenarios."""
        return sorted(set(self.contrato) - set(self.api))

    @property
    def faltantes(self):
        """Códigos que vio Schemathesis (en el log o en un hallazgo) y ningún escenario nuestro."""
        return sorted(set(self.solo_contrato) | {h[2] for h in self.hallazgos if h[2] and h[2] not in self.api})

    @property
    def brecha(self):
        if not self.api and (self.contrato or self.hallazgos):
            return "sin escenarios nuestros"
        if self.faltantes:
            return "faltan casos"
        if self.hallazgos:
            return "hallazgo ya cubierto"
        return "cubierto" if self.api else "sin pruebas"


def plantillas(openapi):
    """[(metodo, ruta, regex)] de las operaciones del OpenAPI, primero las rutas sin parámetros."""
    ops = []
    for ruta, metodos in openapi["paths"].items():
        patron = re.compile("^" + re.sub(r"\\\{[^}]+\\\}", "[^/]+", re.escape(ruta)) + "$")
        for metodo in metodos:
            if metodo in METODOS:
                ops.append((metodo.upper(), ruta, patron))
    return sorted(ops, key=lambda o: o[1].count("{"))


def operacion_de(ops, metodo, ruta):
    ruta = ruta.split("?")[0]
    return next(((m, r) for m, r, p in ops if m == metodo and p.match(ruta)), None)


def leer_log(ruta, ops, destino, lado):
    if not ruta or not Path(ruta).exists():
        return False
    for linea in Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines():
        coincide = LINEA_LOG.search(linea)
        if not coincide or FUERA.match(coincide.group(2)):
            continue
        clave = operacion_de(ops, coincide.group(1), coincide.group(2))
        if clave and clave[1].startswith("/api/"):
            op = destino.setdefault(clave, Operacion(*clave))
            getattr(op, lado)[coincide.group(3)] += 1
    return True


def leer_hallazgos(rutas, ops, destino):
    for ruta in rutas:
        for caso in ET.parse(ruta).getroot().iter("testcase"):
            for fallo in caso.findall("failure"):
                texto = ANSI.sub("", fallo.text or fallo.get("message") or "")
                metodo, _, camino = caso.get("name", "").partition(" ")
                clave = (metodo, camino) if (metodo, camino) in {(m, r) for m, r, _ in ops} else None
                if clave is None:  # fase stateful u OPTIONS: la operación es la del último curl
                    curls = CURL.findall(texto)
                    if curls:
                        metodo, camino = curls[-1]
                        # un OPTIONS no es una operación del OpenAPI: se anota en la primera de esa ruta
                        clave = operacion_de(ops, metodo, camino) or next(
                            ((m, r) for m, r, p in ops if p.match(camino.split("?")[0])), None)
                if clave is None:
                    continue
                titulo = HALLAZGO.search(texto)
                status = RESPUESTA.search(texto)
                op = destino.setdefault(clave, Operacion(*clave))
                op.hallazgos.append((titulo.group(1) or "" if titulo else "", titulo.group(2).strip() if titulo else "hallazgo",
                                     status.group(1) if status else ""))


def analizar(openapi, log_api, log_contrato, junit_contrato):
    ops = plantillas(json.loads(Path(openapi).read_text(encoding="utf-8")))
    operaciones: dict = {}
    hay_api = leer_log(log_api, ops, operaciones, "api")
    hay_contrato = leer_log(log_contrato, ops, operaciones, "contrato")
    leer_hallazgos(junit_contrato, ops, operaciones)
    del_producto = sum(1 for _, r, _ in ops if r.startswith("/api/") and not FUERA.match(r))
    filas = sorted(operaciones.values(), key=lambda o: (not o.ruta.startswith("/api/limites"), o.ruta, o.metodo))
    return filas, {"api": hay_api, "contrato": hay_contrato, "total": del_producto}


def _codigos(conteo):
    return ", ".join(f"{c} ×{n}" for c, n in sorted(conteo.items())) or "—"


def _hallazgos(op, sep):
    agrupados = Counter(f"{st} {titulo} → {status}".strip() for st, titulo, status in op.hallazgos)
    return sep.join(f"{t}" + (f" (×{n})" if n > 1 else "") for t, n in agrupados.items()) or "—"


def _lectura(op):
    return f"{op.brecha}: {', '.join(op.faltantes)}" if op.brecha == "faltan casos" else op.brecha


def resumen(filas, meta):
    probadas = [o for o in filas if o.api or o.contrato]
    return {
        "operaciones": len(probadas),
        "total": meta["total"],
        "nuestras": sum(1 for o in probadas if o.api),
        "contrato": sum(1 for o in probadas if o.contrato),
        "faltan": [o for o in filas if o.brecha in ("faltan casos", "sin escenarios nuestros")],
    }


def a_markdown(filas, meta):
    r = resumen(filas, meta)
    lineas = [
        "# Cobertura de la API: nuestros escenarios frente a Schemathesis", "",
        f"Operaciones del producto probadas: **{r['operaciones']}** de {r['total']} · con nuestros escenarios: "
        f"**{r['nuestras']}** · con Schemathesis: **{r['contrato']}** · con casos que nos faltan: **{len(r['faltan'])}**.", "",
        "Sale de los logs de la app en cada suite: cada solicitud se lleva a su operación del OpenAPI y se cuentan los "
        "códigos HTTP. *Solo Schemathesis* son los códigos que él provocó y nuestros escenarios no.", "",
        "| Operación | Nuestros escenarios | Schemathesis | Solo Schemathesis | Hallazgos | Lectura |",
        "|---|---|---|---|---|---|",
    ]
    for o in filas:
        lineas.append(f"| `{o.nombre}` | {_codigos(o.api)} | {_codigos(o.contrato)} | {', '.join(o.solo_contrato) or '—'} "
                      f"| {_hallazgos(o, '<br>')} | {_lectura(o)} |")
    if not meta["api"] or not meta["contrato"]:
        lineas += ["", f"> Falta el log de {'la API' if not meta['api'] else 'Schemathesis'}: la comparación está incompleta."]
    return "\n".join(lineas) + "\n"


def a_html(filas, meta):
    e = html.escape
    r = resumen(filas, meta)
    clase = {"cubierto": "passed", "hallazgo ya cubierto": "xfailed", "faltan casos": "failed",
             "sin escenarios nuestros": "failed", "sin pruebas": "skipped"}
    cuerpo = "\n".join(
        f"<tr><td><code>{e(o.nombre)}</code></td><td>{e(_codigos(o.api))}</td><td>{e(_codigos(o.contrato))}</td>"
        f"<td>{e(', '.join(o.solo_contrato) or '—')}</td><td>{'<br>'.join(e(h) for h in _hallazgos(o, chr(10)).splitlines())}</td>"
        f'<td class="{clase[o.brecha]}">{e(_lectura(o))}</td></tr>'
        for o in filas)
    aviso = "" if meta["api"] and meta["contrato"] else '<p class="sub">Falta uno de los logs: la comparación está incompleta.</p>'
    return f"""<h2 id="cobertura-contrato">Cobertura de la API: nuestros escenarios frente a Schemathesis</h2>
<p class="sub">{r['operaciones']} de {r['total']} operaciones probadas · {r['nuestras']} con nuestros escenarios ·
{r['contrato']} con Schemathesis · <strong>{len(r['faltan'])} con casos que nos faltan</strong>.
Sale de los logs de la app: cada solicitud se lleva a su operación del OpenAPI y se cuentan los códigos HTTP.
<a href="cobertura-contrato.html">Ver la comparativa, quién probó qué →</a></p>
{aviso}
<table>
<thead><tr><th>Operación</th><th>Nuestros escenarios</th><th>Schemathesis</th><th>Solo Schemathesis</th><th>Hallazgos</th><th>Lectura</th></tr></thead>
<tbody>
{cuerpo}
</tbody>
</table>"""


ST = {"ST201": "aceptó una solicitud que viola el esquema", "ST202": "rechazó una solicitud válida según el esquema",
      "ST205": "el header Allow no coincide con el 405"}


def _modulo(o):
    if o.ruta.startswith("/api/limites"):
        return "G5 · Límites"
    if o.ruta.split("/")[2] in ("auth", "cuentas", "usuarios", "transferencias"):
        return "Núcleo común"
    return "Apoyo de otros módulos (los usan nuestros escenarios, no son de G5)"


def _quien(o):
    if o.api and o.contrato:
        return "ambos", "Ambos"
    if o.api:
        return "nosotros", "Solo nuestros escenarios"
    if o.contrato:
        return "schema", "Solo Schemathesis"
    return "nadie", "Nadie"


def a_pagina(filas, meta):
    """HTML aparte: una comparativa por operación de quién la probó (nosotros, Schemathesis o ambos)."""
    e = html.escape
    r = resumen(filas, meta)
    probadas = [o for o in filas if o.api or o.contrato]
    cuenta = Counter(_quien(o)[0] for o in probadas)
    brechas = [o for o in probadas if o.brecha in ("faltan casos", "sin escenarios nuestros")]

    def chips(conteo, otro, solo_clase):
        if not conteo:
            return '<span class="nada">no la probó</span>'
        return "".join(f'<span class="c {"ok" if c in otro else solo_clase}">{e(c)}<i>×{n}</i></span>' for c, n in sorted(conteo.items()))

    def hallazgos(o):
        agr = Counter((st, titulo, status) for st, titulo, status in o.hallazgos)
        return "".join(f'<div class="h"><b>{e(st or "—")}</b> {e(ST.get(st, titulo))}'
                       + (f' <span class="c hall">{e(status)}</span>' if status else "")
                       + (f" <i>×{n}</i>" if n > 1 else "") + "</div>" for (st, titulo, status), n in agr.items()) or '<span class="nada">—</span>'

    grupos = {}
    for o in probadas:
        grupos.setdefault(_modulo(o), []).append(o)
    bloques = []
    for modulo in sorted(grupos, key=lambda m: (m != "G5 · Límites", m != "Núcleo común", m)):
        filas_html = []
        for o in grupos[modulo]:
            q, texto = _quien(o)
            falta = (f'<div class="falta">Nos falta provocar: <b>{e(", ".join(o.faltantes))}</b></div>' if o.faltantes
                     else '<div class="bien">Sin casos pendientes</div>')
            filas_html.append(
                f'<tr data-q="{q}" data-brecha="{"si" if o in brechas else "no"}"><td><code>{e(o.nombre)}</code></td>'
                f'<td>{chips(o.api, set(o.contrato), "solo-n")}</td><td>{chips(o.contrato, set(o.api), "solo-s")}</td>'
                f'<td><span class="q q-{q}">{texto}</span>{falta}</td><td>{hallazgos(o)}</td></tr>')
        bloques.append(f'<h2>{e(modulo)} <i>{len(grupos[modulo])} operaciones</i></h2><table><thead><tr><th>Operación</th>'
                       f'<th>Nuestros escenarios<br><small>códigos HTTP que provocaron</small></th><th>Schemathesis<br><small>códigos HTTP que provocó</small></th>'
                       f'<th>Quién la probó</th><th>Hallazgos de Schemathesis</th></tr></thead><tbody>{"".join(filas_html)}</tbody></table>')
    aviso = "" if meta["api"] and meta["contrato"] else '<p class="aviso">Falta uno de los logs: la comparación está incompleta.</p>'
    return f"""<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Cobertura del contrato · quién probó qué</title><style>
:root{{color-scheme:dark}}body{{font:15px/1.5 system-ui,sans-serif;background:#12161c;color:#e6edf3;margin:0}}main{{max-width:1180px;margin:0 auto;padding:34px 20px 70px}}
h1{{margin:0 0 4px}}h2{{color:#9aa7b5;font-size:17px;margin:34px 0 10px}}h2 i{{font-style:normal;font-size:12px;color:#6e7681;margin-left:8px}}.sub{{color:#8b949e;font-size:13px;margin:0}}
.ks{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0 10px}}.k{{background:#1b222c;border:1px solid #2a3340;border-top:3px solid;border-radius:12px;padding:15px 18px}}
.k b{{display:block;font-size:32px}}.k span{{color:#8b949e;font-size:13px}}.k1{{border-top-color:#3fb97f}}.k2{{border-top-color:#58a6ff}}.k3{{border-top-color:#f0716a}}.k4{{border-top-color:#e3b341}}
.leyenda{{background:#1b222c;border:1px solid #2a3340;border-radius:10px;padding:12px 16px;margin:14px 0;font-size:13px;color:#b6c2cf}}.leyenda .c{{margin-right:4px}}
.filtros{{margin:16px 0 0}}.filtros button{{background:#1b222c;color:#e6edf3;border:1px solid #2a3340;border-radius:20px;padding:6px 14px;margin-right:6px;cursor:pointer;font:inherit;font-size:13px}}.filtros button.on{{background:#264a73;border-color:#58a6ff}}
table{{width:100%;border-collapse:collapse;background:#1b222c;border:1px solid #2a3340;border-radius:10px;overflow:hidden}}th{{text-align:left;font-size:12px;color:#8b949e;padding:10px 12px;border-bottom:1px solid #2a3340;font-weight:600}}th small{{font-weight:400;color:#6e7681}}
td{{padding:10px 12px;border-top:1px solid #232b36;vertical-align:top}}td code{{font-size:13px}}
.c{{display:inline-block;font:600 12px ui-monospace,monospace;border-radius:6px;padding:2px 8px;margin:2px 4px 2px 0;border:1px solid}}.c i{{font-style:normal;font-weight:400;opacity:.7;margin-left:4px}}
.ok{{background:#12372a;border-color:#2b6b4c;color:#6fdba5}}.solo-n{{background:#14304f;border-color:#2c5d93;color:#79b8ff}}.solo-s{{background:#40201e;border-color:#8a3b36;color:#ffa198}}.hall{{background:#3a2f10;border-color:#7a6221;color:#e3b341}}
.nada{{color:#6e7681;font-size:13px}}.q{{display:inline-block;font-size:12px;font-weight:600;border-radius:10px;padding:2px 10px}}.q-ambos{{background:#12372a;color:#6fdba5}}.q-nosotros{{background:#14304f;color:#79b8ff}}.q-schema{{background:#40201e;color:#ffa198}}.q-nadie{{background:#222a35;color:#8b949e}}
.falta{{color:#ffa198;font-size:13px;margin-top:5px}}.bien{{color:#6fdba5;font-size:12px;margin-top:5px}}.h{{font-size:13px;margin:2px 0}}.h b{{color:#e3b341}}.h i{{color:#8b949e;font-style:normal}}.aviso{{color:#e3b341}}
tr.oculta{{display:none}}</style><main>
<h1>Cobertura del contrato · quién probó qué</h1>
<p class="sub">Cada solicitud que recibió la app se lleva a su operación del OpenAPI y se cuentan los códigos HTTP, por separado para nuestros escenarios (Playwright) y para Schemathesis.
{r['operaciones']} de las {r['total']} operaciones del OpenAPI recibieron pruebas; el resto son de módulos de otros grupos.</p>{aviso}
<div class="ks"><div class="k k1"><b>{cuenta['ambos']}</b><span>operaciones probadas por ambos</span></div>
<div class="k k2"><b>{cuenta['nosotros']}</b><span>solo por nuestros escenarios</span></div>
<div class="k k3"><b>{len(brechas)}</b><span>con casos que nos faltan (Schemathesis vio algo que nosotros no)</span></div>
<div class="k k4"><b>{sum(len(o.hallazgos) for o in probadas)}</b><span>hallazgos de Schemathesis</span></div></div>
<div class="leyenda"><b>Cómo leerlo.</b> Cada chip es un código HTTP con las veces que se provocó.
<span class="c ok">200<i>×3</i></span> lo provocaron ambos · <span class="c solo-n">422<i>×8</i></span> solo nuestros escenarios · <span class="c solo-s">401<i>×3</i></span> solo Schemathesis, o sea un caso que nos falta ·
<span class="c hall">405</span> código de respuesta de un hallazgo.</div>
<div class="filtros"><button class="on" data-f="todas">Todas</button><button data-f="brecha">Nos faltan casos</button><button data-f="ambos">Probadas por ambos</button><button data-f="nosotros">Solo nuestros escenarios</button></div>
{"".join(bloques)}
</main><script>
document.querySelectorAll('.filtros button').forEach(b=>b.onclick=()=>{{document.querySelectorAll('.filtros button').forEach(x=>x.classList.remove('on'));b.classList.add('on');
const f=b.dataset.f;document.querySelectorAll('tbody tr').forEach(t=>{{const ver=f==='todas'||(f==='brecha'&&t.dataset.brecha==='si')||t.dataset.q===f;t.classList.toggle('oculta',!ver)}})}});
</script></html>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--openapi", required=True)
    p.add_argument("--log-api")
    p.add_argument("--log-contrato")
    p.add_argument("--junit-contrato", nargs="*", default=[])
    p.add_argument("--md")
    p.add_argument("--html")
    a = p.parse_args()
    junit = [r for patron in a.junit_contrato for r in sorted(glob.glob(patron))]
    filas, meta = analizar(a.openapi, a.log_api, a.log_contrato, junit)
    texto = a_markdown(filas, meta)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
    if a.html:
        Path(a.html).write_text(a_pagina(filas, meta), encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
