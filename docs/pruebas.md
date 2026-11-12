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

`npm test` genera los pasos desde `features/`, levanta la app y corre las 260 pruebas (131 casos con sus ejemplos). Resultado esperado: `260 passed`. Los escenarios `@fail` detectan los defectos de [`defectos.md`](defectos.md) y cuentan como passed; entre ellos, CP-53 y CP-86 mandan transferencias simultáneas (DEF-11).

## Contrato con Schemathesis

En una terminal se levanta la app y en otra se corre el contrato:

```bash
uvicorn qolqe.main:app --port 8000     # terminal 1
npm run contrato                       # terminal 2
```

Corre dos pasadas. El **gate** revisa que la API cumpla lo que declara su OpenAPI (sin 500, esquema, códigos, cabeceras y autenticación) y, si algo falla, el script sale con error. Los **hallazgos conocidos** (reglas de negocio que el OpenAPI no declara y la cabecera `Allow` de los 405) se reportan aparte y no bloquean: están analizados en el informe. Los reportes quedan en `reportes/schemathesis/gate/` y `reportes/schemathesis/hallazgos/`. No correr `npm test` y `npm run contrato` al mismo tiempo: comparten el puerto y la base de datos.

### Cobertura frente a Schemathesis

¿Qué prueban nuestros escenarios que Schemathesis no, y al revés? Se responde con el log de la app: cada línea (`"PUT /api/limites/alertas/7 HTTP/1.1" 422`) se lleva a su operación del OpenAPI y se cuentan los códigos HTTP que provocó cada suite. Luego se cruzan con los hallazgos del JUnit de Schemathesis.

```bash
scripts/cobertura.sh      # levanta la app, corre npm test y el contrato, y escribe docs/cobertura-contrato.md
```

Por operación, la tabla dice:

| Lectura | Significa |
|---|---|
| cubierto | Nuestros escenarios la prueban y Schemathesis no encontró nada nuevo |
| hallazgo ya cubierto | Schemathesis reporta algo, pero ya tenemos un escenario que provoca ese mismo código |
| faltan casos: 422, … | Schemathesis provocó esos códigos y ningún escenario nuestro lo hace: candidatos a escenario nuevo |
| sin escenarios nuestros | Solo la prueba Schemathesis |

En el pipeline, los jobs `api` y `contrato` guardan el log de su app, y `reportes` publica la tabla en Pages (debajo de la matriz) y en el resumen del run. El script es `.github/scripts/cobertura_contrato.py`. De esta tabla salió, por ejemplo, el CP-82: Schemathesis borraba alertas con un id que no cabe en un entero (422) y ningún escenario nuestro lo hacía.

## Interfaz web con Selenium + pytest-bdd

16 escenarios web (`features/ui/`, Gherkin en español) automatizados con Selenium 4 y pytest-bdd: los de la pantalla de límites con Page Objects y uno con dos usuarios a la vez (Ana y Bruno, cada uno en su navegador) con el patrón Screenplay. Basta Python 3.11+ y un navegador; Selenium Manager descarga los drivers (y el navegador si falta).

```bash
scripts/selenium.sh todo          # los escenarios web en Chrome sin ventana + reportes/selenium/reporte.html
scripts/selenium.sh demo          # flujo feliz con Chrome visible, resaltando cada elemento
```

Resultado esperado: `17 passed, 3 xfailed` (16 escenarios BDD, uno de ellos con dos usuarios y Screenplay, + 1 ejemplo de Screenplay con un actor; los 3 xfailed son los defectos conocidos de `features/ui/defectos_ui.feature`). Si la app no está corriendo en `localhost:8000`, la suite la levanta sola con una BD propia en `reportes/selenium/`.

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

Opciones de pytest (`pytest tests/e2e --help`): `--navegador chrome|edge|firefox|safari`, `--evidencia con|fallos|sin`, `--headless`, `--movil`, `--grid URL`, `--demo`, `--sanar`, `--romper`, `--url-app`, `--url-navegador`. Para filtrar por etiqueta de Gherkin: `-m happy`, `-m bidi`, `-m HU-G5-03`.

