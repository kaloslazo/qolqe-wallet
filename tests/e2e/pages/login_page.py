import json

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages.base_page import BasePage, tid


class LoginPage(BasePage):
    CELULAR = tid("input-celular")
    PIN = tid("input-pin")
    INGRESAR = tid("boton-ingresar")
    ERROR = tid("login-error")

    def abrir(self):
        return super().abrir("/login")

    def ingresar(self, celular: str, pin: str):
        self.escribir(self.CELULAR, celular, "campo para escribir el número de celular")
        self.escribir(self.PIN, pin, "campo para escribir el PIN de 4 dígitos")
        self.clic(self.INGRESAR, "botón para ingresar a la billetera")
        self.espera.until(EC.url_contains("/inicio"))

    def iniciar_sesion_por_api(self, datos_login: dict):
        """Atajo híbrido: la sesión se obtiene por API y se inyecta en sessionStorage,
        como lo haría la app. Ahorra el login por la UI en los escenarios que no lo prueban."""
        self.abrir()
        self.driver.execute_script("sessionStorage.setItem('qolqe.sesion', arguments[0]);", json.dumps(datos_login))


class Menu(BasePage):
    """Menú lateral de las páginas autenticadas: se navega por el texto visible del enlace."""

    def ir_a(self, opcion: str):
        self.clic((By.LINK_TEXT, opcion), f"enlace del menú '{opcion}'")
