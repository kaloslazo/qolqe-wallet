"""WebDriver BiDi (Selenium 4): escuchar la consola del navegador e interceptar la red."""
import json


class Consola:
    """Guarda los mensajes de consola y los errores de JavaScript de la página."""

    def __init__(self, driver):
        self.mensajes: list[str] = []
        self.errores: list[str] = []
        driver.script.add_console_message_handler(lambda e: self.mensajes.append(f"[{e.level}] {e.text}"))
        driver.script.add_javascript_error_handler(lambda e: self.errores.append(e.text))

    def resumen(self) -> str:
        lineas = [*self.mensajes, *(f"[error JS] {e}" for e in self.errores)]
        return "\n".join(lineas) or "(sin mensajes de consola)"


def responder_error(driver, patron: str, metodo: str, detalle: str, estado: int = 503) -> str:
    """Hace que las peticiones `metodo` a `patron` reciban un error simulado sin llegar al servidor."""
    cuerpo = json.dumps({"codigo": "SERVICIO_NO_DISPONIBLE", "detail": detalle})

    def manejar(peticion):
        if peticion.method == metodo:
            peticion.provide_response(status=estado, headers={"Content-Type": "application/json"}, body=cuerpo)

    return driver.network.add_request_handler([patron], manejar)