Safari necesita habilitarse una vez: `sudo safaridriver --enable` y, en Safari, Desarrollo › Permitir automatización remota. Safari no implementa WebDriver BiDi, así que el escenario `@bidi` se omite allí.

Glosario, cómo armar una prueba nueva y guion de la demo: [`guia-selenium.md`](guia-selenium.md).

## Rendimiento con k6

Qolqe corre en Docker con 1 CPU y 1 GB y k6 genera la carga desde la laptop. Cada prueba se corre con un solo comando que prepara los datos, mide CPU y memoria, revisa el dinero antes y después y deja los gráficos en `tests/performance/resultados/<prueba>/`:

```bash
docker build -f tests/performance/Dockerfile -t qolqe-perf .
tests/performance/correr.sh carga        # humo, demo, carga, pico, estres o resistencia
```

El detalle de cada escenario está en [`tests/performance/README.md`](../tests/performance/README.md) y el análisis en el informe de rendimiento.

## Pipeline

`.github/workflows/pruebas.yml` corre en cada push a una rama, en cada pull request y a mano desde la pestaña Actions (`workflow_dispatch`). No corre al subir un tag ni cuando el cambio solo toca documentación (`docs/`, archivos `.md`) o los resultados de rendimiento: antes, cada entrega corría el pipeline dos veces (la rama y el tag).

```
           ┌─▶ verificar ─┐      ┌─▶ api ───────────┐
push / PR ─┤              ├──────┼─▶ web (chrome)   ├─▶ reportes ─▶ GitHub Pages   (solo main)
           └─▶ contrato ──┘      └─▶ web (firefox) ─┘
              etapa 1 (~1 min)      etapa 2              etapa 3
```

| Etapa | Job | Qué hace | Por qué ahí |
|---|---|---|---|
| 1 | `verificar` | Que cada escenario tenga su HU, CP y criterio, que cada fallo esperado tenga su DEF que Playwright tenga todos sus pasos (`bddgen` falla si falta uno) y que pytest pueda recolectar los escenarios de Selenium | No ejecuta nada contra la app: en menos de un minuto detecta un escenario mal escrito |
| 1 | `contrato` | Gate de Schemathesis: la API cumple su OpenAPI | Si la interfaz de la API está rota, no tiene sentido correr los escenarios que la usan |
| 2 | `api` | `npm test`: los escenarios de API con Playwright | Corre solo si la etapa 1 pasó |
| 2 | `web (chrome)`, `web (firefox)` | Los escenarios de interfaz con Selenium | En paralelo con `api`: no depende de sus resultados y así el pipeline dura lo que la suite más lenta |
| 3 | `reportes` | Publica en Pages la portada, la trazabilidad con el historial de corridas y la cobertura frente a Schemathesis | También cuando algo falla: es cuando más hace falta ver el reporte |

Si falla la etapa 1, las suites largas no corren (quedan como skipped) y se ahorran unos 3 minutos de runner por corrida. En una rama o PR, un push nuevo cancela la corrida anterior; en `main` no, porque cada corrida queda en el historial. Cada job tiene un tiempo máximo (5 a 15 minutos) para que uno colgado no consuma minutos.

Cada job deja un resumen en la página del run (`.github/scripts/resumen.py`), sus reportes como artefacto y, desde `main`, el sitio en [kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/).

### Quality gates

Un cambio pasa a `main` solo si pasa todos los gates bloqueantes:

