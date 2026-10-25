"""Reporte BDD en HTML: un resumen y, por escenario, sus pasos de Gherkin con estado y captura de pantalla.

Las capturas no se incrustan: el HTML las enlaza en capturas/ (misma carpeta), así pesa poco.
"""
import html
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

ESTADOS = {
    "paso": ("Pasó", "ok"),
    "defecto": ("Defecto conocido", "def"),
    "fallo": ("Falló", "mal"),
    "omitido": ("Omitido", "omit"),
}


@dataclass
class Paso:
    texto: str
    estado: str = "pendiente"  # ok | mal | pendiente
    captura: str | None = None  # ruta relativa al reporte
    error: str | None = None
    traza: str | None = None  # archivo, línea y código de nuestro proyecto donde ocurrió el error


@dataclass
class Escenario:
    caracteristica: str
    nombre: str
    etiquetas: list[str]
    pasos: list[Paso] = field(default_factory=list)
    estado: str = "paso"
    duracion: float = 0.0
    motivo: str | None = None
    consola: str | None = None


def _e(texto) -> str:
    return html.escape(str(texto or ""))


def _paso(p: Paso) -> str:
    icono = {"ok": "✓", "mal": "✗"}.get(p.estado, "–")
    error = f'<pre class="error">{_e(p.error)}</pre>' if p.error else ""
    if p.traza:
        error += f'<details class="traza"><summary>Ver traza técnica</summary><pre>{_e(p.traza)}</pre></details>'
    captura = (f'<a href="{_e(p.captura)}" target="_blank"><img loading="lazy" src="{_e(p.captura)}" alt="captura: {_e(p.texto)}"></a>'
               if p.captura else "")
    return f'<li class="paso {p.estado}"><span class="icono">{icono}</span><div><p>{_e(p.texto)}</p>{error}</div>{captura}</li>'


def _escenario(esc: Escenario) -> str:
    etiqueta, clase = ESTADOS[esc.estado]
    abierto = " open" if esc.estado in ("fallo", "defecto") else ""
    tags = "".join(f'<span class="tag">@{_e(t)}</span>' for t in esc.etiquetas)
    motivo = f'<p class="motivo">{_e(esc.motivo)}</p>' if esc.motivo else ""
    consola = (f'<details class="consola"><summary>Consola del navegador (WebDriver BiDi)</summary><pre>{_e(esc.consola)}</pre></details>'
               if esc.consola else "")
    return f"""
<details class="escenario {clase}"{abierto}>
  <summary><span class="pill {clase}">{etiqueta}</span><span class="titulo">{_e(esc.nombre)}</span>
    <span class="dur">{esc.duracion:.1f} s</span></summary>
  <div class="cuerpo"><div class="tags">{tags}</div>{motivo}<ol class="pasos">{"".join(_paso(p) for p in esc.pasos)}</ol>{consola}</div>
</details>"""


