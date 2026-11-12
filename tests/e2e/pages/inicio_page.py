from tests.e2e.pages.base_page import BasePage, tid


class InicioPage(BasePage):
    SALDO = tid("saldo-valor")
    RECIENTES = tid("lista-recientes")
    MOVIMIENTO = tid("movimiento-reciente")

    def abrir(self):
        return super().abrir("/inicio")

    def saldo(self, esperado: str = "") -> str:
        return self.esperar_texto(self.SALDO, esperado)

    def movimientos_recientes(self) -> list[str]:
        self.visible(self.MOVIMIENTO)
        return [m.text for m in self.driver.find_elements(*self.MOVIMIENTO)]
