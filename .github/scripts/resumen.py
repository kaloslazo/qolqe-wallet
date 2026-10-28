"""Resumen de un job en la página del run: lee los resultados y escribe una tabla en Markdown.

Uso: python .github/scripts/resumen.py "Título" resultados.(xml|json) [más archivos...]

- .xml: JUnit XML (pytest, Schemathesis). Los xfail de pytest cuentan como fallos esperados.
- .json: reporter JSON de Playwright, que distingue los @fail (fallos esperados) de los passed.

Escribe en $GITHUB_STEP_SUMMARY si existe; si no, en la salida estándar.
"""
import html
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

ETIQUETAS = {"passed": "✅ passed", "xfailed": "🟡 fallo esperado (defecto reportado)", "flaky": "⚠️ flaky",
             "skipped": "⏭️ skipped", "failed": "❌ failed"}


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def primera_linea(texto):
    return html.escape(ANSI.sub("", texto or "").strip().splitlines()[0][:160]) if (texto or "").strip() else ""


def desde_junit(ruta):
    for caso in ET.parse(ruta).getroot().iter("testcase"):
        prop = caso.find("properties/property[@name='etiquetas']")
        nombre = caso.get("name")
        if prop is not None:
            nombre = f"{nombre} ({prop.get('value')})"
        fallo = caso.find("failure")
        if fallo is None:
            fallo = caso.find("error")
        omitido = caso.find("skipped")
        if fallo is not None:
            yield "failed", nombre, primera_linea(fallo.get("message"))
        elif omitido is not None:
            estado = "xfailed" if omitido.get("type") == "pytest.xfail" else "skipped"
            yield estado, nombre, primera_linea(omitido.get("message"))
        else:
            yield "passed", nombre, ""


def desde_playwright(ruta):
    def recorrer(suite, ruta_titulos):
        for spec in suite.get("specs", []):
            titulo = " › ".join(ruta_titulos + [spec["title"]])
            tags = " ".join(t.lstrip("@") for t in spec["tags"] if t.lstrip("@").startswith(("HU-", "CP-", "DEF-")))
            for test in spec["tests"]:
                esperado_falla = any(a["type"] == "fail" for a in test["annotations"])
                estado = {"expected": "xfailed" if esperado_falla else "passed", "unexpected": "failed",
                          "skipped": "skipped", "flaky": "flaky"}[test["status"]]
                error = next((r["error"]["message"] for r in test["results"] if r.get("error")), "")
                # en un fallo esperado basta la etiqueta DEF; el mensaje se ve en el reporte HTML
                yield estado, f"{titulo} ({tags})", "" if estado == "xfailed" else primera_linea(error)
        for hija in suite.get("suites", []):
            yield from recorrer(hija, ruta_titulos + [hija["title"]])

    for suite in json.loads(Path(ruta).read_text(encoding="utf-8"))["suites"]:
        yield from recorrer(suite, [])


def main():
    titulo, archivos = sys.argv[1], sys.argv[2:]
    casos = []
    faltantes = []
    for ruta in archivos:
        if not Path(ruta).exists():
            faltantes.append(ruta)
            continue
        casos += list(desde_playwright(ruta) if ruta.endswith(".json") else desde_junit(ruta))

    conteo = Counter(estado for estado, _, _ in casos)
    md = [f"### {titulo}", ""]
    if faltantes:
        md += [f"> ❌ No se encontraron resultados: {', '.join(f'`{f}`' for f in faltantes)}", ""]
    md += ["| Resultado | Casos |", "|---|---:|"]
    md += [f"| {ETIQUETAS[e]} | {conteo[e]} |" for e in ETIQUETAS if conteo[e]]
    md += [f"| **Total** | **{len(casos)}** |", ""]
    for estado in ("failed", "flaky", "xfailed", "skipped"):
        lista = [(n, m) for e, n, m in casos if e == estado]
        if lista:
            md += [f"<details{' open' if estado in ('failed', 'flaky') else ''}><summary>{ETIQUETAS[estado]} ({len(lista)})</summary>", ""]
            md += [f"- {n}" + (f": {m}" if m else "") for n, m in lista]
            md += ["", "</details>", ""]

    texto = "\n".join(md) + "\n"
    destino = os.environ.get("GITHUB_STEP_SUMMARY")
    if destino:
        with open(destino, "a", encoding="utf-8") as f:
            f.write(texto)
    else:
        print(texto)


if __name__ == "__main__":
    main()