def escribir(escenarios: list[Escenario], meta: dict, ruta: Path) -> None:
    conteo = {k: sum(1 for e in escenarios if e.estado == k) for k in ESTADOS}
    total = len(escenarios) or 1
    barra = "".join(f'<span class="{ESTADOS[k][1]}" style="width:{conteo[k] / total * 100:.2f}%"></span>' for k in ESTADOS if conteo[k])
    tarjetas = "".join(f'<div class="tarjeta {ESTADOS[k][1]}"><b>{conteo[k]}</b><span>{ESTADOS[k][0]}</span></div>' for k in ESTADOS)
    orden = {"fallo": 0, "defecto": 1, "omitido": 2, "paso": 3}
    por_caracteristica: dict[str, list[Escenario]] = {}
    for esc in sorted(escenarios, key=lambda e: orden[e.estado]):
        por_caracteristica.setdefault(esc.caracteristica, []).append(esc)
    secciones = "".join(f'<section><h2>{_e(c)}</h2>{"".join(_escenario(e) for e in lista)}</section>'
                        for c, lista in por_caracteristica.items())
    datos = " · ".join(f"{_e(k)}: <b>{_e(v)}</b>" for k, v in meta.items())
    ruta.write_text(f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reporte E2E · G5 Límites</title>
<style>
:root {{ --bg:#f6f5f1; --card:#fff; --ink:#14181f; --suave:#5d6470; --linea:#dcdde2;
  --ok:#2f8f5b; --ok-bg:#e3f3ea; --mal:#c8402f; --mal-bg:#fbe6e3; --def:#a86b00; --def-bg:#fbf0d9; --omit:#6a7180; --omit-bg:#eceef1; }}
@media (prefers-color-scheme: dark) {{ :root {{ --bg:#14181f; --card:#1c222b; --ink:#eef0f3; --suave:#9aa3b0; --linea:#2c3440;
  --ok:#5cc28a; --ok-bg:#183327; --mal:#f08070; --mal-bg:#3a1f1c; --def:#e8b04a; --def-bg:#3a2e14; --omit:#9aa3b0; --omit-bg:#262d37; }} }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:16px/1.45 system-ui,-apple-system,"Segoe UI",sans-serif; }}
main {{ max-width:1100px; margin:0 auto; padding:32px 16px 64px; }}
h1 {{ margin:0 0 4px; font-size:28px; }} h2 {{ font-size:18px; margin:32px 0 12px; color:var(--suave); }}
.meta {{ color:var(--suave); font-size:14px; }}
.tarjetas {{ display:grid; grid-template-columns:repeat(4,1fr); gap:12px; margin:24px 0 12px; }}
.tarjeta {{ background:var(--card); border:1px solid var(--linea); border-radius:12px; padding:16px; border-top:4px solid; }}
.tarjeta b {{ display:block; font-size:34px; }} .tarjeta span {{ color:var(--suave); font-size:14px; }}
.tarjeta.ok {{ border-top-color:var(--ok); }} .tarjeta.mal {{ border-top-color:var(--mal); }}
.tarjeta.def {{ border-top-color:var(--def); }} .tarjeta.omit {{ border-top-color:var(--omit); }}
.barra {{ display:flex; height:10px; border-radius:6px; overflow:hidden; background:var(--linea); }}
.barra span.ok {{ background:var(--ok); }} .barra span.mal {{ background:var(--mal); }} .barra span.def {{ background:var(--def); }} .barra span.omit {{ background:var(--omit); }}
.escenario {{ background:var(--card); border:1px solid var(--linea); border-radius:12px; margin:8px 0; border-left:5px solid var(--linea); }}
.escenario.ok {{ border-left-color:var(--ok); }} .escenario.mal {{ border-left-color:var(--mal); }}
.escenario.def {{ border-left-color:var(--def); }} .escenario.omit {{ border-left-color:var(--omit); }}
summary {{ cursor:pointer; padding:12px 16px; display:flex; gap:12px; align-items:center; }}
.titulo {{ flex:1; font-weight:600; }} .dur {{ color:var(--suave); font-size:14px; white-space:nowrap; }}
.pill {{ font-size:12px; font-weight:700; padding:3px 10px; border-radius:99px; white-space:nowrap; }}
.pill.ok {{ color:var(--ok); background:var(--ok-bg); }} .pill.mal {{ color:var(--mal); background:var(--mal-bg); }}
.pill.def {{ color:var(--def); background:var(--def-bg); }} .pill.omit {{ color:var(--omit); background:var(--omit-bg); }}
.cuerpo {{ padding:0 16px 16px; }}
.tags {{ display:flex; flex-wrap:wrap; gap:6px; }} .tag {{ font:12px ui-monospace,Menlo,monospace; color:var(--suave); background:var(--bg); padding:2px 8px; border-radius:6px; }}
.motivo {{ color:var(--def); font-size:14px; margin:8px 0 0; }}
.pasos {{ list-style:none; padding:0; margin:12px 0 0; }}
.paso {{ display:grid; grid-template-columns:24px 1fr 160px; gap:12px; align-items:start; padding:8px 0; border-top:1px solid var(--linea); }}
.paso p {{ margin:0; }} .paso .icono {{ font-weight:700; text-align:center; }}
.paso.ok .icono {{ color:var(--ok); }} .paso.mal .icono {{ color:var(--mal); }} .paso.pendiente {{ color:var(--suave); }}
.paso img {{ width:160px; border-radius:6px; border:1px solid var(--linea); display:block; }}
.paso.mal img {{ outline:3px solid var(--mal); }}
pre {{ white-space:pre-wrap; word-break:break-word; font:13px/1.4 ui-monospace,Menlo,monospace; margin:6px 0 0; }}
pre.error {{ color:var(--mal); background:var(--mal-bg); padding:8px 10px; border-radius:8px; }}
.traza summary, .consola summary {{ padding:6px 0; color:var(--suave); font-size:14px; }}
.traza pre {{ background:var(--bg); padding:8px 10px; border-radius:8px; }}
.consola {{ margin-top:12px; }} .consola summary {{ padding:6px 0; color:var(--suave); font-size:14px; }}
@media (max-width:640px) {{ .tarjetas {{ grid-template-columns:repeat(2,1fr); }} .paso {{ grid-template-columns:24px 1fr; }} .paso img {{ grid-column:2; width:100%; }} }}
</style></head>
<body><main>
<h1>Reporte E2E · G5 Límites</h1>
<p class="meta">{datos} · {datetime.now():%d/%m/%Y %H:%M}</p>
<div class="tarjetas">{tarjetas}</div>
<div class="barra" role="img" aria-label="Proporción de escenarios por estado">{barra}</div>
{secciones}
</main></body></html>""", encoding="utf-8")
