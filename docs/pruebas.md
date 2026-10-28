# Cómo correr las pruebas

Todo se corre desde la raíz del repo con el `.venv` activo. En Windows, los scripts de `scripts/` se corren desde Git Bash.

## Instalación

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-pruebas.txt
npm install
```

Para las pruebas de interfaz hace falta además `pip install -r requirements-e2e.txt`.

## API con Playwright + playwright-bdd

```bash
npm test
npx playwright show-report
```

`npm test` genera los pasos desde `features/`, levanta la app y corre los 108 escenarios. Resultado esperado: `107 passed, 1 skipped`. Los escenarios `@fail` detectan los defectos de [`defectos.md`](defectos.md) y cuentan como passed; el omitido es de rendimiento (Parte 3).

## Contrato con Schemathesis

En una terminal se levanta la app y en otra se corre el contrato:

```bash
uvicorn qolqe.main:app --port 8000     # terminal 1
npm run contrato                       # terminal 2
```

El reporte queda en `reportes/schemathesis/`. No correr `npm test` y `npm run contrato` al mismo tiempo: comparten el puerto y la base de datos.

## Interfaz web con Selenium + pytest-bdd

15 escenarios de la pantalla de límites (`features/ui/limites_ui.feature`, Gherkin en español) automatizados con Selenium 4, pytest-bdd y Page Objects. Basta Python 3.11+ y un navegador; Selenium Manager descarga los drivers (y el navegador si falta).

```bash
scripts/selenium.sh todo          # 15 escenarios en Chrome sin ventana + reportes/selenium/reporte.html
scripts/selenium.sh demo          # flujo feliz con Chrome visible, resaltando cada elemento
```

Resultado esperado: `16 passed, 3 xfailed` (15 escenarios BDD + 1 ejemplo con el patrón Screenplay; los 3 xfailed son los defectos conocidos de `features/ui/defectos_ui.feature`). Si la app no está corriendo en `localhost:8000`, la suite la levanta sola con una BD propia en `reportes/selenium/`.

| Modo | Qué hace |
|---|---|
| `scripts/selenium.sh preparar` | Antes de la demo: levanta el Grid y calienta navegadores |
| `scripts/selenium.sh defectos` | Los 3 defectos conocidos como fallas reales (rojo) y abre el reporte |
| `scripts/selenium.sh navegadores` | La suite en Chrome, Edge y Firefox |
| `scripts/selenium.sh movil` | Flujo feliz emulando un iPhone 12 Pro |
| `scripts/selenium.sh grid` | Levanta Selenium Grid 4 en Docker (`docker-compose.grid.yml`) y corre en Chromium y Firefox remotos. Consola: http://localhost:4444/ui |
| `scripts/selenium.sh romper` | Rompe a propósito un localizador: el flujo feliz falla |
| `scripts/selenium.sh ia` | El mismo localizador roto, reparado por IA: Gemini con `GEMINI_API_KEY` o Claude con `ANTHROPIC_API_KEY`; queda registro en `reportes/selenium/sanaciones.json` |
| `scripts/selenium.sh reporte` | Abre `reportes/selenium/reporte-bdd.html`: cada escenario con sus pasos, una captura por paso, el error en una frase y la consola del navegador |

Opciones de pytest (`pytest tests/e2e --help`): `--navegador chrome|edge|firefox|safari`, `--headless`, `--movil`, `--grid URL`, `--demo`, `--sanar`, `--romper`, `--url-app`, `--url-navegador`. Para filtrar por etiqueta de Gherkin: `-m happy`, `-m bidi`, `-m HU-G5-03`.

Safari necesita habilitarse una vez: `sudo safaridriver --enable` y, en Safari, Desarrollo › Permitir automatización remota. Safari no implementa WebDriver BiDi, así que el escenario `@bidi` se omite allí.

Glosario, cómo armar una prueba nueva y guion de la demo: [`guia-selenium.md`](guia-selenium.md).
