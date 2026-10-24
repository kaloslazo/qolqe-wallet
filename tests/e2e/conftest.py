"""Infraestructura de la suite E2E con Selenium + pytest-bdd.

Opciones (pytest tests/e2e --help, grupo "qolqe-e2e"):
  --navegador chrome|edge|firefox|safari   --headless   --movil   --grid URL
  --demo (resalta y pausa)   --sanar (IA)   --romper (rompe un localizador a propósito)
  --url-app (API, para preparar datos)     --url-navegador (la app vista desde el navegador)
"""
import base64
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from urllib.parse import urlparse

import pytest

from tests.e2e.pages.base_page import BasePage, tid
from tests.e2e.pages.limites_page import LimitesPage
from tests.e2e.soporte.api import ApiQolqe
from tests.e2e.soporte import reporte as reporte_bdd
from tests.e2e.soporte.bidi import Consola
from tests.e2e.soporte.navegador import NAVEGADORES, ConfigNavegador, crear_driver

CARPETA = Path("reportes/selenium")


def pytest_addoption(parser):
    grupo = parser.getgroup("qolqe-e2e")
    grupo.addoption("--navegador", default="chrome", choices=NAVEGADORES)
    grupo.addoption("--headless", action="store_true", help="sin ventana (CI)")
    grupo.addoption("--movil", action="store_true", help="emula un iPhone 12 Pro (Chrome/Edge)")
    grupo.addoption("--grid", default=None, help="URL de Selenium Grid, p. ej. http://localhost:4444")
    grupo.addoption("--demo", action="store_true", help="resalta cada elemento antes de usarlo")
    grupo.addoption("--sanar", action="store_true", help="repara localizadores rotos con Claude")
    grupo.addoption("--romper", action="store_true", help="rompe el localizador del nuevo límite (demo de --sanar)")
    grupo.addoption("--url-app", default="http://localhost:8000")
    grupo.addoption("--url-navegador", default=None, help="por defecto, la misma que --url-app")


def pytest_configure(config):
    for marca in ("G5", "ui", "happy", "demo", "reloj", "e2e", "ventanas", "dialogos", "datos", "bidi", "red",
                  "R-G5-04", "defecto", "screenplay", *(f"HU-G5-0{n}" for n in range(1, 9)), *(f"DEF-0{n}" for n in range(1, 4))):
        config.addinivalue_line("markers", f"{marca}: etiqueta Gherkin")


def pytest_collection_modifyitems(items):
    """Los escenarios @defecto describen el comportamiento correcto y fallan mientras el defecto exista:
    se marcan como fallo esperado (xfail estricto). Con --runxfail se ven en rojo, como fallas reales."""
    for item in items:
        if item.get_closest_marker("defecto"):
            ids = [m.name for m in item.iter_markers() if m.name.startswith("DEF-")]
            item.add_marker(pytest.mark.xfail(reason=f"Defecto conocido {', '.join(ids)} (docs/defectos.md)", strict=True))


# ---------------------------------------------------------------- la app bajo prueba
@pytest.fixture(scope="session")
def app(pytestconfig):
    """Cliente de la API. Si la app no está corriendo en localhost, la levanta con una BD propia."""
    url = pytestconfig.getoption("--url-app")
    api = ApiQolqe(url)
    proceso = None
    if not api.esta_arriba():
        destino = urlparse(url)
        if destino.hostname not in ("localhost", "127.0.0.1"):
            pytest.exit(f"La app no responde en {url}")
        CARPETA.mkdir(parents=True, exist_ok=True)
        entorno = {**os.environ, "QOLQE_MODO_PRUEBA": "1", "QOLQE_BD": str(CARPETA / "qolqe-e2e.db")}
        anfitrion = "0.0.0.0" if pytestconfig.getoption("--grid") else "127.0.0.1"
        proceso = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "qolqe.main:app", "--host", anfitrion, "--port", str(destino.port or 80)],
            env=entorno, stdout=open(CARPETA / "uvicorn.log", "w"), stderr=subprocess.STDOUT)
        for _ in range(120):
            if api.esta_arriba():
                break
            time.sleep(1)
        else:
            proceso.terminate()
            pytest.exit(f"La app no levantó; revisar {CARPETA / 'uvicorn.log'}")
    yield api
    api.hora_real()
    if proceso:
        proceso.terminate()


# ---------------------------------------------------------------- el navegador
@pytest.fixture
def config_navegador(pytestconfig) -> ConfigNavegador:
    return ConfigNavegador(
        nombre=pytestconfig.getoption("--navegador"),
        headless=pytestconfig.getoption("--headless"),
        grid=pytestconfig.getoption("--grid"),
        movil=pytestconfig.getoption("--movil"),
    )


@pytest.fixture
def driver(request, app, config_navegador, pytestconfig, monkeypatch):
    if request.node.get_closest_marker("bidi") and not config_navegador.soporta_bidi:
        pytest.skip(f"{config_navegador.nombre} no implementa WebDriver BiDi")

    BasePage.url_base = (pytestconfig.getoption("--url-navegador") or pytestconfig.getoption("--url-app")).rstrip("/")
    BasePage.demo = pytestconfig.getoption("--demo")
    if pytestconfig.getoption("--sanar"):
        from tests.e2e.soporte.sanador import Sanador
        monkeypatch.setattr(BasePage, "sanador", Sanador())
    if pytestconfig.getoption("--romper"):
        monkeypatch.setattr(LimitesPage, "NUEVO_LIMITE", tid("input-limite-nuevo"))

    navegador = crear_driver(config_navegador)
    if config_navegador.soporta_bidi:
        request.node.stash[CONSOLA] = Consola(navegador)
    yield navegador
    navegador.quit()


