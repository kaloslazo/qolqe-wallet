#!/usr/bin/env python3
"""Tablero de calidad con antes y después.

Junta en una sola página lo que las demás herramientas del repo ya producen: el mapeado (historia → escenario →
criterio), el testing (resultados de la API, la web y el rendimiento), los defectos y lo que aportó la IA. Compara dos
instantáneas del proyecto: «antes» (por ejemplo, la entrega anterior) y «después» (el estado actual).

Dos pasos:

  1. Instantánea de un árbol del repositorio (el actual, o una entrega anterior sacada con `git archive`):
       python .github/scripts/tablero.py instantanea --repo . --nombre "Final" --salida calidad/despues.json \
           [--api-json reportes/resultados-api.json] [--web-junit reportes/selenium/junit.xml]

  2. Tablero comparando dos instantáneas:
       python .github/scripts/tablero.py tablero --antes calidad/antes.json --despues calidad/despues.json \
           --salida reportes/tablero/tablero.html [--enlace "Diagnóstico=../diagnostico/diagnostico.html"]

Todo sale de archivos del repo: no inventa números. Lo que no se pudo medir (por ejemplo los resultados de la web en
un árbol donde no se corrió) aparece como «—», no como cero.
"""
import argparse
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ESCENARIO = re.compile(r"^\s*(Scenario Outline|Scenario|Esquema del escenario|Escenario):\s*(.+)$")
FEATURE = re.compile(r"^\s*(Feature|Característica):")
EJEMPLOS = re.compile(r"^\s*(Examples|Scenarios|Ejemplos):")
CA_TAG = re.compile(r"^CA-(N|G\d+)-(\d+)-(\d+)$")
MODULOS = ("HU-N", "HU-G5")
LIMA = timezone(timedelta(hours=-5))
e = html.escape


# ------------------------------------------------------------------ instantánea
def leer_escenarios(repo):
    lista = []
    for archivo in sorted((repo / "features").rglob("*.feature")):
        nivel = "web" if "ui" in archivo.relative_to(repo / "features").parts[:-1] else "api"
        de_feature, pendientes, actual = [], [], None
        for linea in archivo.read_text(encoding="utf-8").splitlines():
            texto = linea.strip()
            if texto.startswith("@"):
                pendientes += [t[1:] for t in texto.split() if t.startswith("@")]
            elif FEATURE.match(linea):
                de_feature, pendientes = pendientes, []
            elif m := ESCENARIO.match(linea):
                actual = {"nivel": nivel, "nombre": m.group(2).strip(), "etiquetas": de_feature + pendientes}
                lista.append(actual)
                pendientes = []
            elif EJEMPLOS.match(linea):
                if actual:
                    actual["etiquetas"] = actual["etiquetas"] + pendientes
                pendientes = []
            elif texto and not texto.startswith("#"):
                pendientes = []
    return lista


def leer_requisitos(repo):
    """{'HU-N-07': {'titulo': ..., 'criterios': [1, 2, 3]}} en el orden del documento."""
    historias, hu = {}, None
    for linea in (repo / "docs/requisitos.md").read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^### (HU-[A-Z0-9]+-\d+) · ([^·]+)", linea):
            hu = m.group(1)
            historias[hu] = {"titulo": m.group(2).strip(), "criterios": []}
        elif hu and (m := re.match(r"^- \*\*CA(\d+)\.\*\*", linea)):
            historias[hu]["criterios"].append(int(m.group(1)))
    return historias


def leer_defectos(repo):
    ruta = repo / "docs/defectos.md"
    if not ruta.exists():
        return {}
    defectos, actual = {}, None
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if m := re.match(r"^## (DEF-\d+): (.+)$", linea):
            actual = defectos[m.group(1)] = {"titulo": m.group(2).strip(), "severidad": "—"}
        elif actual and (m := re.match(r"^\| Severidad \| (.+?) \|", linea)):
            actual["severidad"] = m.group(1).strip()
    return defectos


def contar_playwright(ruta):
    """Cuenta las pruebas del JSON de Playwright: pasan (con y sin fallo esperado), fallan, flaky, omitidas."""
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    c = {"total": 0, "pasan": 0, "esperados": 0, "fallan": 0, "flaky": 0, "omitidas": 0, "segundos": round(datos.get("stats", {}).get("duration", 0) / 1000)}

    def recorrer(suite):
        for spec in suite.get("specs", []):
            for test in spec["tests"]:
                c["total"] += 1
                esperado_falla = any(a["type"] == "fail" for a in test["annotations"])
                if test["status"] == "expected":
                    c["esperados" if esperado_falla else "pasan"] += 1
                elif test["status"] == "unexpected":
                    c["fallan"] += 1
                elif test["status"] == "flaky":
                    c["flaky"] += 1
                else:
                    c["omitidas"] += 1
        for hija in suite.get("suites", []):
            recorrer(hija)

    for suite in datos["suites"]:
        recorrer(suite)
    return c


