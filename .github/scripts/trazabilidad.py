"""Matriz de trazabilidad HU -> caso -> resultado, a partir de los .feature y de los resultados de un run.

Uso:
  python .github/scripts/trazabilidad.py \
      --api reportes/resultados-api.json \
      --web chrome=reportes/selenium/junit.xml --web firefox=ruta/a/otro/junit.xml \
      --md docs/trazabilidad.md --html sitio/trazabilidad.html

Cada escenario lleva una etiqueta @CP-NN; esa etiqueta une el .feature con el resultado:
  - API (Playwright): el reporter JSON trae las etiquetas de cada test y la anotación "fail" de los @fail.
  - Web (pytest-bdd): el conftest escribe las etiquetas HU, CP y DEF como propiedad "etiquetas" del JUnit XML.
"""
import argparse
import html
import json
import os
import re
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
ESCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario|Esquema del escenario|Escenario):\s*(.+)$")
FEATURE = re.compile(r"^\s*(Feature|Característica):")
EJEMPLOS = re.compile(r"^\s*(Examples|Scenarios|Ejemplos):")
HU_TITULO = re.compile(r"^### (HU-[A-Z0-9]+-\d+) · ([^·]+)")
LIMA = timezone(timedelta(hours=-5))


def leer_casos():
    """CP -> {nombre, archivo, nivel, hu: [...], defectos: [...]}"""
    casos = {}
    for archivo in sorted((RAIZ / "features").rglob("*.feature")):
        etiquetas_feature, pendientes, ultimo = [], [], None
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            texto = linea.strip()
            if texto.startswith("@"):
                pendientes += [t[1:] for t in texto.split() if t.startswith("@")]
            elif FEATURE.match(linea):
                etiquetas_feature, pendientes = pendientes, []
            elif m := ESCENARIO.match(linea):
                etiquetas = etiquetas_feature + pendientes
                pendientes = []
                cp = next((t for t in etiquetas if t.startswith("CP-")), None)
                if cp:
                    ultimo = casos[cp] = {
                        "nombre": m.group(2).strip(),
                        "archivo": archivo.relative_to(RAIZ).as_posix(),
                        "nivel": "web" if "ui" in archivo.relative_to(RAIZ / "features").parts[:-1] else "api",
                        "hu": [t for t in etiquetas if t.startswith("HU-")],
                        "defectos": [t for t in etiquetas if t.startswith("DEF-")],
                    }
            elif EJEMPLOS.match(linea):
                # un bloque Examples puede tener su propia etiqueta @DEF (solo esos ejemplos fallan)
                if ultimo:
                    ultimo["defectos"] += [t for t in pendientes if t.startswith("DEF-") and t not in ultimo["defectos"]]
                pendientes = []
            elif texto and not texto.startswith("#"):
                pendientes = []
    return casos


def leer_historias():
    historias = {}
    for linea in (RAIZ / "docs/requisitos.md").read_text(encoding="utf-8").splitlines():
        if m := HU_TITULO.match(linea):
            historias[m.group(1)] = m.group(2).strip()
    return historias


