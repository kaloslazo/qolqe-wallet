"""Patrón Screenplay: la prueba se cuenta desde quien usa la app.

  Actor      ─ tiene ─▶  Habilidades   (navegar la web)
    │ intenta              │
    ▼                      ▼
  Tareas  ── usan ──▶  Page Objects    (dónde están los elementos)
    │
  Preguntas  ─ responden lo que el actor ve en pantalla

Screenplay no reemplaza a los Page Objects: los usa. Es la prueba de que dos patrones conviven.
"""


class NavegarLaWeb:
    """Habilidad: el actor tiene un navegador."""

    def __init__(self, driver):
        self.driver = driver


class Actor:
    def __init__(self, nombre: str):
        self.nombre = nombre
        self._habilidades = {}

    @classmethod
    def llamado(cls, nombre: str) -> "Actor":
        return cls(nombre)

    def que_puede(self, *habilidades) -> "Actor":
        for habilidad in habilidades:
            self._habilidades[type(habilidad)] = habilidad
        return self

    def usando(self, tipo):
        return self._habilidades[tipo]

    def intenta(self, *tareas) -> None:
        for tarea in tareas:
            tarea.realizada_por(self)

    def ve(self, pregunta):
        return pregunta.respondida_por(self)