def contar_junit(ruta):
    import xml.etree.ElementTree as ET
    c = {"total": 0, "pasan": 0, "esperados": 0, "fallan": 0, "flaky": 0, "omitidas": 0}
    for caso in ET.parse(ruta).getroot().iter("testcase"):
        c["total"] += 1
        omitido = caso.find("skipped")
        if caso.find("failure") is not None or caso.find("error") is not None:
            c["fallan"] += 1
        elif omitido is not None and omitido.get("type") == "pytest.xfail":
            c["esperados"] += 1
        elif omitido is not None:
            c["omitidas"] += 1
        else:
            c["pasan"] += 1
    return c


def recolectar_web(repo):
    """Pruebas que Selenium + pytest-bdd recolecta, sin abrir un navegador. None si no se puede."""
    py = repo / ".venv/bin/python"
    if not py.exists() or not (repo / "tests/e2e").exists():
        return None
    try:
        r = subprocess.run([str(py), "-m", "pytest", "tests/e2e", "--collect-only", "-q", "-p", "no:cacheprovider"],
                           cwd=repo, capture_output=True, text=True, timeout=120)
    except (OSError, subprocess.TimeoutExpired):
        return None
    m = re.search(r"(\d+) tests? collected", r.stdout) or re.search(r"^(\d+) tests? ", r.stdout, re.M)
    return int(m.group(1)) if m else None


def leer_rendimiento(repo):
    filas = []
    base = repo / "tests/performance/resultados"
    for prueba in ("humo", "carga", "pico", "estres", "resistencia", "concurrencia"):
        ruta = base / prueba / "resumen_k6.json"
        if not ruta.exists():
            continue
        m = json.loads(ruta.read_text(encoding="utf-8")).get("metrics", {})
        p95 = lambda k: (m.get(k) or {}).get("p(95)")
        fallas = (m.get("http_req_failed") or {}).get("value")
        filas.append({"prueba": prueba, "consultas": p95("http_req_duration{tipo:consulta}"),
                      "dinero": p95("http_req_duration{tipo:dinero}"), "fallas": fallas,
                      "peticiones": (m.get("http_reqs") or {}).get("count")})
    return filas


def instantanea(repo, nombre, api_json, web_junit):
    repo = Path(repo).resolve()
    escenarios = leer_escenarios(repo)
    historias = leer_requisitos(repo)
    cubiertos, por_hu = set(), {hu: {"api": 0, "web": 0} for hu in historias}
    for esc in escenarios:
        et = esc["etiquetas"]
        for hu in (t for t in et if t.startswith("HU-")):
            if hu in por_hu:
                por_hu[hu][esc["nivel"]] += 1
        if esc["nivel"] == "api":
            for t in et:
                if m := CA_TAG.match(t):
                    cubiertos.add(f"HU-{m.group(1)}-{m.group(2)} CA{m.group(3)}")
    historias_salida = {}
    for hu, h in historias.items():
        mod = hu.rsplit("-", 1)[0]
        historias_salida[hu] = {
            "titulo": h["titulo"], "modulo": mod, "criterios": len(h["criterios"]),
            "cubiertos": sum(1 for n in h["criterios"] if f"{hu} CA{n}" in cubiertos),
            "api": por_hu[hu]["api"], "web": por_hu[hu]["web"]}
    de_modulo = [h for hu, h in historias_salida.items() if h["modulo"] in MODULOS]
    ia = repo / "propuestas/ia"
    skills = repo / ".claude/skills"
    web_res = contar_junit(web_junit) if web_junit and Path(web_junit).exists() else None
    return {
        "nombre": nombre,
        "fecha": datetime.now(LIMA).strftime("%Y-%m-%d %H:%M"),
        "escenarios": {"total": len(escenarios), "api": sum(1 for x in escenarios if x["nivel"] == "api"),
                       "web": sum(1 for x in escenarios if x["nivel"] == "web"),
                       "con_defecto": sum(1 for x in escenarios if "fail" in x["etiquetas"] or "defecto" in x["etiquetas"])},
        "criterios": {"total": sum(h["criterios"] for h in de_modulo), "cubiertos": sum(h["cubiertos"] for h in de_modulo)},
        "historias": historias_salida,
        "defectos": leer_defectos(repo),
        "api": contar_playwright(api_json) if api_json and Path(api_json).exists() else None,
        "web": web_res,
        "web_recolectadas": recolectar_web(repo),
        "rendimiento": leer_rendimiento(repo),
        "ia": {"propuestas": len(list(ia.glob("*.md"))) if ia.exists() else 0,
               "skills": sorted(p.name for p in skills.iterdir() if p.is_dir()) if skills.exists() else []},
    }


