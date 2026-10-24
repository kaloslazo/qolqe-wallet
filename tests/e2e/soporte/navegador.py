"""Fábrica de WebDriver: local o remoto (Selenium Grid), con o sin cabeza, escritorio o móvil.

Selenium Manager (incluido desde Selenium 4.6) resuelve el driver y, si hace falta, descarga el
navegador: no hay que instalar chromedriver ni geckodriver a mano.
"""
from dataclasses import dataclass

from selenium import webdriver

NAVEGADORES = ("chrome", "edge", "firefox", "safari")

# Viewport y user agent de un iPhone 12 Pro para la emulación móvil de Chromium
MOVIL = {
    "deviceMetrics": {"width": 390, "height": 844, "pixelRatio": 3.0},
    "userAgent": ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
                  "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"),
}


@dataclass
class ConfigNavegador:
    nombre: str = "chrome"
    headless: bool = False
    grid: str | None = None
    movil: bool = False

    @property
    def soporta_bidi(self) -> bool:
        # safaridriver todavía no implementa WebDriver BiDi
        return self.nombre != "safari"


def _opciones(cfg: ConfigNavegador):
    if cfg.nombre in ("chrome", "edge"):
        opciones = webdriver.ChromeOptions() if cfg.nombre == "chrome" else webdriver.EdgeOptions()
        if cfg.headless:
            opciones.add_argument("--headless=new")
        # sin el aviso de "contraseña filtrada" que tapa la página tras el login
        opciones.add_argument("--disable-features=PasswordLeakDetection")
        opciones.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
            "profile.password_manager_leak_detection": False,
        })
        if cfg.movil:
            opciones.add_experimental_option("mobileEmulation", MOVIL)
    elif cfg.nombre == "firefox":
        opciones = webdriver.FirefoxOptions()
        if cfg.headless:
            opciones.add_argument("-headless")
    elif cfg.nombre == "safari":
        opciones = webdriver.SafariOptions()
    else:
        raise ValueError(f"Navegador no soportado: {cfg.nombre}. Opciones: {', '.join(NAVEGADORES)}")

    if cfg.soporta_bidi:
        opciones.enable_bidi = True
    return opciones


def crear_driver(cfg: ConfigNavegador) -> webdriver.Remote:
    opciones = _opciones(cfg)
    if cfg.grid:
        driver = webdriver.Remote(command_executor=cfg.grid, options=opciones)
    else:
        driver = {
            "chrome": webdriver.Chrome,
            "edge": webdriver.Edge,
            "firefox": webdriver.Firefox,
            "safari": webdriver.Safari,
        }[cfg.nombre](options=opciones)
    if not cfg.movil:
        driver.set_window_size(1400, 1000)
    return driver
