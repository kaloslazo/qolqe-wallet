#!/usr/bin/env python3
"""Reporte BDD de la API: lee resultados-api.json de Playwright y arma un HTML con los pasos Gherkin de cada
escenario, igual que el reporte BDD de la web. Un fallo esperado (@fail, con su DEF) se muestra como
«Defecto conocido» y no como un pase: Playwright lo cuenta como passed porque falló como se esperaba.

Uso: python .github/scripts/reporte_bdd_api.py resultados-api.json salida.html"""
import html, json, re, sys
from collections import OrderedDict
from datetime import datetime

ANSI = re.compile(r"\x1b\[[0-9;]*m")
esc = lambda s: html.escape(str(s))


def recorrer(suite, acc):
    for sp in suite.get("specs", []):
        for t in sp["tests"]:
            r = t["results"][-1] if t["results"] else {}
            esperado_fallo = t.get("expectedStatus") == "failed"
            estado = r.get("status", "skipped")
            if estado == "skipped":
                clase = "omitido"
            elif esperado_fallo and estado == "failed":
                clase = "defecto"
            elif estado == "passed" and not esperado_fallo:
                clase = "paso"
            else:
                clase = "fallo"
            acc.append(dict(archivo=sp["file"], titulo=sp["title"], tags=sp.get("tags", []), clase=clase,
                            ms=r.get("duration", 0), pasos=r.get("steps", []),
                            error=ANSI.sub("", (r.get("errors") or [{}])[0].get("message", ""))))
    for c in suite.get("suites", []):
        recorrer(c, acc)