# ------------------------------------------------------------------ tablero
def num(v, sufijo=""):
    return "—" if v is None else f"{v}{sufijo}"


def delta(a, d, menos_es_mejor=False):
    if a is None or d is None or a == d:
        return '<span class="igual">sin cambio</span>' if a == d and a is not None else ""
    dif = d - a
    bueno = dif < 0 if menos_es_mejor else dif > 0
    return f'<span class="{"mejor" if bueno else "peor"}">{"+" if dif > 0 else ""}{dif:g}</span>'


def tarjeta(titulo, a, d, ayuda, menos_es_mejor=False, fmt=None):
    f = fmt or num
    return (f'<div class="kpi"><div class="kpi-t">{e(titulo)}</div>'
            f'<div class="kpi-v"><span class="antes">{f(a)}</span><span class="flecha">→</span><b>{f(d)}</b> {delta(a, d, menos_es_mejor)}</div>'
            f'<div class="kpi-a">{e(ayuda)}</div></div>')


def barra(parte, total):
    pct = 0 if not total else round(100 * parte / total)
    return f'<span class="barra"><i style="width:{pct}%"></i></span>'


def get(d, *ruta):
    for k in ruta:
        if d is None:
            return None
        d = d.get(k) if isinstance(d, dict) else None
    return d


