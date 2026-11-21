from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages.base_page import BasePage, tid


class RegistroPage(BasePage):
    DNI = tid("input-dni")
    NOMBRES = tid("input-nombres")
    CELULAR = tid("input-celular")
    PIN = tid("input-pin")
    PIN_CONFIRMACION = tid("input-pin-confirmacion")
    REGISTRAR = tid("boton-registrar")
    ERROR = tid("registro-error")

    def abrir(self):
        return super().abrir("/registro")

    def registrar(self, dni: str, nombres: str, celular: str, pin: str):
        """Llena el formulario y lo envía. Termina cuando la app responde: el login con el aviso, o el error."""
        self.escribir(self.DNI, dni, "campo para escribir el DNI")
        self.escribir(self.NOMBRES, nombres, "campo para escribir los nombres")
        self.escribir(self.CELULAR, celular, "campo para escribir el celular")
        self.escribir(self.PIN, pin, "campo para escribir el PIN")
        self.escribir(self.PIN_CONFIRMACION, pin, "campo para repetir el PIN")
        self.clic(self.REGISTRAR, "botón para crear la cuenta")
        self.espera.until(EC.any_of(EC.url_contains("/login"), EC.visibility_of_element_located(self.ERROR)))

    def error(self, esperado: str = "") -> str:
        return self.esperar_texto(self.ERROR, esperado)
