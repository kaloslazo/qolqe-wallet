"""IA aplicada a Selenium: localizadores que se reparan solos ("self-healing") con Gemini o Claude.

Cuando un localizador ya no encuentra su elemento (por ejemplo, cambió un data-testid), el sanador
manda al modelo una lista compacta de los elementos visibles de la página y la intención del
localizador ("botón para guardar el límite diario"). El modelo devuelve un selector CSS nuevo, el
sanador comprueba que encuentre exactamente un elemento y lo usa. Cada reparación queda registrada
en reportes/selenium/sanaciones.json para que una persona la revise y corrija el Page Object.

Se activa con --sanar. Usa Gemini si existe GEMINI_API_KEY (modelo en GEMINI_MODEL, por defecto
gemini-flash-lite-latest, el más rápido); si no, Claude con las credenciales de Anthropic (ANTHROPIC_API_KEY).
"""
import json
import os
from datetime import datetime
from pathlib import Path

import requests
from selenium.webdriver.common.by import By

MODELO = "claude-opus-5-5"
URL_GEMINI = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
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


SISTEMA = ("Eres un ingeniero de automatización de pruebas con Selenium. Recibes un localizador "
           "que dejó de funcionar, su intención y los elementos visibles de la página. Responde "
           "con un selector CSS que identifique un único elemento que cumpla esa intención. "
           "Prefiere atributos estables: data-testid, id, name; evita posiciones y clases.")


class Sanador:
    def __init__(self):
        self.clave_gemini = os.environ.get("GEMINI_API_KEY")
        if self.clave_gemini:
            self.proveedor = "Gemini"
            self.modelo_gemini = os.environ.get("GEMINI_MODEL", "gemini-flash-lite-latest")
        else:
            import anthropic  # solo se necesita con --sanar y sin GEMINI_API_KEY

            self.proveedor = "Claude"
            self.cliente = anthropic.Anthropic()

    def proponer(self, driver, localizador: tuple[str, str], intencion: str):
        """Devuelve (selector_css, razon) o None si el modelo no propone algo que funcione."""
        pedido = json.dumps({
            "url": driver.current_url,
            "localizador_roto": {"estrategia": localizador[0], "valor": localizador[1]},
            "intencion": intencion,
            "elementos": driver.execute_script(JS_ELEMENTOS),
        }, ensure_ascii=False)
        texto = self._preguntar_gemini(pedido) if self.clave_gemini else self._preguntar_claude(pedido)
        if not texto:
            return None
        propuesta = json.loads(texto)
        selector = propuesta["selector_css"]
        if len(driver.find_elements(By.CSS_SELECTOR, selector)) != 1:
            return None
        self._registrar(driver.current_url, localizador, intencion, selector, propuesta["razon"])
        return selector, propuesta["razon"]

    def _preguntar_gemini(self, pedido: str) -> str | None:
        respuesta = requests.post(
            URL_GEMINI.format(modelo=self.modelo_gemini),
            headers={"x-goog-api-key": self.clave_gemini},
            json={
                "systemInstruction": {"parts": [{"text": SISTEMA}]},
                "contents": [{"role": "user", "parts": [{"text": pedido}]}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": {
                        "type": "OBJECT",
                        "properties": {"selector_css": {"type": "STRING"}, "razon": {"type": "STRING"}},
                        "required": ["selector_css", "razon"],
                    },
                },
            },
            timeout=60,
        )
        respuesta.raise_for_status()
        candidatos = respuesta.json().get("candidates") or []
        partes = candidatos[0].get("content", {}).get("parts", []) if candidatos else []
        return partes[0].get("text") if partes else None

    def _preguntar_claude(self, pedido: str) -> str | None:
        respuesta = self.cliente.beta.messages.create(
            model=MODELO,
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low", "format": {"type": "json_schema", "schema": ESQUEMA}},
            system=SISTEMA,
            messages=[{"role": "user", "content": pedido}],
        )
        if respuesta.stop_reason == "refusal":
            return None
        return next((b.text for b in respuesta.content if b.type == "text"), None)

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
