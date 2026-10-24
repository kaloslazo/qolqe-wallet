"""Tareas y preguntas del G5. Cada una se lee como una frase: CrearAlerta.de("Recargas").desde(50)."""
from tests.e2e.pages.limites_page import LimitesPage
from tests.e2e.pages.login_page import LoginPage, Menu
from tests.e2e.screenplay import NavegarLaWeb
from tests.e2e.soporte.api import USUARIOS


def _driver(actor):
    return actor.usando(NavegarLaWeb).driver


# ---------------------------------------------------------------- tareas
class IniciarSesion:
    def __init__(self, celular: str, pin: str):
        self.celular, self.pin = celular, pin

    @classmethod
    def como(cls, usuario: str) -> "IniciarSesion":
        return cls(*USUARIOS[usuario])

    def realizada_por(self, actor):
        LoginPage(_driver(actor)).abrir().ingresar(self.celular, self.pin)


class IrA:
    def __init__(self, opcion: str):
        self.opcion = opcion

    def realizada_por(self, actor):
        Menu(_driver(actor)).ir_a(self.opcion)
        LimitesPage(_driver(actor)).esperar_carga()


class CambiarLimiteDiario:
    def __init__(self, monto: int):
        self.monto = monto

    @classmethod
    def a(cls, monto: int) -> "CambiarLimiteDiario":
        return cls(monto)

    def realizada_por(self, actor):
        pagina = LimitesPage(_driver(actor))
        pagina.cambiar_limite(self.monto)
        pagina.mensaje("Tu límite diario fue actualizado")


class CrearAlerta:
    def __init__(self, tipo: str, umbral: int | None = None):
        self.tipo, self.umbral = tipo, umbral

    @classmethod
    def de(cls, tipo: str) -> "CrearAlerta":
        return cls(tipo)

    def desde(self, umbral: int) -> "CrearAlerta":
        self.umbral = umbral
        return self

    def realizada_por(self, actor):
        LimitesPage(_driver(actor)).crear_alerta(self.tipo, self.umbral)


# ---------------------------------------------------------------- preguntas
class LimiteDiarioVigente:
    def __init__(self, esperado: str = ""):
        self.esperado = esperado

    def respondida_por(self, actor) -> str:
        pagina = LimitesPage(_driver(actor))
        return pagina.esperar_texto(pagina.LIMITE_DIARIO, self.esperado)


class EstadoDeAlerta:
    def __init__(self, titulo: str, esperado: str = ""):
        self.titulo, self.esperado = titulo, esperado

    def respondida_por(self, actor) -> str:
        return LimitesPage(_driver(actor)).estado_alerta(self.titulo, self.esperado)
