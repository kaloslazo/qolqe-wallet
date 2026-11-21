"""Diagnóstico de una corrida: del job en rojo (o del defecto conocido) al request del servidor que lo explica.

Los reportes por defecto dicen qué prueba falló. Este script agrega lo que falta para encontrar por qué: cruza el
resultado de cada prueba con el log de la app (uvicorn), que guarda cada request con su código HTTP y las trazas de
Python de los errores internos.

Uso:
  python .github/scripts/diagnostico.py --playwright reportes/resultados-api.json --log-api reportes/log-api.txt \
      --salida reportes/diagnostico

Escribe SALIDA/diagnostico.md y SALIDA/diagnostico.html.

Cómo se une una prueba con su tramo del log (API). Cada escenario empieza con el paso «los datos de prueba están
restaurados», que llama a POST /api/pruebas/reiniciar, y Playwright corre en serie (workers: 1). El log de la app se
parte en un tramo por cada reinicio, y el tramo N es el intento N en orden de hora de inicio (el JSON lista por archivo,
no por ejecución; los reintentos cuentan como intento).
La unión solo se acepta si la cantidad de tramos es igual a la de intentos; si no, se dice y no se adivina.
Este diagnóstico es solo de la API. La web no se cruza con el log de la app: sus escenarios pueden abrir dos navegadores
y esa unión no se validó; para la web el camino es el reporte BDD (paso, captura, consola del navegador).
"""
import argparse
import html
import json
import re
from collections import Counter
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")
ACCESO = re.compile(r'"(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD) (\S+) HTTP/[\d.]+" (\d{3})')
REINICIO = ("POST", "/api/pruebas/reiniciar")
RUIDO = re.compile(r"^/api/(pruebas|salud)")  # rutas de soporte: no son del producto
INICIO = re.compile(r"^(INFO|WARNING):\s+(Started|Waiting|Application|Uvicorn|Shutting|Finished|Will watch)")
MAX_TRAMO = 14  # requests que se muestran por prueba
e = html.escape


# ---------------------------------------------------------------- log de la app
def tramos_del_log(ruta):
    """Parte el log en un tramo por cada reinicio de datos. Cada tramo: requests (método, ruta, código) y trazas."""
    tramos, actual = [], None
    for linea in Path(ruta).read_text(encoding="utf-8", errors="replace").splitlines():
        linea = ANSI.sub("", linea)
        m = ACCESO.search(linea)
        if m:
            metodo, ruta_, codigo = m.group(1), m.group(2).split("?")[0], int(m.group(3))
            if (metodo, ruta_) == REINICIO:
                actual = {"requests": [], "trazas": []}
                tramos.append(actual)
            elif actual is not None and not (ruta_ == "/api/salud"):
                actual["requests"].append((metodo, ruta_, codigo))
        elif actual is not None and linea.strip() and not INICIO.match(linea):
            actual["trazas"].append(linea.rstrip())
    return tramos


def codigos(tramos):
    c = Counter()
    for t in tramos:
        for _, ruta_, codigo in t["requests"]:
            if not RUIDO.match(ruta_):
                c[f"{codigo // 100}xx"] += 1
    return c


# ---------------------------------------------------------------- resultados de Playwright
def intentos_playwright(ruta):
    """Una entrada por intento, en el orden en que corrieron."""
    salida = []

    def recorrer(suite, titulos):
        for spec in suite.get("specs", []):
            etiquetas = [t.lstrip("@") for t in spec.get("tags", [])]
            for test in spec["tests"]:
                esperado = any(a["type"] == "fail" for a in test.get("annotations", []))
                for r in test["results"]:
                    error = ANSI.sub("", (r.get("error") or {}).get("message", "")).strip()
                    salida.append({
                        "titulo": " › ".join(titulos + [spec["title"]]), "etiquetas": etiquetas,
                        "estado_test": test["status"], "espera_fallar": esperado, "intento": r["retry"],
                        "estado": r["status"], "error": error, "duracion": r.get("duration", 0),
                        "inicio": r.get("startTime", "")})
        for hija in suite.get("suites", []):
            recorrer(hija, titulos + ([hija["title"]] if hija.get("title") else []))

    for suite in json.loads(Path(ruta).read_text(encoding="utf-8")).get("suites", []):
        recorrer(suite, [])
    # el JSON lista por archivo y por escenario; el log, en el orden en que corrieron: se ordena por la hora de inicio
    return sorted(salida, key=lambda x: x["inicio"])


