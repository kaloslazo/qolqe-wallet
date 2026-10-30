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
    return f"""<h2>Cobertura de la API: nuestros escenarios frente a Schemathesis</h2>
<p class="sub">{r['operaciones']} de {r['total']} operaciones probadas · {r['nuestras']} con nuestros escenarios ·
{r['contrato']} con Schemathesis · <strong>{len(r['faltan'])} con casos que nos faltan</strong>.
Sale de los logs de la app: cada solicitud se lleva a su operación del OpenAPI y se cuentan los códigos HTTP.</p>
{aviso}
<table>
<thead><tr><th>Operación</th><th>Nuestros escenarios</th><th>Schemathesis</th><th>Solo Schemathesis</th><th>Hallazgos</th><th>Lectura</th></tr></thead>
<tbody>
{cuerpo}
</tbody>
</table>"""


def main():
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--openapi", required=True)
    p.add_argument("--log-api")
    p.add_argument("--log-contrato")
    p.add_argument("--junit-contrato", nargs="*", default=[])
    p.add_argument("--md")
    a = p.parse_args()
    junit = [r for patron in a.junit_contrato for r in sorted(glob.glob(patron))]
    filas, meta = analizar(a.openapi, a.log_api, a.log_contrato, junit)
    texto = a_markdown(filas, meta)
    if a.md:
        Path(a.md).write_text(texto, encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