def tablero(antes, despues, enlaces):
    ya, yd = antes["api"], despues["api"]
    kpis = [
        tarjeta("Escenarios Gherkin", antes["escenarios"]["total"], despues["escenarios"]["total"],
                f"{despues['escenarios']['api']} de API y {despues['escenarios']['web']} de web"),
        tarjeta("Criterios con escenario de API", antes["criterios"]["cubiertos"], despues["criterios"]["cubiertos"],
                f"de {despues['criterios']['total']} del núcleo y del módulo G5"),
        tarjeta("Pruebas de API ejecutadas", get(ya, "total"), get(yd, "total"), "cada ejemplo de un esquema cuenta como una prueba"),
        tarjeta("Pruebas de API que fallan sin esperarlo", get(ya, "fallan"), get(yd, "fallan"), "debe ser 0", menos_es_mejor=True),
        tarjeta("Pruebas web", antes["web_recolectadas"] if antes["web_recolectadas"] is not None else get(antes, "web", "total"),
                despues["web_recolectadas"] if despues["web_recolectadas"] is not None else get(despues, "web", "total"),
                "las que pytest-bdd recolecta (cada navegador las repite)"),
        tarjeta("Defectos documentados", len(antes["defectos"]), len(despues["defectos"]), "cada uno con su escenario"),
        tarjeta("Propuestas de la IA revisadas", get(antes, "ia", "propuestas"), get(despues, "ia", "propuestas"), "en propuestas/ia/, aceptadas por una persona"),
    ]

    # mapeado por historia
    filas = []
    for hu, h in despues["historias"].items():
        if h["modulo"] not in MODULOS:
            continue
        a = antes["historias"].get(hu, {"api": 0, "web": 0, "cubiertos": 0, "criterios": h["criterios"]})
        mejora = (h["cubiertos"], h["api"], h["web"]) != (a["cubiertos"], a["api"], a["web"])
        filas.append(
            f'<tr class="{"cambio" if mejora else ""}"><td><b>{e(hu)}</b></td><td>{e(h["titulo"])}</td>'
            f'<td>{a["api"]} → <b>{h["api"]}</b></td><td>{a["web"]} → <b>{h["web"]}</b></td>'
            f'<td>{a["cubiertos"]} → <b>{h["cubiertos"]}</b> de {h["criterios"]} {barra(h["cubiertos"], h["criterios"])}</td></tr>')
    mapeado = ('<table><thead><tr><th>Historia</th><th>Qué es</th><th>Escenarios de API</th><th>Escenarios web</th>'
               '<th>Criterios con escenario</th></tr></thead><tbody>' + "".join(filas) + "</tbody></table>")

    # testing
    def fila_res(nombre, a, d):
        if not a and not d:
            return ""
        g = lambda x, k: None if not x else x[k]
        celdas = "".join(f"<td>{num(g(a, k))} → <b>{num(g(d, k))}</b></td>" for k in ("total", "pasan", "esperados", "fallan", "flaky"))
        return f"<tr><td><b>{nombre}</b></td>{celdas}</tr>"
    testing = ('<table><thead><tr><th>Suite</th><th>Pruebas</th><th>Pasan</th><th>Fallo esperado (defecto)</th><th>Fallan</th><th>Flaky</th></tr></thead><tbody>'
               + fila_res("API · Playwright", ya, yd) + fila_res("Web · Selenium (una corrida)", antes["web"], despues["web"]) + "</tbody></table>")
    nota_web = ""
    if despues["web"] is None:
        nota_web = '<p class="nota">La fila de la web aparece cuando se pasa <code>--web-junit</code> con el JUnit de una corrida real de Selenium; sin él no se inventa.</p>'

    # rendimiento
    ra = {f["prueba"]: f for f in antes["rendimiento"]}
    rf = []
    for f in despues["rendimiento"]:
        x = ra.get(f["prueba"])
        mismo = x == f
        rf.append(f'<tr><td><b>{f["prueba"]}</b></td><td>{num(None if f["consultas"] is None else round(f["consultas"]), " ms")}</td>'
                  f'<td>{num(None if f["dinero"] is None else round(f["dinero"]), " ms")}</td>'
                  f'<td>{num(None if f["fallas"] is None else f"{f["fallas"] * 100:.1f} %")}</td><td>{num(f["peticiones"])}</td>'
                  f'<td>{"sin cambio" if mismo else "distinto del anterior"}</td></tr>')
    rendimiento = ('<table><thead><tr><th>Prueba</th><th>p95 consultas<br><small>umbral 800 ms</small></th><th>p95 dinero<br><small>umbral 1500 ms</small></th>'
                   '<th>Fallas<br><small>umbral 1 %</small></th><th>Peticiones</th><th>Contra el antes</th></tr></thead><tbody>'
                   + "".join(rf) + "</tbody></table>") if rf else ""

    # defectos
    df = []
    for k, d in despues["defectos"].items():
        nuevo = k not in antes["defectos"]
        df.append(f'<tr class="{"cambio" if nuevo else ""}"><td><b>{k}</b></td><td>{e(d["titulo"])}</td><td>{e(d["severidad"])}</td>'
                  f'<td>{"nuevo" if nuevo else "ya reportado"}</td></tr>')
    defectos = ('<table><thead><tr><th>Defecto</th><th>Qué pasa</th><th>Severidad</th><th>Contra el antes</th></tr></thead><tbody>'
                + "".join(df) + "</tbody></table>")

    # qué cambió
    nuevos_def = [k for k in despues["defectos"] if k not in antes["defectos"]]
    cambios = [
        f'{despues["escenarios"]["total"] - antes["escenarios"]["total"]:+d} escenarios Gherkin '
        f'({despues["escenarios"]["web"] - antes["escenarios"]["web"]:+d} de web)',
        f'criterios con escenario de API: {antes["criterios"]["cubiertos"]} → {despues["criterios"]["cubiertos"]} de {despues["criterios"]["total"]}',
    ]
    if ya and yd:
        cambios.append(f'pruebas de API: {ya["total"]} → {yd["total"]}; fallan sin esperarlo: {ya["fallan"]} → {yd["fallan"]}')
    if nuevos_def:
        cambios.append("defectos nuevos: " + ", ".join(nuevos_def))
    ia_nueva = [s for s in despues["ia"]["skills"] if s not in antes["ia"]["skills"]]
    if ia_nueva:
        cambios.append("skills de IA nuevas: " + ", ".join(ia_nueva))
    links = "".join(f'<li><a href="{e(u)}">{e(t)}</a></li>' for t, u in enlaces)

    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Tablero de calidad · Qolqe G5</title>
