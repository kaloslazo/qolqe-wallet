"""Matriz de trazabilidad HU -> caso -> resultado, a partir de los .feature y de los resultados de un run.

Uso:
  python .github/scripts/trazabilidad.py \
      --api reportes/resultados-api.json \
      --web chrome=reportes/selenium/junit.xml --web firefox=ruta/a/otro/junit.xml \
      --historial sitio/historial.json --md docs/trazabilidad.md --html sitio/trazabilidad.html

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
CA_TAG = re.compile(r"^CA-(N|G\d+)-(\d+)-(\d+)$")
CA_TEXTO = re.compile(r"^- \*\*CA(\d+)\.\*\* (.+)$")
LIMA = timezone(timedelta(hours=-5))
CORRIDAS = 30  # cuántas corridas guarda el historial


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
                        # @CA-N-07-3 -> "HU-N-07 CA3"
                        "criterios": [f"HU-{c.group(1)}-{c.group(2)} CA{c.group(3)}"
                                      for t in etiquetas if (c := CA_TAG.match(t))],
                        "tipo": "técnico" if "tecnico" in etiquetas else "funcional",
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


def leer_criterios():
    """{'HU-N-07 CA3': 'Si es exitosa: se debita mi saldo...'} de docs/requisitos.md."""
    criterios, hu = {}, None
    for linea in (RAIZ / "docs/requisitos.md").read_text(encoding="utf-8").splitlines():
        if m := HU_TITULO.match(linea):
            hu = m.group(1)
        elif hu and (m := CA_TEXTO.match(linea)):
            texto = re.sub(r"\*+", "", m.group(2))
            criterios[f"{hu} CA{m.group(1)}"] = texto if len(texto) <= 110 else texto[:107].rstrip() + "..."
    return criterios


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


PEOR = ("failed", "flaky", "skipped", "xfailed")


def peor(estados):
    return next((p for p in PEOR if p in estados), "passed") if estados else None


def resumir(estados, defectos):
    """Varias ejecuciones de un caso (ejemplos de un Scenario Outline) en un solo texto."""
    if not estados:
        return "sin ejecutar"
    texto = peor(estados)
    if len(estados) > 1:
        texto += f" {estados.count(texto)}/{len(estados)}"
    if "xfailed" in estados and defectos:
        texto += " → " + ", ".join(defectos)
    return texto


def estados_del_run(casos, api, web):
    """CP -> estado de esta corrida: el peor de sus ejemplos y navegadores."""
    res = {}
    for cp, caso in casos.items():
        if caso["nivel"] == "api":
            estados = api.get(cp, []) if api is not None else []
        else:
            estados = [e for r in web.values() for e in r.get(cp, [])]
        if estados:
            res[cp] = peor(estados)
    return res


def actualizar_historial(historial, estados, ctx):
    """Agrega esta corrida al historial (sin repetirla) y deja las últimas CORRIDAS."""
    if estados:
        historial = [h for h in historial if h.get("run") != ctx["run"]]
        historial.append({"run": ctx["run"], "url": ctx["url"], "sha": ctx["sha"], "fecha": ctx["fecha"],
                          "estados": estados})
    return historial[-CORRIDAS:]


def resumen_historial(historial, cp):
    """'passed 12' · 'xfailed 12' · 'passed 10 · failed 2 · último fallo run #45'."""
    vistos = [(h["run"], h["estados"][cp]) for h in historial if cp in h.get("estados", {})]
    if not vistos:
        return "—"
    cuenta = defaultdict(int)
    for _, estado in vistos:
        cuenta[estado] += 1
    texto = " · ".join(f"{e} {cuenta[e]}" for e in ("passed", "xfailed", "flaky", "failed", "skipped") if cuenta[e])
    fallos = [run for run, estado in vistos if estado in ("failed", "flaky")]
    return texto + (f" · último fallo {fallos[-1]}" if fallos else "")


def armar(casos, historias, api, web, historial=None):
    """Filas de la matriz (una por HU y caso), la cobertura por HU y la cobertura por criterio."""
    historial = historial or []
    filas = []
    for cp, caso in sorted(casos.items(), key=lambda c: int(c[0][3:])):
        if caso["nivel"] == "api":
            resultado = resumir(api.get(cp, []), caso["defectos"]) if api is not None else "sin datos"
        else:
            partes = [f"{nav}: {resumir(res.get(cp, []), caso['defectos'])}" for nav, res in web.items()]
            resultado = " · ".join(partes) or "sin datos"
        for hu in caso["hu"] or ["—"]:
            filas.append({**caso, "hu": hu, "cp": cp, "resultado": resultado,
                          "historial": resumen_historial(historial, cp)})
    filas.sort(key=lambda f: (f["hu"] == "—", orden_hu(f["hu"]), int(f["cp"][3:])))
    # solo los módulos que probamos: los prefijos (HU-N, HU-G5) que aparecen en algún caso
    modulos = {f["hu"].rsplit("-", 1)[0] for f in filas if f["hu"] != "—"}

    def por_numero(cps):
        return sorted(set(cps), key=lambda c: int(c[3:]))

    cobertura = {}
    for hu in sorted(historias, key=orden_hu):
        if hu.rsplit("-", 1)[0] not in modulos:
            continue
        de_hu = [f for f in filas if f["hu"] == hu]
        cobertura[hu] = {"funcional": por_numero(f["cp"] for f in de_hu if f["tipo"] == "funcional"),
                         "técnico": por_numero(f["cp"] for f in de_hu if f["tipo"] == "técnico")}
    criterios = defaultdict(list)
    for cp, caso in casos.items():
        for ca in caso["criterios"]:
            criterios[ca].append(cp)
    criterios = {ca: por_numero(cps) for ca, cps in criterios.items()}
    return filas, cobertura, criterios


def orden_hu(hu):
    """HU-N-* primero, luego HU-G5-*, cada una por número."""
    modulo, _, n = hu.rpartition("-")
    return (modulo != "HU-N", modulo, int(n) if n.isdigit() else 0)


def orden_ca(ca):
    hu, _, n = ca.partition(" CA")
    return (orden_hu(hu), int(n))


def contexto_run():
    run, sha = os.environ.get("GITHUB_RUN_NUMBER"), os.environ.get("GITHUB_SHA", "")[:7]
    url = (f"{os.environ['GITHUB_SERVER_URL']}/{os.environ['GITHUB_REPOSITORY']}/actions/runs/{os.environ['GITHUB_RUN_ID']}"
           if run else None)
    return {"run": f"run #{run}" if run else "corrida local", "url": url, "sha": sha,
            "fecha": datetime.now(LIMA).strftime("%Y-%m-%d %H:%M")}


def _criterios_de(hu, todos, cubiertos):
    propios = [ca for ca in todos if ca.startswith(hu + " ")]
    return f"{sum(1 for ca in propios if ca in cubiertos)}/{len(propios)}" if propios else "—"


def a_markdown(filas, cobertura, historias, ctx, criterios=None, textos=None, historial=None):
    criterios, textos, historial = criterios or {}, textos or {}, historial or []
    origen = f"[{ctx['run']}]({ctx['url']})" if ctx["url"] else ctx["run"]
    md = ["# Matriz de trazabilidad · G5 Límites y núcleo", "",
          f"Generada por `.github/scripts/trazabilidad.py` con los resultados de {origen}"
          f"{' · commit `' + ctx['sha'] + '`' if ctx['sha'] else ''} · {ctx['fecha']} (hora de Lima).", "",
          "Cada escenario lleva una etiqueta `@CP-NN`, las `@HU` que cubre y sus criterios (`@CA-N-07-3` = HU-N-07 CA3). "
          "Un `xfailed` es un fallo esperado: el escenario describe el comportamiento correcto y falla por un defecto "
          "reportado en [`defectos.md`](defectos.md).", ""]
    if historial:
        md += [f"El historial reúne las últimas {len(historial)} corridas de `main` "
               f"(desde {historial[0]['run']}, {historial[0]['fecha']}): un caso estable sale con un solo estado; "
               "uno inestable muestra cuántas veces falló y en qué corrida.", ""]
    md += ["## Cobertura por historia", "",
           "| HU | Historia | Funcionales | Técnicos | Criterios con caso |", "|---|---|---|---|---|"]
    textos_hu = [ca for ca in textos]
    for hu, cob in cobertura.items():
        md.append(f"| {hu} | {historias[hu]} | {', '.join(cob['funcional']) or '**sin casos**'} | "
                  f"{', '.join(cob['técnico']) or '—'} | {_criterios_de(hu, textos_hu, criterios)} |")
    if textos:
        md += ["", "## Cobertura por criterio", "", "| Criterio | Qué pide | Casos |", "|---|---|---|"]
        for ca in sorted((c for c in textos if c.rsplit(" ", 1)[0] in cobertura), key=orden_ca):
            md.append(f"| {ca} | {textos[ca]} | {', '.join(criterios.get(ca, [])) or '**sin casos**'} |")
    cabecera = f"| HU | Caso | Nivel | Tipo | Resultado ({ctx['run']}) |"
    md += ["", "## Casos y resultados", "",
           cabecera + (" Últimas corridas |" if historial else ""),
           "|---|---|---|---|---|" + ("---|" if historial else "")]
    for f in filas:
        md.append(f"| {f['hu']} | {f['cp']} {f['nombre']} | {f['nivel']} | {f['tipo']} | {f['resultado']} |"
                  + (f" {f['historial']} |" if historial else ""))
    return "\n".join(md) + "\n"


def a_html(filas, cobertura, historias, ctx, criterios=None, textos=None, historial=None):
    criterios, textos, historial = criterios or {}, textos or {}, historial or []
    e = html.escape
    origen = f'<a href="{e(ctx["url"])}">{e(ctx["run"])}</a>' if ctx["url"] else e(ctx["run"])

    def clase(r):
        return next((c for c in ("failed", "flaky", "skipped", "xfailed", "sin") if c in r), "passed")

    textos_hu = list(textos)
    cob = "".join(f"<tr><td>{hu}</td><td>{e(historias[hu])}</td><td>{', '.join(c['funcional']) or '<b>sin casos</b>'}</td>"
                  f"<td>{', '.join(c['técnico']) or '—'}</td><td>{_criterios_de(hu, textos_hu, criterios)}</td></tr>"
                  for hu, c in cobertura.items())
    por_ca = "".join(f"<tr><td>{ca}</td><td>{e(textos[ca])}</td><td>{', '.join(criterios.get(ca, [])) or '<b>sin casos</b>'}</td></tr>"
                     for ca in sorted((c for c in textos if c.rsplit(' ', 1)[0] in cobertura), key=orden_ca))
    con_hist = bool(historial)
    casos = "".join(f'<tr><td>{f["hu"]}</td><td><b>{f["cp"]}</b> {e(f["nombre"])}</td><td>{f["nivel"]}</td>'
                    f'<td>{f["tipo"]}</td><td class="{clase(f["resultado"])}">{e(f["resultado"])}</td>'
                    + (f'<td class="{clase(f["historial"])}">{e(f["historial"])}</td>' if con_hist else "")
                    + "</tr>" for f in filas)
    hist = (f"<p>Historial: últimas {len(historial)} corridas de <code>main</code>, desde {e(historial[0]['run'])} "
            f"({e(historial[0]['fecha'])}).</p>" if con_hist else "")
    return f"""<h2 id="trazabilidad">Trazabilidad</h2>
