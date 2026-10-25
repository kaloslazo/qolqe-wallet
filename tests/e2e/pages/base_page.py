"""Page Object base: esperas explícitas, modo demo (resaltar y pausar) y localizadores auto-reparables."""
import time

from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


def tid(valor: str) -> tuple[str, str]:
    """Localizador por data-testid, el atributo estable que Qolqe expone en cada control."""
    return By.CSS_SELECTOR, f'[data-testid="{valor}"]'


class BasePage:
    ESPERA = 10
    # La configuración se comparte entre páginas: la fija conftest al crear el driver
    url_base = "http://localhost:8000"
    demo = False
    sanador = None
    reparados: dict = {}  # localizador roto -> selector que propuso la IA (se pregunta una sola vez)

    def __init__(self, driver):
        self.driver = driver
        self.espera = WebDriverWait(driver, self.ESPERA, ignored_exceptions=[StaleElementReferenceException])

    def abrir(self, ruta: str = ""):
        self.driver.get(f"{self.url_base}{ruta}")
        return self

    # ---- búsqueda de elementos
    def visible(self, localizador, intencion: str | None = None):
        if localizador in self.reparados:
            localizador = (By.CSS_SELECTOR, self.reparados[localizador])
        try:
            elemento = self.espera.until(EC.visibility_of_element_located(localizador))
        except TimeoutException as error:
            if not (self.sanador and intencion):
                quien = f" ({intencion})" if intencion else ""
                raise TimeoutException(f"No apareció el elemento {localizador[1]}{quien} en {self.ESPERA} s") from error
            elemento = self._sanar(localizador, intencion)
        self._resaltar(elemento)
        return elemento

    def _sanar(self, localizador, intencion):
        try:
            propuesta = self.sanador.proponer(self.driver, localizador, intencion)
        except Exception as error:  # sin credenciales, sin red, límite de uso...
            raise TimeoutException(f"No se encontró {localizador} y la IA no respondió: {error}") from error
        if not propuesta:
            raise TimeoutException(f"No se encontró {localizador} y la IA no propuso un reemplazo")
        selector, razon = propuesta
        BasePage.reparados[localizador] = selector
        print(f"\n[IA · {self.sanador.proveedor}] {localizador[1]} -> {selector} ({razon})")
        return self.espera.until(EC.visibility_of_element_located((By.CSS_SELECTOR, selector)))

    def texto(self, localizador) -> str:
        return self.visible(localizador).text

    def esperar_texto(self, localizador, texto: str) -> str:
        """Espera hasta que el elemento contenga `texto` (la UI pinta después de responder la API)."""
        try:
            self.espera.until(EC.text_to_be_present_in_element(localizador, texto))
        except TimeoutException:
            pass  # la aserción del paso muestra el texto real
        return self.texto(localizador)

    # ---- acciones
    def clic(self, localizador, intencion: str | None = None):
        elemento = self.visible(localizador, intencion)
        self.espera.until(EC.element_to_be_clickable(elemento))
        elemento.click()

    def escribir(self, localizador, valor, intencion: str | None = None):
        elemento = self.visible(localizador, intencion)
        elemento.clear()
        elemento.send_keys(str(valor))

    def _resaltar(self, elemento):
        if not self.demo:
            return
        self.driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});"
            "arguments[0].style.outline = '3px solid #e5534b';"
            "arguments[0].style.outlineOffset = '2px';", elemento)
        time.sleep(0.6)
        self.driver.execute_script("arguments[0].style.outline = '';", elemento)