| Gate | Job | Criterio | Umbral | Bloquea |
|---|---|---|---|---|
| Trazabilidad | `verificar` | Escenarios con `@HU`, `@CP` único y `@CA`; criterios del núcleo y de G5 con al menos un escenario de API; fallos esperados con un `@DEF` que existe en `defectos.md` | 0 faltantes | sí |
| Gherkin compila | `verificar` | Cada paso de los `.feature` de API tiene su implementación (`bddgen`) y los escenarios de Selenium se recolectan sin errores | 0 pasos sin definir · 0 errores de recolección | sí |
| Contrato | `contrato` | Respuestas sin 500, con los códigos, tipos, esquema y cabeceras que declara el OpenAPI; ninguna ruta protegida responde sin token (checks `not_a_server_error`, `status_code_conformance`, `content_type_conformance`, `response_schema_conformance`, `response_headers_conformance`, `ignored_auth` y el resto, salvo los cuatro de la fila siguiente) | 0 fallos | sí |
| Hallazgos de contrato conocidos | `contrato` | `positive_data_acceptance`, `negative_data_rejection`, `unsupported_method`, `allow_header_conformance`: reglas de negocio que el OpenAPI no declara y la cabecera `Allow` de los 405, analizados en el informe | se reportan | no |
| Funcional API | `api` | Todos los escenarios pasan; un `@fail` solo puede fallar por su defecto y, si empieza a pasar, el job falla para actualizar el escenario | 0 failed · 0 flaky (`failOnFlakyTests`: si pasa al reintentar, falla igual) · 0 `test.only` (`forbidOnly`) | sí |
| Funcional web | `web` | Lo mismo con `@defecto` (xfail estricto), en Chrome y en Firefox | 0 failed en los dos navegadores | sí |
| Rendimiento | manual (`tests/performance/correr.sh`) | Umbrales del requerimiento en k6: p95 de consultas y login < 800 ms, p95 de dinero < 1500 ms, fallas < 1 %, dinero cuadrado | k6 sale con error si no se cumplen | antes de cada campaña; no en cada push, porque necesita el contenedor con CPU limitada y 20 minutos o más |

Para que GitHub no deje fusionar un PR con el pipeline en rojo: Settings › Branches › regla para `main` › *Require status checks to pass* con `verificar`, `contrato`, `api`, `web (chrome)` y `web (firefox)`.

### Evidencia con o sin capturas

Al correr el pipeline a mano (Actions › Pipeline › *Run workflow*) se elige la evidencia de los reportes:

| Opción | Web (Selenium) | API (Playwright) |
|---|---|---|
| `con` | Una captura de pantalla por paso en el reporte BDD y en pytest-html | Traza de cada escenario: cada petición y respuesta, abrible desde el reporte HTML |
| `fallos` | Solo la captura del paso que falla | Traza solo de los escenarios que fallan |
| `sin` | Ninguna captura: el reporte más liviano | Sin trazas |

En push y PR se usa `fallos`. En local es la variable `EVIDENCIA` o la opción `--evidencia` de pytest:

```bash
EVIDENCIA=con npm test
scripts/selenium.sh todo --evidencia sin
```

### Trazabilidad

Cada escenario lleva `@CP-NN`, las `@HU` que cubre y sus criterios: `@CA-N-07-3` es HU-N-07 CA3. `.github/scripts/trazabilidad.py` cruza los `.feature` con los resultados del run (el JSON de Playwright y la propiedad `etiquetas` que el conftest escribe en el JUnit de pytest) y genera:

- la cobertura por historia, separando casos funcionales y técnicos (`@tecnico`), y cuántos criterios tienen caso;
- la cobertura por criterio, con el texto del criterio y sus casos;
- los casos con el resultado de esta corrida y el de las **últimas 30 corridas de `main`**: un caso estable sale como `passed 30`; uno inestable, como `passed 28 · failed 2 · último fallo run #45`.

El historial vive en el sitio publicado (`historial.json`): el job `reportes` lo baja, le agrega la corrida y lo vuelve a publicar. Así la trazabilidad no se queda en el último run: muestra desde cuándo falla un caso, si un defecto se corrigió y qué casos son inestables.

Para actualizar [`trazabilidad.md`](trazabilidad.md) en cada entrega, se baja `trazabilidad.md` del sitio publicado o se genera en local:

```bash
python .github/scripts/trazabilidad.py --api reportes/resultados-api.json \
  --web chrome=reportes/selenium/junit.xml --md docs/trazabilidad.md
```
