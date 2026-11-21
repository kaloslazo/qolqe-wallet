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

`npm test` genera los pasos desde `features/`, levanta la app y corre las 263 pruebas (133 casos con sus ejemplos). Resultado esperado: `263 passed`. Los resultados de la última corrida (JUnit y resumen por defecto) están en [`tests/api/resultados/`](../tests/api/resultados/resumen.md). Los escenarios `@fail` detectan los defectos de [`defectos.md`](defectos.md) y cuentan como passed; entre ellos, CP-53 y CP-86 mandan transferencias simultáneas (DEF-11).

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

29 escenarios web (`features/ui/`, Gherkin en español) automatizados con Selenium 4 y pytest-bdd: los de la pantalla de límites y los del núcleo común (registro, ingreso y transferencia) con Page Objects, y uno con dos usuarios a la vez (Ana y Bruno, cada uno en su navegador) con el patrón Screenplay. Basta Python 3.11+ y un navegador; Selenium Manager descarga los drivers (y el navegador si falta).

```bash
scripts/selenium.sh todo          # los escenarios web en Chrome sin ventana + reportes/selenium/reporte.html
scripts/selenium.sh demo          # flujo feliz con Chrome visible, resaltando cada elemento
```

Resultado esperado: `37 passed, 5 xfailed` (29 escenarios BDD que se vuelven 41 pruebas por sus ejemplos, uno de ellos con dos usuarios y Screenplay, + 1 prueba de Screenplay con un actor; los 5 xfailed son los defectos conocidos de `features/ui/defectos_ui.feature`: los 3 de límites, DEF-05 y DEF-13). Si la app no está corriendo en `localhost:8000`, la suite la levanta sola con una BD propia en `reportes/selenium/`.

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

## IA: proponer casos y redactar defectos

Dos skills de Claude Code en `.claude/skills/`. Se usan desde Claude Code abierto en la raíz del repo, y lo que producen es una **propuesta**: queda en `propuestas/ia/`, fuera de `features/` y de `docs/`, y no cuenta como cobertura hasta que una persona lo revisa con [`ia-checklist.md`](ia-checklist.md).

| Skill | Cómo se pide | Qué entrega |
|---|---|---|
| `proponer-casos` | «propón casos web para HU-N-07» | `propuestas/ia/<HU>-<fecha>.md`: escenarios Gherkin con técnica, esperado citado del requisito y preguntas sobre lo que el requisito no dice |
| `reporte-defecto` | «redacta el defecto del escenario CP-NN» | `propuestas/ia/DEF-borrador-<tema>.md`: reporte en el formato de `defectos.md`, reproducido contra la app |
| `reporte-calidad` | «arma el tablero de calidad con el antes y el después» | `reportes/tablero/tablero.html` (también en Pages): mapeado por historia, testing, defectos y rendimiento frente a la entrega anterior (`calidad/antes.json`). Solo reporta |

Para aceptar una propuesta: pasar los escenarios a `features/`, implementar los pasos nuevos, y correr `npx bddgen`, `python .github/scripts/verificar_etiquetas.py` y la suite. Cada uso se anota en [`IA.md`](../IA.md).

## Pipeline

`.github/workflows/pruebas.yml` corre en cada push a una rama, en cada pull request y a mano desde la pestaña Actions (`workflow_dispatch`). No corre al subir un tag ni cuando el cambio solo toca documentación (`docs/`, archivos `.md`) o los resultados de rendimiento: antes, cada entrega corría el pipeline dos veces (la rama y el tag).

```
           ┌─▶ verificar ─┐
push / PR ─┼─▶ contrato ──┼──▶ web (chrome)  ─┐
           └─▶ api ───────┘    web (firefox) ─┴─▶ reportes ─▶ GitHub Pages   (solo main)
              etapa 1             etapa 2          etapa 3
          (en paralelo)       (en paralelo)
```

| Etapa | Job | Qué hace | Por qué ahí |
|---|---|---|---|
| 1 | `verificar` | Que cada escenario tenga su HU, CP y criterio, que cada fallo esperado tenga su DEF, que Playwright tenga todos sus pasos (`bddgen` falla si falta uno) y que pytest pueda recolectar los escenarios de Selenium | No ejecuta nada contra la app: en menos de un minuto detecta un escenario mal escrito |
| 1 | `contrato` | Gate de Schemathesis: la API cumple su OpenAPI | Es una prueba de la API con entradas generadas |
| 1 | `api` | `npm test`: los escenarios de negocio en Gherkin (playwright-bdd) | Va junto al contrato porque los dos prueban la misma API desde ángulos distintos: nuestros casos y las entradas que no imaginamos. No depende de verificar ni de contrato, así que no espera por ellos |
| 2 | `web (chrome)`, `web (firefox)` | Los escenarios de interfaz en Gherkin con Selenium + pytest-bdd | En paralelo entre sí (son independientes) y solo si pasó toda la etapa 1: Selenium prepara sus datos y su sesión por la API del producto, y un fallo web con la API rota no aporta información. Es lo más lento y lo que más se rompe |
| 3 | `reportes` | Publica en Pages la portada, la trazabilidad con el historial de corridas, la cobertura frente a Schemathesis y el [diagnóstico por prueba](reporteria.md) | También cuando algo falla (o la web no corrió): es cuando más hace falta ver el reporte |