<style>
:root{{--t:#1c1917;--m:#78716c;--l:#e7e5e4;--f:#fafaf9;--ok:#15803d;--mal:#b91c1c;--az:#1d4ed8}}
*{{box-sizing:border-box}}body{{font:15px/1.5 system-ui,-apple-system,sans-serif;color:var(--t);background:#fff;margin:0}}
main{{max-width:1120px;margin:0 auto;padding:32px 20px 60px}}h1{{font-size:30px;margin:0 0 4px}}h2{{font-size:20px;margin:36px 0 6px}}
.sub{{color:var(--m);margin:0 0 22px}}.sub b{{color:var(--t)}}
.kpis{{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}}
.kpi{{border:1px solid var(--l);border-radius:12px;padding:14px 16px;background:var(--f)}}
.kpi-t{{font-size:13px;color:var(--m)}}.kpi-v{{font-size:26px;margin:4px 0 2px;display:flex;align-items:baseline;gap:8px;flex-wrap:wrap}}
.kpi-v b{{font-weight:700}}.antes{{color:var(--m)}}.flecha{{color:var(--m);font-size:18px}}.kpi-a{{font-size:12px;color:var(--m)}}
.mejor{{color:var(--ok);font-size:14px;font-weight:600}}.peor{{color:var(--mal);font-size:14px;font-weight:600}}.igual{{color:var(--m);font-size:13px}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:10px 0}}th,td{{text-align:left;padding:7px 10px;border-bottom:1px solid var(--l);vertical-align:top}}
th{{background:var(--f);font-weight:600}}th small{{font-weight:400;color:var(--m)}}tr.cambio td{{background:#f0fdf4}}
.barra{{display:inline-block;width:70px;height:7px;background:var(--l);border-radius:4px;margin-left:6px;vertical-align:middle}}
.barra i{{display:block;height:100%;background:var(--ok);border-radius:4px}}.nota{{font-size:13px;color:var(--m)}}
ul.cambios li{{margin:3px 0}}code{{background:var(--f);padding:1px 5px;border-radius:4px;font-size:13px}}a{{color:var(--az)}}
.leyenda{{font-size:13px;color:var(--m)}}.leyenda i{{display:inline-block;width:12px;height:12px;background:#f0fdf4;border:1px solid #bbf7d0;vertical-align:middle}}
</style></head><body><main>
<h1>Tablero de calidad · Qolqe Wallet</h1>
<p class="sub"><span class="antes">Antes:</span> <b>{e(antes["nombre"])}</b> &nbsp;→&nbsp; <span>Después:</span> <b>{e(despues["nombre"])}</b> (generado {despues["fecha"]})</p>
<h2>Qué cambió</h2><ul class="cambios">{"".join(f"<li>{c}</li>" for c in cambios)}</ul>
<div class="kpis" style="margin-top:14px">{"".join(kpis)}</div>
<h2>Mapeado: de la historia al escenario y al criterio</h2>
<p class="nota">Cada historia con los escenarios que la prueban y los criterios de aceptación con al menos un escenario de API. <span class="leyenda"><i></i> fila que cambió</span></p>
{mapeado}
<h2>Testing: qué se ejecutó y cómo salió</h2>{testing}{nota_web}
{"<h2>Rendimiento (k6)</h2>" + rendimiento if rendimiento else ""}
<h2>Defectos</h2>{defectos}
{"<h2>Reportes de esta corrida</h2><ul>" + links + "</ul>" if links else ""}
<p class="nota">Generado por <code>.github/scripts/tablero.py</code> a partir de los .feature, docs/requisitos.md, docs/defectos.md y los resultados de las suites. Cada número se puede volver a calcular.</p>
</main></body></html>"""


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("instantanea")
    i.add_argument("--repo", default=".")
    i.add_argument("--nombre", required=True)
    i.add_argument("--salida", required=True)
    i.add_argument("--api-json")
    i.add_argument("--web-junit")
    t = sub.add_parser("tablero")
    t.add_argument("--antes", required=True)
    t.add_argument("--despues", required=True)
    t.add_argument("--salida", required=True)
    t.add_argument("--enlace", action="append", default=[], help='"Texto=ruta"')
    a = ap.parse_args()
    if a.cmd == "instantanea":
        datos = instantanea(a.repo, a.nombre, a.api_json, a.web_junit)
        Path(a.salida).parent.mkdir(parents=True, exist_ok=True)
        Path(a.salida).write_text(json.dumps(datos, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"instantánea «{a.nombre}»: {datos['escenarios']['total']} escenarios, "
              f"{datos['criterios']['cubiertos']}/{datos['criterios']['total']} criterios, {len(datos['defectos'])} defectos → {a.salida}")
    else:
        antes = json.loads(Path(a.antes).read_text(encoding="utf-8"))
        despues = json.loads(Path(a.despues).read_text(encoding="utf-8"))
        enlaces = [tuple(x.split("=", 1)) for x in a.enlace if "=" in x]
        salida = Path(a.salida)
        salida.parent.mkdir(parents=True, exist_ok=True)
        salida.write_text(tablero(antes, despues, enlaces), encoding="utf-8")
        print(f"tablero en {salida}")


if __name__ == "__main__":
    sys.exit(main())