def resultados_api(ruta):
    """CP -> lista de estados ('passed', 'failed', 'skipped', 'xfailed', 'flaky') del JSON de Playwright."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    res = defaultdict(list)

    def recorrer(suite):
        for spec in suite.get("specs", []):
            cp = next((t.lstrip("@") for t in spec["tags"] if t.lstrip("@").startswith("CP-")), None)
            for test in spec["tests"]:
                esperado_falla = any(a["type"] == "fail" for a in test["annotations"])
                estado = {"expected": "xfailed" if esperado_falla else "passed", "unexpected": "failed",
                          "skipped": "skipped", "flaky": "flaky"}[test["status"]]
                if cp:
                    res[cp].append(estado)
        for hija in suite.get("suites", []):
            recorrer(hija)

    for suite in datos["suites"]:
        recorrer(suite)
    return res


def resultados_junit(ruta):
    """CP -> lista de estados, del JUnit XML de pytest con la propiedad 'etiquetas'."""
    res = defaultdict(list)
    for caso in ET.parse(ruta).getroot().iter("testcase"):
        prop = caso.find("properties/property[@name='etiquetas']")
        cp = next((t for t in (prop.get("value").split() if prop is not None else []) if t.startswith("CP-")), None)
        if not cp:
            continue
        omitido = caso.find("skipped")
        if caso.find("failure") is not None or caso.find("error") is not None:
            estado = "failed"
        elif omitido is not None:
            estado = "xfailed" if omitido.get("type") == "pytest.xfail" else "skipped"
        else:
            estado = "passed"
        res[cp].append(estado)
    return res


def resumir(estados, defectos):
    """Varias ejecuciones de un caso (ejemplos de un Scenario Outline) en un solo texto."""
    if not estados:
        return "sin ejecutar"
    for peor in ("failed", "flaky", "skipped", "xfailed"):
        if peor in estados:
            texto = peor
            break
    else:
        texto = "passed"
    if len(estados) > 1:
        texto += f" {estados.count(texto)}/{len(estados)}"
    if "xfailed" in estados and defectos:
        texto += " → " + ", ".join(defectos)
    return texto


def armar(casos, historias, api, web):
    """Filas de la matriz (una por HU y caso) y la cobertura por HU."""
    filas = []
    for cp, caso in sorted(casos.items(), key=lambda c: int(c[0][3:])):
        if caso["nivel"] == "api":
            resultado = resumir(api.get(cp, []), caso["defectos"]) if api is not None else "sin datos"
        else:
            partes = [f"{nav}: {resumir(res.get(cp, []), caso['defectos'])}" for nav, res in web.items()]
            resultado = " · ".join(partes) or "sin datos"
        for hu in caso["hu"] or ["—"]:
            filas.append({**caso, "hu": hu, "cp": cp, "resultado": resultado})
    filas.sort(key=lambda f: (f["hu"] == "—", orden_hu(f["hu"]), int(f["cp"][3:])))
    # solo los módulos que probamos: los prefijos (HU-N, HU-G5) que aparecen en algún caso
    modulos = {f["hu"].rsplit("-", 1)[0] for f in filas if f["hu"] != "—"}
    cobertura = {hu: sorted({f["cp"] for f in filas if f["hu"] == hu}, key=lambda c: int(c[3:]))
                 for hu in sorted(historias, key=orden_hu) if hu.rsplit("-", 1)[0] in modulos}
    return filas, cobertura


def orden_hu(hu):
    """HU-N-* primero, luego HU-G5-*, cada una por número."""
    modulo, _, n = hu.rpartition("-")
    return (modulo != "HU-N", modulo, int(n) if n.isdigit() else 0)


def contexto_run():
    run, sha = os.environ.get("GITHUB_RUN_NUMBER"), os.environ.get("GITHUB_SHA", "")[:7]
    url = (f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
           if run else None)
    return {"run": f"run #{run}" if run else "corrida local", "url": url, "sha": sha,
            "fecha": datetime.now(LIMA).strftime("%Y-%m-%d %H:%M")}


def a_markdown(filas, cobertura, historias, ctx):
    origen = f"[{ctx['run']}]({ctx['url']})" if ctx["url"] else ctx["run"]
    md = ["# Matriz de trazabilidad · G5 Límites y núcleo", "",
          f"Generada por `.github/scripts/trazabilidad.py` con los resultados de {origen}"
          f"{' · commit `' + ctx['sha'] + '`' if ctx['sha'] else ''} · {ctx['fecha']} (hora de Lima).", "",
          "Cada escenario lleva una etiqueta `@CP-NN` y las `@HU` que cubre. Un `xfailed` es un fallo esperado: "
          "el escenario describe el comportamiento correcto y falla por un defecto reportado en "
          "[`defectos.md`](defectos.md).", "",
          "## Cobertura por historia", "", "| HU | Historia | Casos |", "|---|---|---|"]
    for hu, cps in cobertura.items():
        md.append(f"| {hu} | {historias[hu]} | {', '.join(cps) if cps else '**sin casos**'} |")
    md += ["", "## Casos y resultados", "", f"| HU | Caso | Nivel | Resultado ({ctx['run']}) |", "|---|---|---|---|"]
    for f in filas:
        md.append(f"| {f['hu']} | {f['cp']} {f['nombre']} | {f['nivel']} | {f['resultado']} |")
    return "\n".join(md) + "\n"


def a_html(filas, cobertura, historias, ctx):
    e = html.escape
    origen = f'<a href="{e(ctx["url"])}">{e(ctx["run"])}</a>' if ctx["url"] else e(ctx["run"])
    def clase(r):
        return next((c for c in ("failed", "flaky", "skipped", "xfailed", "sin") if c in r), "passed")
    cob = "".join(f"<tr><td>{hu}</td><td>{e(historias[hu])}</td><td>{', '.join(cps) or '<b>sin casos</b>'}</td></tr>"
                  for hu, cps in cobertura.items())
    casos = "".join(f'<tr><td>{f["hu"]}</td><td><b>{f["cp"]}</b> {e(f["nombre"])}</td><td>{f["nivel"]}</td>'
                    f'<td class="{clase(f["resultado"])}">{e(f["resultado"])}</td></tr>' for f in filas)
    return f"""<h2 id="trazabilidad">Trazabilidad</h2>
<p>Resultados de {origen}{' · commit <code>' + ctx['sha'] + '</code>' if ctx['sha'] else ''} · {ctx['fecha']} (hora de Lima).
Un <span class="xfailed">xfailed</span> es un fallo esperado por un defecto reportado.</p>
<h3>Cobertura por historia</h3>
<table><tr><th>HU</th><th>Historia</th><th>Casos</th></tr>{cob}</table>
<h3>Casos y resultados</h3>
<table><tr><th>HU</th><th>Caso</th><th>Nivel</th><th>Resultado</th></tr>{casos}</table>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", help="JSON del reporter de Playwright")
    p.add_argument("--web", action="append", default=[], metavar="NAVEGADOR=JUNIT", help="JUnit XML de Selenium")
    p.add_argument("--md", help="dónde escribir la matriz en Markdown")
    p.add_argument("--html", help="dónde escribir la matriz como fragmento HTML (para la portada)")
    a = p.parse_args()

    api = resultados_api(a.api) if a.api and Path(a.api).exists() else None
    web = {}
    for par in a.web:
        nav, ruta = par.split("=", 1)
        if Path(ruta).exists():
            web[nav] = resultados_junit(ruta)
    historias = leer_historias()
    filas, cobertura = armar(leer_casos(), historias, api, web)
    ctx = contexto_run()
    if a.md:
        Path(a.md).write_text(a_markdown(filas, cobertura, historias, ctx), encoding="utf-8")
    if a.html:
        Path(a.html).parent.mkdir(parents=True, exist_ok=True)
        Path(a.html).write_text(a_html(filas, cobertura, historias, ctx), encoding="utf-8")
    if not (a.md or a.html):
        print(a_markdown(filas, cobertura, historias, ctx))


if __name__ == "__main__":
    main()