def etiqueta(item, prefijo):
    return next((t for t in item["etiquetas"] if t.startswith(prefijo)), "")


def veredicto(item):
    if item["estado"] == "skipped":
        return "skipped"
    if item["estado_test"] == "flaky" or item["intento"] > 0:
        return "flaky" if item["estado"] == "passed" else "failed"
    if item["estado_test"] == "expected":
        return "xfailed" if item["espera_fallar"] else "passed"
    return "failed"


def recorte(texto, n=3):
    lineas = [ln for ln in (texto or "").splitlines() if ln.strip()]
    return "\n".join(lineas[:n])


def formato_requests(requests):
    util = [r for r in requests if not RUIDO.match(r[1])]
    filas = [f"{m} {r} → {c}" + ("  ⚠ error del servidor" if c >= 500 else "") for m, r, c in util[:MAX_TRAMO]]
    if len(util) > MAX_TRAMO:
        filas.append(f"… y {len(util) - MAX_TRAMO} más")
    return filas or ["(sin requests al producto)"]


def diagnosticar_api(json_ruta, log_ruta):
    intentos, tramos = intentos_playwright(json_ruta), tramos_del_log(log_ruta)
    alineado = len(intentos) == len(tramos)
    casos = []
    for i, it in enumerate(intentos):
        v = veredicto(it)
        if v == "passed":
            continue
        tramo = tramos[i] if alineado else None
        casos.append({"cp": etiqueta(it, "CP-"), "hu": ", ".join(t for t in it["etiquetas"] if t.startswith("HU-")),
                      "def": etiqueta(it, "DEF-"), "titulo": it["titulo"], "veredicto": v, "error": it["error"],
                      "requests": formato_requests(tramo["requests"]) if tramo else [],
                      "trazas": tramo["trazas"][-8:] if tramo else [], "intento": it["intento"]})
    errores_5xx = []
    if alineado:
        for it, tr in zip(intentos, tramos):
            for m, r, c in tr["requests"]:
                if c >= 500 and not RUIDO.match(r):
                    errores_5xx.append({"cp": etiqueta(it, "CP-"), "def": etiqueta(it, "DEF-"), "request": f"{m} {r} → {c}",
                                        "traza": next((ln for ln in reversed(tr["trazas"]) if re.match(r"^\w+(\.\w+)*(Error|Exception)", ln)), "")})
    return {"intentos": len(intentos), "tramos": len(tramos), "alineado": alineado, "casos": casos,
            "codigos": codigos(tramos), "errores_5xx": errores_5xx}


# ---------------------------------------------------------------- salida
ETIQUETA_ESTADO = {"failed": "❌ falló", "xfailed": "🟡 fallo esperado (defecto)", "flaky": "⚠️ flaky", "skipped": "⏭️ omitido"}