**Duración.** La etapa 1 dura lo que dura su job más largo (la API, de 2 a 3 minutos con la instalación) y no la suma de los tres. Respecto de la Parte 2, donde la API corría junto a la web, la web ahora empieza unos dos minutos más tarde.

Si falla algo de la etapa 1 (verificar, contrato o API), la web no corre (queda como skipped) y el reporte lo dice; así se ahorran los minutos de la suite más larga. En una rama o PR, un push nuevo cancela la corrida anterior; en `main` no, porque cada corrida queda en el historial. Cada job tiene un tiempo máximo (5 a 15 minutos) para que uno colgado no consuma minutos.

Cada job deja un resumen en la página del run (`.github/scripts/resumen.py`), sus reportes como artefacto y, desde `main`, el sitio en [kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/).

### Quality gates

Un cambio pasa a `main` solo si pasa todos los gates bloqueantes:

| Gate | Job | Qué mide (métrica) | Umbral | Valor de referencia (20-nov) | Bloquea |
|---|---|---|---|---|---|
| Trazabilidad | `verificar` | Escenarios sin `@HU`, `@CP` único o `@CA`; criterios del núcleo y de G5 sin escenario de API; fallos esperados sin un `@DEF` que exista en `defectos.md` | 0 faltantes | 162 escenarios revisados · **48 de 48** criterios con caso | sí |
| Gherkin compila | `verificar` | Pasos de los `.feature` de API sin implementar (`bddgen`); errores al recolectar los de Selenium | 0 pasos sin definir · 0 errores | 133 casos de API con sus pasos · 42 pruebas web recolectadas | sí |
| Contrato | `contrato` | Fallos de los checks de Schemathesis (`not_a_server_error`, `status_code_conformance`, `content_type_conformance`, `response_schema_conformance`, `response_headers_conformance`, `ignored_auth` y el resto, salvo los cuatro de la fila siguiente) en 4 fases: ejemplos, cobertura, fuzzing y flujos con estado | 0 fallos | **13 de 13** operaciones probadas · 4 fases en verde · 31 escenarios con estado | sí |
| Hallazgos de contrato conocidos | `contrato` | `positive_data_acceptance`, `negative_data_rejection`, `unsupported_method`, `allow_header_conformance`: reglas de negocio que el OpenAPI no declara y la cabecera `Allow` de los 405, analizados en el informe | se reportan | 15 hallazgos (el número varía un poco con la semilla) | no |
| Funcional API | `api` | Pruebas que fallan, que pasan solo al reintentar (flaky) o que quedaron con `test.only`; un `@fail` que empieza a pasar | 0 failed · 0 flaky (`failOnFlakyTests`) · 0 `test.only` (`forbidOnly`) | **263 de 263** (16 son fallos esperados de defectos) · 0 flaky · 1.4 min | sí |
| Funcional web | `web` | Lo mismo con `@defecto` (xfail estricto), en Chrome y en Firefox | 0 failed en los dos navegadores | 37 pasan + 5 fallos esperados por navegador (esperado: la web nueva se verificó con Playwright; Actions la corre por primera vez) | sí |
| Rendimiento | manual (`tests/performance/correr.sh`) | p95 del tiempo de respuesta de consultas e inicio de sesión; p95 de operaciones de dinero; tasa de peticiones fallidas; consistencia del dinero (saldos contra movimientos) | p95 consultas < 800 ms · p95 dinero < 1500 ms · fallas < 1 % · dinero cuadrado | hora punta (100 usuarios): 51 ms · 126 ms · 0 % · cuadrado | antes de cada campaña; no en cada push, porque necesita el contenedor con CPU limitada y 20 minutos o más |

Los ceros son a propósito: en un gate de *calidad*, la regla es «cero fallos», y lo que informa es la columna de valor de referencia (cuánto se revisó). El de rendimiento es el único con umbrales numéricos, porque los fija el requerimiento.

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