<p>Resultados de {origen}{' · commit <code>' + ctx['sha'] + '</code>' if ctx['sha'] else ''} · {ctx['fecha']} (hora de Lima).
Un <span class="xfailed">xfailed</span> es un fallo esperado por un defecto reportado.</p>
{hist}
<h3>Cobertura por historia</h3>
<table><tr><th>HU</th><th>Historia</th><th>Funcionales</th><th>Técnicos</th><th>Criterios con caso</th></tr>{cob}</table>
<h3>Cobertura por criterio</h3>
<table><tr><th>Criterio</th><th>Qué pide</th><th>Casos</th></tr>{por_ca}</table>
<h3>Casos y resultados</h3>
<table><tr><th>HU</th><th>Caso</th><th>Nivel</th><th>Tipo</th><th>Resultado</th>{'<th>Últimas corridas</th>' if con_hist else ''}</tr>{casos}</table>
"""


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--api", help="JSON del reporter de Playwright")
    p.add_argument("--web", action="append", default=[], metavar="NAVEGADOR=JUNIT", help="JUnit XML de Selenium")
    p.add_argument("--historial", help="JSON con las corridas anteriores; se le agrega esta corrida")
    p.add_argument("--md", help="dónde escribir la matriz en Markdown")
    p.add_argument("--html", help="dónde escribir la matriz como fragmento HTML (para la portada)")
    a = p.parse_args()

    api = resultados_api(a.api) if a.api and Path(a.api).exists() else None
    web = {}
    for par in a.web:
        nav, ruta = par.split("=", 1)
        if Path(ruta).exists():
            web[nav] = resultados_junit(ruta)
    casos, historias, textos, ctx = leer_casos(), leer_historias(), leer_criterios(), contexto_run()
    historial = []
    if a.historial:
        ruta = Path(a.historial)
        previo = json.loads(ruta.read_text(encoding="utf-8")) if ruta.exists() else []
        historial = actualizar_historial(previo, estados_del_run(casos, api, web), ctx)
        ruta.write_text(json.dumps(historial, ensure_ascii=False), encoding="utf-8")
    filas, cobertura, criterios = armar(casos, historias, api, web, historial)
    md = a_markdown(filas, cobertura, historias, ctx, criterios, textos, historial)
    if a.md:
        Path(a.md).write_text(md, encoding="utf-8")
    if a.html:
        Path(a.html).parent.mkdir(parents=True, exist_ok=True)
        Path(a.html).write_text(a_html(filas, cobertura, historias, ctx, criterios, textos, historial), encoding="utf-8")
    if not (a.md or a.html):
        print(md)


if __name__ == "__main__":
    main()
