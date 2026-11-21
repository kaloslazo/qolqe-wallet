# Reportería y logs: de un job en rojo hasta la causa

Cada herramienta trae su reporte por defecto, y ese reporte dice **qué** prueba falló. Para encontrar **por qué** agregamos lo que falta en cada etapa y cruzamos los logs de la app con los resultados. Este documento es el mapa: qué reporte hay en cada etapa, cómo se llega al fallo, qué logs se recogen, cuáles mapeamos nosotros y cuáles no (y por qué).

Todo se publica al terminar el último job en el sitio de GitHub Pages ([kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/)) y se resume en la página de la corrida. Con `EVIDENCIA=con` (opción al lanzar el pipeline a mano) cada paso lleva captura (web) o traza de cada petición (API); con `fallos`, solo lo que falla; con `sin`, un reporte liviano. Ver [`pruebas.md`](pruebas.md#evidencia-con-o-sin-capturas).

## 1. Qué reporte hay en cada etapa

| Etapa | Reporte por defecto de la herramienta | Lo que agregamos para ver el detalle | Cómo se llega al fallo |
|---|---|---|---|
| **verificar** | Playwright-bdd falla si falta un paso; pytest falla si no recolecta | `verificar_etiquetas.py` dice **archivo, línea y escenario** y la regla rota («falta el criterio que cubre», «fallo esperado sin @DEF-NN») | La salida del job nombra el escenario exacto; se corrige la etiqueta o el paso |
| **contrato** | Schemathesis: consola, JUnit y HTML con el **comando `curl` que reproduce** cada hallazgo | Dos pasadas: el *gate* bloquea; los *hallazgos conocidos* se reportan sin bloquear. `cobertura_contrato.py` cruza los hallazgos con la operación del OpenAPI y con lo que probaron nuestros escenarios | HTML del gate → el check que falló → copiar el `curl` y reproducir. En la cobertura se ve si nuestros escenarios ya probaban esa operación |
| **api** | Playwright: lista, HTML, JUnit y JSON | **Diagnóstico por prueba** (`diagnostico.py`): para cada prueba que no pasó limpia, lo que dijo la aserción, los requests que hizo y el código que respondió el servidor, y la traza de Python si hubo un 500. Con `EVIDENCIA=con`, la traza completa de cada petición en el HTML | `diagnostico.html` → el caso (`CP-NN`, `HU`, `DEF`) → su tramo de requests. Un `⚠ error del servidor` apunta a la excepción del log |
| **web** (Chrome y Firefox) | pytest: JUnit y pytest-html | **Reporte BDD propio** (`reporte-bdd.html`): cada escenario con sus pasos de Gherkin, estado por paso, captura de pantalla, el error y la **traza de nuestro código**, y la **consola del navegador** (WebDriver BiDi) | `reporte-bdd.html` → escenario en rojo (abierto por defecto) → el paso que falló, con su captura. La consola dice si hubo un error de JavaScript. |
| **rendimiento** (local, no corre en Actions) | k6: resumen por consola y tablero HTML | `correr.sh` guarda por prueba: series de tiempo (CSV), CPU, memoria e hilos de Qolqe y de k6 cada segundo, el log de la app, la revisión del dinero (`integridad.txt`) y gráficos | `resumen.md` → umbral que falló → gráficos y `recursos_*.csv` para ver cuándo → `log_qolqe.txt.gz` para ver qué dijo la app en ese minuto |
| **reportes** | — | Portada con el estado de cada job, **matriz de trazabilidad con las últimas 30 corridas**, cobertura del contrato, diagnóstico y la corrida en Qase | Portada → tarjeta del job en rojo → su reporte |

### Ruta corta cuando un job sale rojo

1. **verificar rojo:** leer el job; dice el escenario y la regla. Se arregla en el `.feature`.
2. **contrato rojo:** abrir el HTML del gate; cada fallo trae el `curl` para reproducirlo. Si es un 500, mirar la traza en `log-contrato.txt`.
3. **api rojo:** abrir `diagnostico/diagnostico.html`. Ahí está la prueba, lo que esperaba, lo que recibió y los requests con su código. Para ver cada petición con su cuerpo, la traza del reporte HTML de Playwright.
4. **web rojo (solo corre si pasaron verificar, contrato y api):** abrir `reporte-bdd.html` del navegador que falló, ir al paso en rojo y ver su captura y la consola. Si falla solo en uno de los dos navegadores, es de ese navegador; si falla en los dos, es de la app o del escenario.
5. **Defecto conocido que «pasa»:** el job falla a propósito («se esperaba que fallara y pasó»): alguien corrigió un defecto y hay que quitar su etiqueta `@fail` o `@defecto`.

## 2. Qué es un fallo esperado en el reporte

Los escenarios `@DEF-NN @fail` (API) y `@defecto` (web, xfail estricto) describen el comportamiento **correcto** y fallan mientras el defecto exista. Por eso el reporte los muestra aparte, como «fallo esperado (defecto)», y el diagnóstico les adjunta la evidencia: qué esperaba la prueba, qué respondió la app y qué requests lo provocaron. Es la evidencia que va en cada `DEF-NN` de [`defectos.md`](defectos.md).

## 3. Mapa de logs: cuáles mapeamos y cuáles no

«Mapear» es llevar un log a algo que se cruza con los resultados: una prueba, una operación del OpenAPI o una métrica.

| Log | Lo produce | Cómo se saca | ¿Lo mapeamos? | Para qué se cruza, o por qué no |
|---|---|---|---|---|
| **Log de la app durante la API** (accesos de uvicorn con método, ruta y código, y trazas de Python de los 500) | uvicorn (herramienta) | El job lo redirige: `uvicorn … > reportes/log-api.txt`. Artefacto `api` | **Sí, nosotros** | `cobertura_contrato.py`: qué códigos provocó cada suite por operación. `diagnostico.py`: cada prueba con sus requests. Se une prueba ↔ log porque cada escenario empieza con `POST /api/pruebas/reiniciar`: el tramo N del log es el intento N (ordenado por hora de inicio). Solo se acepta si los conteos coinciden (263 = 263) |
| **Log de la app durante el contrato** | uvicorn | `… > reportes/schemathesis/log-contrato.txt` | **Sí, nosotros** | Lo que probó Schemathesis por operación, para compararlo con lo que probamos nosotros |
| **Hallazgos de Schemathesis** (consola, JUnit, HTML, `curl` de reproducción) | Schemathesis (herramienta) | `st run … --report junit,html` (`scripts/contrato.sh`) | **Sí, nosotros** | Se llevan a su operación del OpenAPI y se cruzan con lo que ya probaban los escenarios: una brecha es un caso que nos falta |
| **Cassette o HAR de Schemathesis** (cada request y respuesta) | Schemathesis (opcional) | `--report har` o `vcr` | No | Pesaría megas por cada pasada de 20 ejemplos por operación y repite lo que ya tenemos: el `curl` en el JUnit y el log de la app con el código de cada request. Se activa si hay que depurar un hallazgo puntual |
| **Resultados de Playwright** (lista, JSON, JUnit, HTML) | Playwright | `reporter` en `playwright.config.ts` | **Sí, nosotros** | El JSON alimenta la matriz de trazabilidad, el resumen del job y el diagnóstico; el JUnit va a Qase |
| **Traza de Playwright** (cada petición, su cuerpo y respuesta) | Playwright | `EVIDENCIA=con` (todas) o `fallos` (las que fallan), dentro del reporte HTML | No (la lee una persona) | Es el detalle fino para depurar un caso; el diagnóstico ya resume los requests y los códigos |
| **Salida de depuración de Playwright** (`DEBUG=pw:api`) | Playwright | Variable de entorno `DEBUG` | No | Describe la herramienta, no la app: ruido salvo que falle Playwright |
| **Resultados de Selenium** (JUnit, pytest-html) | pytest | `--junitxml`, `--html` | **Sí, nosotros** | El JUnit alimenta la trazabilidad por navegador, el resumen del job y Qase |
| **Reporte BDD por paso** (estado, captura, error, traza de nuestro código) | **Nosotros** (`tests/e2e/soporte/reporte.py`) | Hooks de `pytest-bdd` en `conftest.py`; `--evidencia con/fallos/sin` | **Sí, nosotros** | Es el camino al fallo en la web: el paso exacto con su captura |
| **Consola del navegador y errores de JavaScript** | El navegador, vía WebDriver BiDi (Selenium) | `driver.script.add_console_message_handler` (`soporte/bidi.py`) | **Sí, nosotros**, donde el navegador implementa BiDi (`soporta_bidi`) | Va dentro del escenario en el reporte BDD: distingue un error de la app de un error de la prueba |
| **Red del navegador** (todas las peticiones) | El navegador, vía BiDi | `driver.network` | No, salvo para simular errores | Tiene cientos de peticiones de estáticos por pantalla; lo que importa de la red está en el log del servidor y en la captura. Se usa solo para provocar un 503 y probar el mensaje de error |
| **Log del driver** (chromedriver, geckodriver) | Los drivers | `log_output` del servicio de Selenium | No | Solo sirve cuando falla el driver (`session not created`) y ahí el error ya llega a la salida del job |
| **Salida, serie de tiempo y tablero de k6** | k6 (herramienta) | `--out csv`, `--summary-export`, `K6_WEB_DASHBOARD_EXPORT` (`correr.sh`) | **Sí, nosotros** | `graficos.py` los convierte en gráficos por prueba y `resumen.md` compara cada umbral |
| **CPU, memoria e hilos** de Qolqe y de k6 | **Nosotros** (`monitor.py`, psutil, cada segundo) | `correr.sh` lo lanza dentro del contenedor y fuera | **Sí, nosotros** | Se cruza con los tiempos de k6 para ver que el cuello de botella no es el CPU y que los hilos pasan de 17 a 51 cuando el p95 salta de 50 ms a 60 s |
| **Log de Qolqe durante la carga** | uvicorn (en Docker) | `docker logs qolqe-perf \| gzip > log_qolqe.txt.gz` | **Sí, nosotros** | De ahí sale la causa del colapso: 3878 `database is locked` y los 500 a los 10.5 s del `busy_timeout` |
| **Integridad del dinero** | **Nosotros** (`verificar_dinero.py`) | Antes y después de cada prueba | **Sí, nosotros** | Cruza la BD con las respuestas de k6: saldos contra movimientos, operaciones en BD = 201 de k6 |
| **Estadísticas de Docker** (`docker stats`) | Docker | `docker stats` | No | Da CPU y memoria del contenedor, que `monitor.py` ya mide desde adentro y con hilos |
| **Logs de GitHub Actions** | GitHub | Pestaña del job, `gh run view --log` | **Parcial** | Caducan (90 días por defecto): por eso lo importante se sube como artefacto, se resume en la página de la corrida y se publica en Pages |
| **Historial de ejecuciones por caso** | Qase | `qasectl` desde el job `reportes` | **Sí, nosotros** | Cada caso acumula su historial de corridas; Pages guarda además las últimas 30 de `main` |

### Por qué no mapeamos todo

Un log se mapea cuando (1) lo podemos unir con algo que ya identificamos (una prueba, una operación, un umbral), (2) esa unión se puede **validar** y (3) responde una pregunta que el reporte por defecto no responde. Lo que no cumple eso queda disponible como artefacto o como opción (`EVIDENCIA=con`, cassettes, log del driver) para depurar un caso puntual, sin cargar cada corrida con megas de ruido. La unión prueba ↔ log de la API cumple las tres: se comprobó que el 500 de `CP-32` (DEF-09, registros simultáneos) y las transferencias simultáneas de `CP-53` y `CP-86` (DEF-11) caen en el tramo de su prueba. La de Selenium no está validada y por eso no se afirma.

## 4. Cómo sacarlos, en local

```bash
npm run diagnostico                      # API con log guardado y reportes/diagnostico/diagnostico.html
EVIDENCIA=con npm test                   # trazas de Playwright en el reporte HTML
npm run contrato                         # reportes/schemathesis/{gate,hallazgos}
scripts/selenium.sh todo --evidencia con # reporte BDD con captura de cada paso
tests/performance/correr.sh carga        # resultados/<prueba>/ con series, recursos, log y gráficos
```