def a_markdown(api):
    md = ["# Diagnóstico de la corrida", "",
          "Cruce de cada prueba que no pasó limpia con el log de la app: qué requests hizo y qué respondió el servidor.", ""]
    if api:
        c = api["codigos"]
        md += ["## API · Playwright", "",
               f"- Intentos de prueba: **{api['intentos']}** · tramos del log de la app: **{api['tramos']}** · "
               + ("unión prueba ↔ log: **sí**" if api["alineado"] else "unión prueba ↔ log: **no** (la cantidad no coincide; no se adivina)"),
               f"- Requests al producto por código: " + (", ".join(f"{k}: {v}" for k, v in sorted(c.items())) or "—"), ""]
        if api["errores_5xx"]:
            md += ["### Errores del servidor (5xx)", "", "| Caso | Defecto | Request | Excepción en el log |", "|---|---|---|---|"]
            md += [f"| {x['cp']} | {x['def'] or '—'} | `{x['request']}` | `{x['traza'] or '—'}` |" for x in api["errores_5xx"]]
            md += [""]
        else:
            md += ["No hubo errores 5xx del servidor durante la corrida.", ""]
        md += ["### Pruebas que no pasaron limpias", ""]
        if not api["casos"]:
            md += ["Ninguna: todas pasaron sin defectos esperados ni reintentos.", ""]
        for x in api["casos"]:
            md += [f"#### {x['cp'] or '—'} · {x['hu']} · {x['def'] or 'sin defecto'} · {ETIQUETA_ESTADO[x['veredicto']]}", "",
                   f"_{x['titulo']}_", ""]
            if x["error"]:
                md += ["Lo que dijo la prueba:", "", "```", recorte(x["error"]), "```", ""]
            if x["requests"]:
                md += ["Lo que hizo contra la app:", "", "```", *x["requests"], "```", ""]
            if x["trazas"]:
                md += ["Traza del servidor:", "", "```", *x["trazas"], "```", ""]
    return "\n".join(md) + "\n"


def a_html(md):
    """Markdown mínimo (títulos, listas, tablas, bloques de código) a HTML autocontenido."""
    cuerpo, en_codigo, en_tabla, en_lista = [], False, False, False

    def cerrar():
        nonlocal en_tabla, en_lista
        if en_tabla:
            cuerpo.append("</tbody></table>"); en_tabla = False
        if en_lista:
            cuerpo.append("</ul>"); en_lista = False

    def inline(t):
        t = e(t)
        t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
        t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
        return re.sub(r"(?<![\w])_(.+?)_(?![\w])", r"<i>\1</i>", t)

    cabecera = False
    for linea in md.splitlines():
        if linea.startswith("```"):
            cerrar()
            cuerpo.append("</pre>" if en_codigo else "<pre>")
            en_codigo = not en_codigo
        elif en_codigo:
            cuerpo.append(e(linea))
        elif linea.startswith("|"):
            celdas = [c.strip() for c in linea.strip("|").split("|")]
            if set("".join(celdas)) <= set("-: "):
                continue
            if not en_tabla:
                cuerpo.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in celdas) + "</tr></thead><tbody>")
                en_tabla = True
            else:
                cuerpo.append("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in celdas) + "</tr>")
        else:
            cerrar()
            if linea.startswith("#"):
                n = len(linea) - len(linea.lstrip("#"))
                cuerpo.append(f"<h{n}>{inline(linea[n:].strip())}</h{n}>")
            elif linea.startswith("- "):
                if not en_lista:
                    cuerpo.append("<ul>"); en_lista = True
                cuerpo.append(f"<li>{inline(linea[2:])}</li>")
            elif linea.strip():
                cuerpo.append(f"<p>{inline(linea)}</p>")
    cerrar()
    return f"""<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Diagnóstico · Qolqe G5</title>
<style>body{{font:15px/1.55 system-ui,sans-serif;max-width:1000px;margin:0 auto;padding:24px 16px;color:#1c1917}}
table{{border-collapse:collapse;width:100%;font-size:14px;margin:12px 0}}th,td{{text-align:left;padding:6px 10px;border-bottom:1px solid #e7e5e4;vertical-align:top}}
pre{{background:#f5f5f4;padding:10px 12px;border-radius:6px;overflow-x:auto;font-size:13px}}code{{font-size:13px}}h4{{margin:22px 0 4px}}</style>
</head><body>{chr(10).join(cuerpo)}</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--playwright")
    ap.add_argument("--log-api")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args()
    api = diagnosticar_api(a.playwright, a.log_api) if a.playwright and a.log_api and Path(a.playwright).exists() and Path(a.log_api).exists() else None
    md = a_markdown(api)
    salida = Path(a.salida)
    salida.mkdir(parents=True, exist_ok=True)
    (salida / "diagnostico.md").write_text(md, encoding="utf-8")
    (salida / "diagnostico.html").write_text(a_html(md), encoding="utf-8")
    print(f"diagnóstico en {salida}/diagnostico.md")


if __name__ == "__main__":
    main()