def main(entrada, salida):
    datos = json.load(open(entrada, encoding="utf-8"))
    pruebas = []
    for s in datos["suites"]:
        recorrer(s, pruebas)
    cuenta = {k: sum(1 for p in pruebas if p["clase"] == k) for k in ("paso", "defecto", "fallo", "omitido")}
    fecha = datetime.fromisoformat(datos["stats"]["startTime"].replace("Z", "+00:00")).astimezone().strftime("%d/%m/%Y %H:%M")

    def pasos(p):
        filas = []
        for i, st in enumerate(p["pasos"]):
            mal = "error" in st
            filas.append(f'<li class="{"mal" if mal else "ok"}"><span>{"✗" if mal else "✓"}</span> {esc(st["title"])}'
                         + (f'<pre>{esc(ANSI.sub("", st["error"].get("message", ""))[:420] if isinstance(st["error"], dict) else p["error"][:420])}</pre>' if mal else "") + "</li>")
        return "<ul>" + "".join(filas) + "</ul>"

    def etiquetas(p):
        return "".join(f'<code class="{"def" if t.startswith("DEF") else ""}">@{esc(t)}</code>' for t in p["tags"] if t not in ("api", "fail"))

    def bloque(p, abierto=False):
        defe = next((t for t in p["tags"] if t.startswith("DEF-")), "")
        nota = f'<p class="nota">Defecto conocido {esc(defe)} (docs/defectos.md): falla como se espera y por eso Playwright lo cuenta como passed.</p>' if p["clase"] == "defecto" else ""
        rot = {"paso": "Pasó", "defecto": "Defecto conocido", "fallo": "Falló", "omitido": "Omitido"}[p["clase"]]
        return (f'<details class="{p["clase"]}"{" open" if abierto else ""}><summary><b class="b-{p["clase"]}">{rot}</b> '
                f'<span class="t">{esc(p["titulo"])}</span> {etiquetas(p)} <i>{p["ms"] / 1000:.1f} s</i></summary>{nota}{pasos(p)}</details>')

    defectos = [p for p in pruebas if p["clase"] in ("defecto", "fallo")]
    por_archivo = OrderedDict()
    for p in pruebas:
        if p["clase"] == "paso":
            por_archivo.setdefault(p["archivo"], []).append(p)
    secciones = "".join(f'<details class="arch"><summary>{esc(a.replace(".spec.js", ""))} <i>{len(l)} escenarios que pasan</i></summary>{"".join(bloque(p) for p in l)}</details>'
                        for a, l in por_archivo.items())
    kpis = "".join(f'<div class="k k-{c}"><b>{cuenta[c]}</b><span>{t}</span></div>'
                   for c, t in (("paso", "Pasó"), ("defecto", "Defecto conocido"), ("fallo", "Falló"), ("omitido", "Omitido")))
    barra = "".join(f'<i class="s-{c}" style="width:{100 * cuenta[c] / max(len(pruebas), 1):.2f}%"></i>' for c in ("paso", "defecto", "fallo", "omitido"))
    open(salida, "w", encoding="utf-8").write(f"""<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reporte BDD · API · G5 Límites</title><style>
:root{{color-scheme:dark}}body{{font:15px/1.5 system-ui,sans-serif;background:#12161c;color:#e6edf3;margin:0}}main{{max-width:1080px;margin:0 auto;padding:36px 20px 60px}}
h1{{margin:0 0 4px}}.meta{{color:#8b949e;font-size:13px}}h2{{color:#8b949e;font-size:17px;margin:30px 0 10px}}
.ks{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:22px 0 14px}}.k{{background:#1b222c;border:1px solid #2a3340;border-top:3px solid;border-radius:12px;padding:16px 18px}}
.k b{{display:block;font-size:34px}}.k span{{color:#8b949e;font-size:13px}}.k-paso{{border-top-color:#3fb97f}}.k-defecto{{border-top-color:#e3b341}}.k-fallo{{border-top-color:#f0716a}}.k-omitido{{border-top-color:#6e7681}}
.barra{{display:flex;height:8px;border-radius:4px;overflow:hidden;background:#222a35}}.s-paso{{background:#3fb97f}}.s-defecto{{background:#e3b341}}.s-fallo{{background:#f0716a}}.s-omitido{{background:#6e7681}}
details{{background:#1b222c;border:1px solid #2a3340;border-radius:10px;margin:8px 0;padding:0}}details.defecto{{border-left:4px solid #e3b341}}details.fallo{{border-left:4px solid #f0716a}}
summary{{cursor:pointer;padding:11px 14px;list-style:none}}summary::-webkit-details-marker{{display:none}}summary i{{float:right;color:#8b949e;font-style:normal;font-size:12px}}
.t{{font-weight:600}}.b-paso,.b-defecto,.b-fallo,.b-omitido{{font-size:11px;padding:2px 8px;border-radius:10px;margin-right:6px}}.b-paso{{background:#12372a;color:#3fb97f}}.b-defecto{{background:#3a2f10;color:#e3b341}}.b-fallo{{background:#40201e;color:#f0716a}}
code{{font-size:11px;background:#222a35;color:#9db4cf;border-radius:5px;padding:1px 6px;margin-left:4px}}code.def{{color:#e3b341}}
ul{{list-style:none;margin:0;padding:0 14px 12px}}li{{padding:5px 0;border-top:1px solid #232b36}}li span{{display:inline-block;width:20px;font-weight:700}}li.ok span{{color:#3fb97f}}li.mal span{{color:#f0716a}}
pre{{background:#3a1e1c;color:#ffb4ad;border-radius:6px;padding:8px 10px;white-space:pre-wrap;font-size:12px;margin:6px 0 0 20px}}.nota{{color:#e3b341;font-size:13px;margin:0 14px 6px}}.arch>summary{{font-weight:600}}.arch details{{margin:6px 14px}}
</style><main><h1>Reporte BDD · API · G5 Límites</h1>
<div class="meta">Playwright + playwright-bdd · Escenarios: <b>{len(pruebas)}</b> · {fecha}</div>
<div class="ks">{kpis}</div><div class="barra">{barra}</div>
<h2>Defectos conocidos vistos desde la API ({len(defectos)})</h2>{"".join(bloque(p, i == 0) for i, p in enumerate(defectos))}
<h2>Escenarios que pasan, por archivo</h2>{secciones}</main></html>""")
    print(f"{salida}: {len(pruebas)} escenarios · {cuenta}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
