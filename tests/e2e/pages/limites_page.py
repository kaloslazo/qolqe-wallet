from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.relative_locator import locate_with
from selenium.webdriver.support.ui import Select, WebDriverWait

from tests.e2e.pages.base_page import BasePage, tid


class LimitesPage(BasePage):
    LIMITE_DIARIO = tid("limite-diario")
    USADO = tid("limite-usado")
    DISPONIBLE = tid("limite-disponible")
    PENDIENTE = tid("limite-pendiente")
    MENSAJE = tid("limites-mensaje")
    NUEVO_LIMITE = tid("input-nuevo-limite")
    GUARDAR_LIMITE = tid("boton-guardar-limite")

    TIPO_ALERTA = tid("select-alerta-tipo")
    UMBRAL = tid("input-alerta-umbral")
    CREAR_ALERTA = tid("boton-crear-alerta")
    ERROR_ALERTA = tid("alerta-error")
    CONTADOR = tid("contador-alertas")
    LISTA = tid("lista-alertas")
    TOAST = tid("toast")

    # diálogos que la app crea al vuelo
    CONFIRMAR = tid("boton-confirmar-accion")
    UMBRAL_DIALOGO = tid("input-editar-umbral")
    GUARDAR_DIALOGO = tid("boton-guardar-dialogo")

    def abrir(self):
        super().abrir("/limites")
        self.esperar_carga()
        return self

    def esperar_carga(self):
        # la tarjeta se pinta cuando responde GET /api/limites
        self.espera.until(lambda d: d.find_element(*self.LIMITE_DIARIO).text.strip())
        self.espera.until(lambda d: d.find_element(*self.CONTADOR).text.strip())

    # ---- límite diario
    def limite_diario(self) -> str:
        return self.texto(self.LIMITE_DIARIO)

    def cambiar_limite(self, monto):
        self.escribir(self.NUEVO_LIMITE, monto, "campo para escribir el nuevo límite diario")
        self.boton_guardar_limite().click()

    def boton_guardar_limite(self):
        """Selenium 4 · localizador relativo: el primer botón debajo del campo del nuevo límite."""
        campo = self.visible(self.NUEVO_LIMITE, "campo para escribir el nuevo límite diario")
        boton = self.driver.find_element(locate_with(By.TAG_NAME, "button").below(campo))
        self._resaltar(boton)
        return boton

    def mensaje(self, esperado: str = "") -> str:
        return self.esperar_texto(self.MENSAJE, esperado)

    def aviso_pendiente(self) -> str:
        return self.driver.find_element(*self.PENDIENTE).text

    def sin_aviso_pendiente(self) -> bool:
        try:
            WebDriverWait(self.driver, 3).until(EC.invisibility_of_element_located(self.PENDIENTE))
            return True
        except TimeoutException:
            return False

    # ---- alertas
    def crear_alerta(self, tipo_visible: str, umbral):
        Select(self.visible(self.TIPO_ALERTA, "lista para elegir el tipo de gasto")).select_by_visible_text(tipo_visible)
        self.escribir(self.UMBRAL, umbral, "campo para escribir el umbral de la alerta")
        self.clic(self.CREAR_ALERTA, "botón para crear la alerta")

    def resultado_alerta(self) -> str:
        """Texto del aviso que aparezca primero: el toast de éxito o el error del formulario."""
        def aviso(driver):
            for localizador in (self.TOAST, self.ERROR_ALERTA):
                elementos = driver.find_elements(*localizador)
                if elementos and elementos[0].is_displayed() and elementos[0].text.strip():
                    return elementos[0].text.strip()
            return False
        return self.espera.until(aviso)

    @staticmethod
    def _fila(titulo: str):
        # XPath: el <li> de la alerta cuyo título coincide, para operar sobre sus propios botones
        return By.XPATH, (f"//li[@data-testid='alerta'][.//*[@data-testid='alerta-titulo' "
                          f"and normalize-space()='{titulo}']]")

    def fila_alerta(self, titulo: str):
        return self.visible(self._fila(titulo))

    def estado_alerta(self, titulo: str, esperado: str = "") -> str:
        localizador = (By.XPATH, self._fila(titulo)[1] + "//*[@data-testid='alerta-estado']")
        return self.esperar_texto(localizador, esperado)

    def _boton_de(self, titulo: str, testid: str):
        fila = self.fila_alerta(titulo)
        boton = fila.find_element(*tid(testid))
        # en pantallas chicas el toast inferior tapa los botones de la última alerta: se centra el botón
        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", boton)
        self._resaltar(boton)
        return boton

    def pausar(self, titulo: str):
        self._boton_de(titulo, "boton-pausar-alerta").click()
        self.espera.until(EC.presence_of_element_located(
            (By.XPATH, self._fila(titulo)[1] + "//*[@data-testid='boton-reanudar-alerta']")))

    def reanudar(self, titulo: str):
        self._boton_de(titulo, "boton-reanudar-alerta").click()
        self.espera.until(EC.presence_of_element_located(
            (By.XPATH, self._fila(titulo)[1] + "//*[@data-testid='boton-pausar-alerta']")))

    def eliminar_y_confirmar(self, titulo: str):
        self._boton_de(titulo, "boton-eliminar-alerta").click()
        self.clic(self.CONFIRMAR, "botón para confirmar la eliminación en el diálogo")
        self.espera.until(EC.invisibility_of_element_located(self._fila(titulo)))

    def editar_umbral(self, titulo: str, umbral):
        self._boton_de(titulo, "boton-editar-alerta").click()
        self.escribir(self.UMBRAL_DIALOGO, umbral, "campo del diálogo para el nuevo umbral")
        self.clic(self.GUARDAR_DIALOGO, "botón para guardar el diálogo")

    def contador(self, esperado: str = "") -> str:
        return self.esperar_texto(self.CONTADOR, esperado)

    def texto_lista(self, esperado: str = "") -> str:
        return self.esperar_texto(self.LISTA, esperado)
