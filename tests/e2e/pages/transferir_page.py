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
    COMPROBANTE_CODIGO = tid("comprobante-codigo")
    COMPROBANTE_DESTINO = tid("comprobante-destino")
    COMPROBANTE_COMISION = tid("comprobante-comision")
    COMPROBANTE_TOTAL = tid("comprobante-total")
    COMPROBANTE_SALDO = tid("comprobante-saldo")
    CONFIRMAR_MONTO = tid("confirmar-monto")
    CONFIRMAR_COMISION = tid("confirmar-comision")
    CONFIRMAR_TOTAL = tid("confirmar-total")

    def abrir(self):
        return super().abrir("/transferir")

    def transferir(self, monto, celular: str):
        self.pedir(monto, celular)
        self._confirmar_si_hay_dialogo()

    def transferir_a_otro_banco(self, monto, cci: str):
        self.pedir_a_otro_banco(monto, cci)
        self._confirmar_si_hay_dialogo()

    def pedir(self, monto, celular: str):
        """Llena el formulario y pulsa Continuar: deja abierto el diálogo de confirmación (o el error)."""
        self.escribir(self.CELULAR_DESTINO, celular, "campo para escribir el celular de destino")
        self._continuar(monto)

    def pedir_a_otro_banco(self, monto, cci: str):
        self.clic(self.PESTANA_INTERBANCARIA, "pestaña para transferir a otro banco")
        self.escribir(self.CCI, cci, "campo para escribir el CCI de 20 dígitos")
        self._continuar(monto)

    def _continuar(self, monto):
        self.escribir(self.MONTO, monto, "campo para escribir el monto a transferir")
        self.clic(self.CONTINUAR, "botón para continuar con la transferencia")
        # se abre el <dialog> con la comisión calculada, o aparece un error antes de confirmar
        self.espera.until(EC.any_of(EC.visibility_of_element_located(self.DIALOGO),
                                    EC.visibility_of_element_located(self.ERROR)))

    def confirmar(self):
        self.clic(self.CONFIRMAR, "botón para confirmar la transferencia")
        # termina cuando la app responde: comprobante o error
        self.espera.until(EC.any_of(EC.visibility_of_element_located(self.COMPROBANTE),
                                    EC.visibility_of_element_located(self.ERROR)))

    def _confirmar_si_hay_dialogo(self):
        if self.driver.find_element(*self.DIALOGO).is_displayed():
            self.confirmar()

    def dialogo(self) -> dict:
        """Lo que muestra el diálogo de confirmación antes de transferir (HU-N-09: la simulación de la comisión)."""
        return {"monto": self.texto(self.CONFIRMAR_MONTO), "comision": self.texto(self.CONFIRMAR_COMISION),
                "total": self.texto(self.CONFIRMAR_TOTAL)}

    def comprobante(self) -> dict:
        self.visible(self.COMPROBANTE)
        return {"codigo": self.texto(self.COMPROBANTE_CODIGO), "destino": self.texto(self.COMPROBANTE_DESTINO),
                "monto": self.texto(self.COMPROBANTE_MONTO), "comision": self.texto(self.COMPROBANTE_COMISION),
                "total": self.texto(self.COMPROBANTE_TOTAL), "saldo": self.texto(self.COMPROBANTE_SALDO)}

    def error(self) -> str:
        return self.texto(self.ERROR)

    def monto_comprobante(self) -> str:
        self.visible(self.COMPROBANTE)
        return self.texto(self.COMPROBANTE_MONTO)
