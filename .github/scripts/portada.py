"""Portada del sitio de reportes que el pipeline publica en GitHub Pages.

Uso: python .github/scripts/portada.py SITIO
  SITIO ya tiene los reportes copiados por el job "reportes":
    api/          reporte HTML de Playwright, junit-api.xml y resultados-api.json
    contrato/     reporte HTML y JUnit de Schemathesis
    web-chrome/   reporte.html (pytest-html), reporte-bdd.html, junit.xml
    web-firefox/  lo mismo en Firefox
Escribe SITIO/index.html con el estado de cada job, los enlaces y la matriz de trazabilidad.
"""
import html
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import resumen  # noqa: E402
import trazabilidad  # noqa: E402

e = html.escape


def contar(rutas):
    casos = []
    for ruta in rutas:
        if ruta.exists():
            casos += list(resumen.desde_playwright(str(ruta)) if ruta.suffix == ".json" else resumen.desde_junit(str(ruta)))
    return Counter(estado for estado, _, _ in casos)


def tarjeta(titulo, detalle, estado_job, conteo, enlaces):
    cifras = " · ".join(f"{conteo[k]} {k}" for k in ("passed", "xfailed", "flaky", "skipped", "failed") if conteo[k])
    links = " ".join(f'<a href="{e(href)}">{e(texto)}</a>' for texto, href in enlaces) or "<span>sin reporte</span>"
    return f"""<article class="tarjeta">
  <header><h3>{e(titulo)}</h3><span class="job {e(estado_job)}">{e(estado_job)}</span></header>
  <p>{e(detalle)}</p>
  <p class="cifras">{e(cifras) or "sin resultados"}</p>
  <nav>{links}</nav>
</article>"""


def main():
    sitio = Path(sys.argv[1])
    estados = {job: os.environ.get(f"ESTADO_{job.upper()}", "—") for job in ("api", "contrato", "web")}

    contrato_html = sorted(sitio.glob("contrato/html-*/index.html"))
    contrato_junit = sorted(sitio.glob("contrato/junit-*.xml"))
    navegadores = sorted(p.name.removeprefix("web-") for p in sitio.glob("web-*") if p.is_dir())

    tarjetas = [
        tarjeta("API", "Playwright + playwright-bdd: escenarios Gherkin del G5 y del núcleo.", estados["api"],
                contar([sitio / "api/resultados-api.json"]),
                [("Reporte HTML", "api/index.html")] if (sitio / "api/index.html").exists() else []),
        tarjeta("Contrato", "Schemathesis contra el OpenAPI. Informativo: sus hallazgos están en el informe.",
                estados["contrato"], contar(contrato_junit[-1:]),
                [("Reporte HTML", p.relative_to(sitio).as_posix()) for p in contrato_html[-1:]]),
    ]
    for nav in navegadores:
        base = sitio / f"web-{nav}"
        tarjetas.append(tarjeta(f"Web · {nav}", "Selenium 4 + pytest-bdd con Page Objects.", estados["web"],
                                contar([base / "junit.xml"]),
                                [(t, f"web-{nav}/{f}") for t, f in (("Reporte BDD", "reporte-bdd.html"),
                                                                    ("pytest-html", "reporte.html")) if (base / f).exists()]))

    web = {nav: trazabilidad.resultados_junit(str(sitio / f"web-{nav}/junit.xml"))
           for nav in navegadores if (sitio / f"web-{nav}/junit.xml").exists()}
    api_json = sitio / "api/resultados-api.json"
    historias = trazabilidad.leer_historias()
    filas, cobertura = trazabilidad.armar(trazabilidad.leer_casos(), historias,
                                          trazabilidad.resultados_api(str(api_json)) if api_json.exists() else None, web)
    ctx = trazabilidad.contexto_run()
    matriz = trazabilidad.a_html(filas, cobertura, historias, ctx)
    (sitio / "trazabilidad.md").write_text(trazabilidad.a_markdown(filas, cobertura, historias, ctx), encoding="utf-8")

    origen = f'<a href="{e(ctx["url"])}">{e(ctx["run"])}</a>' if ctx["url"] else e(ctx["run"])
    (sitio / "index.html").write_text(f"""<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reportes · Qolqe G5</title>
<style>
  :root {{ --fondo:#fafaf9; --texto:#1c1917; --suave:#57534e; --borde:#e7e5e4; --tarjeta:#fff;
          --ok:#15803d; --mal:#b91c1c; --aviso:#a16207; --gris:#78716c; --enlace:#1d4ed8; }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --fondo:#1c1917; --texto:#f5f5f4; --suave:#a8a29e; --borde:#44403c; --tarjeta:#292524;
            --ok:#4ade80; --mal:#f87171; --aviso:#facc15; --gris:#a8a29e; --enlace:#93c5fd; }}
  }}
  * {{ box-sizing:border-box; }}
  body {{ margin:0; background:var(--fondo); color:var(--texto); font:15px/1.55 system-ui, sans-serif; }}
  main {{ max-width:1100px; margin:0 auto; padding:32px 16px 64px; }}
  h1 {{ margin:0 0 4px; font-size:26px; }}
  a {{ color:var(--enlace); }}
  .sub {{ color:var(--suave); margin:0 0 28px; }}
  .tarjetas {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(240px, 1fr)); gap:12px; margin-bottom:36px; }}
  .tarjeta {{ background:var(--tarjeta); border:1px solid var(--borde); border-radius:10px; padding:14px 16px; }}
  .tarjeta header {{ display:flex; justify-content:space-between; align-items:center; gap:8px; }}
  .tarjeta h3 {{ margin:0; font-size:16px; }}
  .tarjeta p {{ margin:8px 0; color:var(--suave); font-size:14px; }}
  .tarjeta .cifras {{ color:var(--texto); font-variant-numeric:tabular-nums; }}
  .tarjeta nav a {{ margin-right:12px; font-size:14px; }}
  .job {{ font-size:12px; padding:2px 8px; border-radius:99px; border:1px solid currentColor; }}
  .success, .passed {{ color:var(--ok); }} .failure, .failed {{ color:var(--mal); }}
  .xfailed, .flaky {{ color:var(--aviso); }} .skipped, .sin, .cancelled {{ color:var(--gris); }}
  .tabla {{ overflow-x:auto; }}
  table {{ border-collapse:collapse; width:100%; font-size:14px; margin-bottom:24px; }}
  th, td {{ text-align:left; padding:6px 10px; border-bottom:1px solid var(--borde); vertical-align:top; }}
  th {{ color:var(--suave); font-weight:600; }}
  code {{ font-size:13px; }}
</style>
</head>
<body>
<main>
  <h1>Qolqe Wallet · G5 Límites</h1>
  <p class="sub">Reportes de {origen}{' · commit <code>' + e(ctx['sha']) + '</code>' if ctx['sha'] else ''} · {e(ctx['fecha'])} (hora de Lima)</p>
  <section class="tarjetas">
{chr(10).join(tarjetas)}
  </section>
  <div class="tabla">
{matriz}
  </div>
  <p class="sub">La misma matriz en Markdown: <a href="trazabilidad.md">trazabilidad.md</a></p>
</main>
</body>
</html>
""", encoding="utf-8")


if __name__ == "__main__":
    main()
