"""IA aplicada a Selenium: localizadores que se reparan solos ("self-healing") con Claude.

Cuando un localizador ya no encuentra su elemento (por ejemplo, cambió un data-testid), el sanador
manda a Claude una lista compacta de los elementos visibles de la página y la intención del
localizador ("botón para guardar el límite diario"). Claude devuelve un selector CSS nuevo, el
sanador comprueba que encuentre exactamente un elemento y lo usa. Cada reparación queda registrada
en reportes/selenium/sanaciones.json para que una persona la revise y corrija el Page Object.

Se activa con --sanar y necesita credenciales de la API de Anthropic (ANTHROPIC_API_KEY).
"""
import json
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By

MODELO = "claude-opus-5-5"
REGISTRO = Path("reportes/selenium/sanaciones.json")

# Resume la página en una lista de elementos interactivos o con texto propio
JS_ELEMENTOS = """
const visibles = [...document.querySelectorAll('button, a, input, select, textarea, [data-testid], [role], h1, h2, label')]
  .filter(e => e.offsetParent !== null || e.tagName === 'DIALOG');
return visibles.slice(0, 250).map(e => ({
  tag: e.tagName.toLowerCase(),
  id: e.id || null,
  testid: e.dataset.testid || null,
  tipo: e.getAttribute('type'),
  nombre: e.getAttribute('name'),
  aria: e.getAttribute('aria-label'),
  texto: (e.innerText || e.value || '').trim().slice(0, 60) || null,
}));
"""

ESQUEMA = {
    "type": "object",
    "properties": {
        "selector_css": {"type": "string"},
        "razon": {"type": "string"},
    },
    "required": ["selector_css", "razon"],
    "additionalProperties": False,
}


class Sanador:
    def __init__(self):
        import anthropic  # solo se necesita con --sanar

        self.cliente = anthropic.Anthropic()

    def proponer(self, driver, localizador: tuple[str, str], intencion: str):
        """Devuelve (selector_css, razon) o None si Claude no propone algo que funcione."""
        elementos = driver.execute_script(JS_ELEMENTOS)
        respuesta = self.cliente.beta.messages.create(
            model=MODELO,
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
            system=("Eres un ingeniero de automatización de pruebas con Selenium. Recibes un localizador "
                    "que dejó de funcionar, su intención y los elementos visibles de la página. Responde "
                    "con un selector CSS que identifique un único elemento que cumpla esa intención. "
                    "Prefiere atributos estables: data-testid, id, name; evita posiciones y clases."),
            messages=[{"role": "user", "content": json.dumps({
                "url": driver.current_url,
                "localizador_roto": {"estrategia": localizador[0], "valor": localizador[1]},
                "intencion": intencion,
                "elementos": elementos,
            }, ensure_ascii=False)}],
        )
        if respuesta.stop_reason == "refusal":
            return None
        texto = next((b.text for b in respuesta.content if b.type == "text"), None)
        if not texto:
            return None
        propuesta = json.loads(texto)
        selector = propuesta["selector_css"]
        if len(driver.find_elements(By.CSS_SELECTOR, selector)) != 1:
            return None
        self._registrar(driver.current_url, localizador, intencion, selector, propuesta["razon"])
        return selector, propuesta["razon"]

    @staticmethod
    def _registrar(url, localizador, intencion, selector, razon):
        REGISTRO.parent.mkdir(parents=True, exist_ok=True)
        historial = json.loads(REGISTRO.read_text()) if REGISTRO.exists() else []
        historial.append({
            "fecha": datetime.now().isoformat(timespec="seconds"),
            "url": url,
            "localizador_roto": list(localizador),
            "intencion": intencion,
            "selector_propuesto": selector,
            "razon": razon,
        })
        REGISTRO.write_text(json.dumps(historial, ensure_ascii=False, indent=2))