@pytest.fixture
def contexto() -> dict:
    """Estado compartido entre los pasos de un escenario (por ejemplo, la sesión obtenida por API)."""
    return {}


# ---------------------------------------------------------------- evidencia: capturas por paso y reportes HTML
CAPTURAS = pytest.StashKey[list]()
CONSOLA = pytest.StashKey[Consola]()
ESCENARIO = pytest.StashKey[reporte_bdd.Escenario]()
ESCENARIOS: list[reporte_bdd.Escenario] = []


def _capturar(request, titulo: str) -> str | None:
    """Guarda una captura del navegador; devuelve su ruta relativa a reportes/selenium/."""
    if "driver" not in request.fixturenames:
        return None
    navegador = request.getfixturevalue("driver")
    capturas = request.node.stash.setdefault(CAPTURAS, [])
    png = navegador.get_screenshot_as_png()
    carpeta = Path("capturas") / re.sub(r"[^\w.-]+", "_", request.node.name)[:120]
    (CARPETA / carpeta).mkdir(parents=True, exist_ok=True)
    archivo = carpeta / f"{len(capturas) + 1:02d}.png"
    (CARPETA / archivo).write_bytes(png)
    capturas.append((titulo, base64.b64encode(png).decode()))
    return archivo.as_posix()


def _mensaje(error: BaseException) -> str:
    # los mensajes de Selenium traen el stacktrace del driver: solo interesa lo de antes
    texto = str(error).split("Stacktrace:")[0].strip() or type(error).__name__
    if isinstance(error, AssertionError):
        texto = texto.splitlines()[0]  # sin el detalle "assert ... where ..." que agrega pytest
        return texto[:600]
    return f"{type(error).__name__}: {texto}"[:600]


def pytest_bdd_before_scenario(request, feature, scenario):
    esc = reporte_bdd.Escenario(
        caracteristica=feature.name, nombre=scenario.name, etiquetas=sorted(scenario.tags),
        pasos=[reporte_bdd.Paso(f"{p.keyword.strip()} {p.name}") for p in scenario.steps])
    request.node.stash[ESCENARIO] = esc
    request.node.stash[PUNTERO] = 0


PUNTERO = pytest.StashKey[int]()


def _paso_actual(request):
    esc = request.node.stash.get(ESCENARIO, None)
    i = request.node.stash.get(PUNTERO, 0)
    if esc is None or i >= len(esc.pasos):
        return None
    request.node.stash[PUNTERO] = i + 1
    return esc.pasos[i]


def pytest_bdd_after_step(request, feature, scenario, step, step_func, step_func_args):
    paso = _paso_actual(request)
    captura = _capturar(request, f"{step.keyword} {step.name}")
    if paso:
        paso.estado, paso.captura = "ok", captura


def pytest_bdd_step_error(request, feature, scenario, step, step_func, step_func_args, exception):
    paso = _paso_actual(request)
    captura = _capturar(request, f"FALLÓ · {step.keyword} {step.name}")
    if paso:
        paso.estado, paso.captura, paso.error = "mal", captura, _mensaje(exception)


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    resultado = yield
    reporte = resultado.get_result()

    # reporte BDD propio
    if reporte.when == "setup" and reporte.skipped:
        ESCENARIOS.append(reporte_bdd.Escenario("Omitidos", item.name, [], estado="omitido",
                                                motivo=str(reporte.longrepr[-1]) if isinstance(reporte.longrepr, tuple) else None))
    if reporte.when == "call" and ESCENARIO in item.stash:
        esc = item.stash[ESCENARIO]
        esc.duracion = reporte.duration
        if hasattr(reporte, "wasxfail"):
            esc.estado, esc.motivo = ("defecto", reporte.wasxfail) if reporte.skipped else ("fallo", "Se esperaba que fallara (defecto conocido) y pasó: ¿se corrigió?")
        else:
            esc.estado = "paso" if reporte.passed else "fallo"
        if CONSOLA in item.stash:
            esc.consola = item.stash[CONSOLA].resumen()
        ESCENARIOS.append(esc)

    # pytest-html: capturas y consola como extras
    html = item.config.pluginmanager.getplugin("html")
    if reporte.when != "call" or not html:
        return
    extras = getattr(reporte, "extras", [])
    for titulo, imagen in item.stash.get(CAPTURAS, []):
        extras.append(html.extras.image(imagen, titulo))
    if CONSOLA in item.stash:
        extras.append(html.extras.text(item.stash[CONSOLA].resumen(), "Consola del navegador (BiDi)"))
    reporte.extras = extras


def pytest_sessionfinish(session):
    if not ESCENARIOS:
        return
    config = session.config
    modo = f"Grid {config.getoption('--grid')}" if config.getoption("--grid") else "local"
    meta = {"Navegador": config.getoption("--navegador"), "Ejecución": modo,
            "Vista": "móvil (iPhone 12 Pro)" if config.getoption("--movil") else "escritorio",
            "Escenarios": len(ESCENARIOS)}
    CARPETA.mkdir(parents=True, exist_ok=True)
    reporte_bdd.escribir(ESCENARIOS, meta, CARPETA / "reporte-bdd.html")
