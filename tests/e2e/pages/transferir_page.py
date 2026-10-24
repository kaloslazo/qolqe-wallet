from selenium.webdriver.support import expected_conditions as EC

from tests.e2e.pages.base_page import BasePage, tid


class TransferirPage(BasePage):
    PESTANA_INTERBANCARIA = tid("pestana-interbancaria")
    CELULAR_DESTINO = tid("input-celular-destino")
    CCI = tid("input-cci")
    MONTO = tid("input-monto")
    CONTINUAR = tid("boton-continuar")
    DIALOGO = tid("dialogo-confirmacion")
    CONFIRMAR = tid("boton-confirmar")
    ERROR = tid("transferencia-error")
    COMPROBANTE = tid("comprobante")
    COMPROBANTE_MONTO = tid("comprobante-monto")

    def abrir(self):
        return super().abrir("/transferir")

    def transferir(self, monto, celular: str):
        self.escribir(self.CELULAR_DESTINO, celular, "campo para escribir el celular de destino")
        self._confirmar(monto)

    def transferir_a_otro_banco(self, monto, cci: str):
        self.clic(self.PESTANA_INTERBANCARIA, "pestaña para transferir a otro banco")
        self.escribir(self.CCI, cci, "campo para escribir el CCI de 20 dígitos")
        self._confirmar(monto)

    def _confirmar(self, monto):
        self.escribir(self.MONTO, monto, "campo para escribir el monto a transferir")
        self.clic(self.CONTINUAR, "botón para continuar con la transferencia")
        # se abre el <dialog> con la comisión calculada, o aparece un error antes de confirmar
        self.espera.until(EC.any_of(EC.visibility_of_element_located(self.DIALOGO),
                                    EC.visibility_of_element_located(self.ERROR)))
        if self.driver.find_element(*self.DIALOGO).is_displayed():
            self.clic(self.CONFIRMAR, "botón para confirmar la transferencia")
            # termina cuando la app responde: comprobante o error
            self.espera.until(EC.any_of(EC.visibility_of_element_located(self.COMPROBANTE),
                                        EC.visibility_of_element_located(self.ERROR)))

    def error(self) -> str:
        return self.texto(self.ERROR)

    def monto_comprobante(self) -> str:
        self.visible(self.COMPROBANTE)
        return self.texto(self.COMPROBANTE_MONTO)
