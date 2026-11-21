# Informe del proyecto – Grupo 5 · Límites

## 1. Datos generales y alcance

| Campo | Valor |
|---|---|
| Integrantes | Kalos · Gianpier |
| Módulo | G5 · Límites y alertas de consumo |
| Herramienta de API | Playwright (API testing) + playwright-bdd |
| Herramienta de contrato | Schemathesis 4.31 |
| Herramienta web | Selenium 4 + pytest-bdd, con Page Object |
| Herramienta de rendimiento | Grafana k6 v2.3 |
| CI/CD | GitHub Actions, reportes en GitHub Pages |
| Gestión de casos | Qase (plan gratis), con una corrida por pipeline de `main` |
| Capacidad de IA | Claude (Claude Code): skills `proponer-casos` y `reporte-defecto`, con el checklist «La IA propone, el tester decide» (sección 7 y [`IA.md`](../IA.md)) |

**Alcance y nivel de prueba**

| HU | Prioridad | Nivel | Justificación |
|---|---|---|---|
| HU-N-01 a HU-N-09 (núcleo) | Alta / Media | API (+ web en HU-N-01, 02, 07, 08 y 09) | Reglas de dinero, credenciales y sesión: observables en la API; la concurrencia de HU-N-07 CA5 va a rendimiento. En la web van los flujos de registro, ingreso y transferencia: el mensaje que ve el usuario, el diálogo de confirmación y el comprobante |
| HU-G5-01 Ver mis límites | Media | API | El cálculo de usado/disponible se verifica en el JSON |
| HU-G5-02 Cambiar límite diario | Alta | API | Rango, múltiplos y vigencia a 24 h; requiere controlar el reloj (`/api/pruebas/reloj`) |
| HU-G5-03 Respetar el límite al transferir | Alta | API (+ rendimiento para CA2) | Afecta dinero; la concurrencia se prueba en la Parte 3 |
| HU-G5-04 Crear alerta | Media | API | Particiones y valores límite del umbral |
| HU-G5-05 Ver alertas | Baja | API (+ web en Parte 2) | Gasto de hoy por tipo, verificable en JSON |
| HU-G5-06 Editar/pausar/reanudar | Media | API (+ web) | Regla de reanudación frente al límite |
| HU-G5-07 Eliminar alerta | Baja | API (+ web) | Una alerta eliminada deja de notificar |
| HU-G5-08 Notificación de alerta | Alta | API | Actor Sistema; se observa en `/api/pruebas/notificaciones` |

Criterios: prioridad (riesgo), si la regla es observable en la API sin UI y si requiere control del reloj o de los datos.

**Por qué estas herramientas y cómo se complementan.** Cada una responde una pregunta distinta y deja un hueco que cubre otra; ninguna repite el trabajo de otra:

| Herramienta | Pregunta que responde | Cómo prueba | Lo que no ve, y quién lo cubre |
|---|---|---|---|
| Playwright + playwright-bdd (API) | ¿Se cumple cada regla de negocio de cada HU? | Casos diseñados por nosotros (particiones, valores límite, reloj controlado), con el requisito como oráculo | Entradas que no se nos ocurrieron → Schemathesis. La pantalla → Selenium. Tiempos con muchos usuarios → k6 |
| Schemathesis (contrato) | ¿La API cumple lo que declara su OpenAPI, con cualquier entrada? | Genera cientos de peticiones a partir del esquema (pruebas basadas en propiedades) | No conoce las reglas de negocio (no sabe que el límite va de 100 a 2000) → Playwright |
| Selenium + pytest-bdd (web) | ¿El usuario puede hacerlo en la pantalla, en Chrome y en Firefox? | Navegador real por el estándar W3C WebDriver; datos y sesión preparados por API | Las reglas finas: un caso por interfaz tarda y se rompe más que por API (en la Parte 2, 19 casos web tardaron de 1 a 2 minutos por navegador), así que en la web van los flujos y lo que es propio de la pantalla → Playwright |
| k6 (rendimiento) | ¿Responde a tiempo con 100 y 300 usuarios, y dónde se rompe? | Usuarios virtuales con el modelo de carga del requerimiento | No revisa funcionalidad → Playwright; detecta, eso sí, reglas que se rompen bajo concurrencia (DEF-11) |
| GitHub Actions + Pages | ¿Se corrió todo, en cada cambio, y qué pasó? | Pipeline por etapas con quality gates; reportes y trazabilidad publicados | — |

El costo de combinarlas es mantener dos lenguajes (TypeScript para API y Python para web). Lo compensa que las dos suites leen el mismo formato (Gherkin con las mismas etiquetas `@HU`, `@CP`, `@CA` y `@DEF`), así la trazabilidad es una sola. Selenium nos tocó por sorteo para la web; Playwright lo elegimos para API porque su cliente `request` prueba la API sin abrir un navegador, levanta la app sola (`webServer`) y su traza guarda cada petición y respuesta como evidencia.

**Cobertura de Gherkin:** 5 archivos `.feature` (`limites`, `nucleo_registro`, `nucleo_sesion`, `nucleo_cuenta`, `nucleo_transferencias`), con todas las HU del núcleo y del módulo. Para la web hay 4 archivos más en `features/ui/` (`limites_ui`, `dos_usuarios_ui`, `nucleo_ui` y `defectos_ui`) con 29 escenarios (42 pruebas con sus ejemplos y el caso de Screenplay), entre ellos los del núcleo común (registro, ingreso y transferencia), que son parte de las pruebas web exigidas en la entrega final. Cada escenario lleva su HU, su caso, su nivel y los criterios que cubre (`@HU-G5-02 @api @CP-02 @CA-G5-02-1`). Los 48 criterios del núcleo y de G5 tienen al menos un caso de API, y la etapa `verificar` del pipeline falla si alguno se queda sin caso.

**Casos funcionales y técnicos:** los funcionales verifican las reglas de negocio (R-G5-01 a R-G5-05, RN-01 a RN-09) con particiones y valores límite. Los técnicos (`@tecnico`) verifican la interfaz de cada HU del núcleo y del módulo: autenticación (sin token, con un token inválido o vencido → 401 `NO_AUTENTICADO`), cuerpo vacío, campo faltante o tipo inválido (422 `SOLICITUD_INVALIDA` que indica el campo), ausencia de efecto tras un rechazo (el saldo, el límite o el perfil no cambian y no se envía el SMS) y propiedad de los datos (la alerta o el contacto de otro usuario responden 404 y no se modifican; el gasto de otro usuario no consume mi límite ni dispara mis alertas). Registro e inicio de sesión son públicos, así que ahí no aplica el 401. Hay 92 casos funcionales y 39 técnicos; la matriz por criterio está en [`trazabilidad.md`](trazabilidad.md).

## 2. Pruebas de API

**Herramienta:** Playwright Test (cliente `request` / `APIRequestContext`) + playwright-bdd. Los escenarios de `features/*.feature` se enlazan con pasos en TypeScript (`tests/api/pasos.ts`, `pasos_nucleo.ts`); `bddgen` los convierte en specs de Playwright.

**Enfoque:** BDD. El `.feature` es el caso de prueba legible por negocio; cada paso es una función que llama a la API. La API de soporte (`/api/pruebas/*`) reinicia la semilla antes de cada escenario, fija el reloj y expone los SMS.

**Instalación y ejecución**
```bash
python -m venv .venv && source .venv/bin/activate && pip install -r requirements-pruebas.txt
npm install
npm test                                   # bddgen + playwright test (levanta uvicorn solo)
npx playwright test --grep @HU-G5-02       # solo una HU
npx playwright test --grep @DEF            # solo los escenarios que detectan defectos
npm run report                             # reporte HTML
```

**Defectos conocidos:** los escenarios con `@DEF-xx @fail` usan `test.fail()`: pasan mientras el defecto exista y se ponen en rojo cuando lo corrijan (aviso para retirar la etiqueta).

**Ventajas:** API y web con el mismo runner; levanta la app con `webServer`; trazas y reporte HTML y JUnit; TypeScript con autocompletado.
**Limitaciones:** los escenarios comparten BD y reloj, así que corren en serie (`workers: 1`); playwright-bdd agrega un paso de generación (`bddgen`); no valida contratos OpenAPI (para eso Schemathesis); requiere Node además de Python.
**Capacidades de IA:** test agents Planner, Generator y Healer (`npx playwright init-agents`, desde v1.56); servidor MCP `@playwright/mcp`; depurador y análisis de trazas por CLI (v1.59). Riesgo: el Healer puede "arreglar" una aserción que en realidad detecta un defecto; el oráculo sigue siendo el requisito.

**Resultados:** 108 escenarios (8 técnicos): 97 pasan, 10 fallan como se espera porque detectan 9 defectos (DEF-06 tiene dos escenarios) y 1 quedaba para la Parte 3 (`@rendimiento`). En la Parte 3 ese escenario se activó (CP-53) junto con CP-86 y los dos detectan DEF-11; la suite de la entrega final tiene 263 pruebas (133 casos con sus ejemplos) y todas pasan, contando los 16 fallos esperados. Los 3 últimos son de DEF-13 (redondeo de la comisión), hallado en la entrega final con la skill de IA `proponer-casos` (sección 7). Tras la retroalimentación de la Parte 2 se agregaron 58 casos (CP-87 a CP-144) para cubrir cada criterio con casos funcionales y técnicos; uno de ellos encontró DEF-12.

**Contrato (Schemathesis 4.31)** — `npm run contrato` (`scripts/contrato.sh`): reinicia la semilla, usa el usuario de carga 900000001 y excluye el cierre de cuenta para no romper el token.

| Hallazgo de Schemathesis | Lectura |
|---|---|
| 500 en `POST /api/usuarios` (fase stateful) | Defecto real → **DEF-09** |
| "API rejected schema-compliant request" (8–10) | Reglas de negocio que el esquema no declara (múltiplos de 50, saldo, duplicados). Recomendación: documentar `multipleOf`, mínimos y máximos en el OpenAPI |
| "API accepted schema-violating request" (2) | `cci` con tipo incorrecto se ignora en transferencias QOLQE; `pin` fuera de patrón se procesa en login. Baja severidad |
| "Invalid Allow header" (4) | Respuestas 405 a `OPTIONS` sin cabecera `Allow`. Baja severidad |

Evidencia: `docs/evidencia/schemathesis/` (reporte HTML, JUnit y salida de la corrida del 17-oct, con la lectura de cada hallazgo en `docs/evidencia/README.md`) y `docs/evidencia/schemathesis-2026-10-16/` (corrida anterior). Cada corrida nueva queda en `reportes/schemathesis/`. El reporte de Playwright está en `docs/evidencia/playwright/`.

## 3. Pruebas web y CI/CD

**Herramienta:** Selenium 4 + pytest-bdd (Python). Los escenarios de `features/ui/*.feature` (Gherkin en español) se enlazan con pasos en `tests/e2e/test_limites_ui.py`. Corre en Chrome, Firefox, Edge y Safari reales por el estándar W3C WebDriver, en local o en Selenium Grid 4 (Docker), y con WebDriver BiDi escucha la consola y la red del navegador. Los datos y la sesión se preparan por API, no por la pantalla.

**Ventajas:** estándar W3C mantenido por los fabricantes de navegadores; Safari real; Grid para correr en paralelo o en remoto; Python, el mismo lenguaje de la app y de su API de soporte. **Limitaciones:** más código propio que Playwright (esperas, reportes, capturas); un driver por navegador (Selenium Manager los descarga); más lento que probar por API. **IA:** reparación de localizadores rotos con un modelo de lenguaje (`scripts/selenium.sh ia`), que deja cada reparación en `reportes/selenium/sanaciones.json` para que una persona la revise y corrija el Page Object.

### Patrón de diseño: Page Object para las pantallas, Screenplay para varios usuarios

**El problema.** La pantalla de límites cambia (textos, `data-testid`, orden de campos), la suite la mantienen dos personas y los pasos de Gherkin tienen que leerse como la historia de usuario. Elegimos el patrón con seis criterios: (1) un cambio de interfaz se corrige en un solo lugar; (2) los pasos hablan el idioma del negocio; (3) poco código extra para el tamaño de la suite (16 escenarios en 4 pantallas); (4) que los dos podamos explicarlo y mantenerlo; (5) expresar escenarios con varios usuarios a la vez, porque en Qolqe el dinero pasa de un usuario a otro y la Parte 3 trata justamente de usuarios simultáneos; (6) escalabilidad: que la suite pueda crecer en pantallas, escenarios y usuarios sin que el costo de mantenerla crezca al mismo ritmo.

| Opción | (1) Un cambio, un lugar | (2) Pasos de negocio | (3) Código extra | (4) Mantenerlo entre dos | (5) Varios usuarios | (6) Escalabilidad | Decisión |
|---|---|---|---|---|---|---|---|
| Script lineal, sin patrón | no: el mismo localizador se repite en cada paso que lo usa | no: los pasos se llenan de `find_element` | ninguno | fácil al inicio, frágil después | no | **no**: cada escenario nuevo copia localizadores; el costo de mantenimiento crece con escenarios × pantallas | descartado |
| **Page Object** | **sí: cada localizador vive en su página** | **sí: `cambiar_limite(500)`** | **una clase por pantalla y una base** | **sí** | no: la página no sabe quién la usa | **sí**: una pantalla nueva es una clase y los escenarios nuevos reutilizan sus métodos. Límite: una pantalla grande engorda su clase (se separa un Component Object, como el menú) | **elegido para las pantallas** |
| **Screenplay** | sí, porque usa las páginas por dentro | **sí, aún más: «Ana le transfiere a Bruno»** | alto: actores, tareas y preguntas | más conceptos que aprender | **sí: cada actor con su navegador y su sesión** | **sí en usuarios**: otro actor es otra sesión, sin tocar las páginas. En escenarios de un solo usuario cada tarea es una clase de más y no se justifica | **elegido para los flujos entre usuarios** |
| Page Factory | sí | sí | — | — | — | — | no existe en Python (`@FindBy` es de Java) |

**La evidencia de que cumple.** Los 34 localizadores están en `pages/limites_page.py` (17), `transferir_page.py` (10), `login_page.py` (4) e `inicio_page.py` (3); de los 37 pasos, ninguno busca un elemento por su cuenta (solo uno lee el texto completo de la página para verificar un mensaje). `scripts/selenium.sh romper` cambia a propósito un localizador y el flujo feliz falla; arreglarlo es una línea en `limites_page.py` y los 15 escenarios vuelven a pasar. Screenplay, en `tests/e2e/screenplay/`, resuelve lo que Page Object no: **quién** hace cada cosa. En CP-145 (`features/ui/dos_usuarios_ui.feature`) Ana y Bruno ingresan cada uno en su propio navegador, con su propia sesión; Ana le transfiere S/ 50 a Bruno, y Bruno ve el dinero en su saldo y en sus movimientos. El escenario se lee igual que el código: `ana.intenta(Transferir.a("Bruno").por(50))` y `bruno.ve(SaldoDisponible("S/ 850.00"))`. Pasa en Chrome y en Firefox. Las tareas usan las páginas por dentro (`TransferirPage`, `InicioPage`), así que no se duplica ningún localizador: Page Object responde «dónde está cada botón» y Screenplay, «quién hace qué».

**La evidencia de que escala.** Entre la Parte 2 y la entrega final la suite web pasó de 20 a 42 pruebas (de 14 a 29 escenarios Gherkin; los esquemas con ejemplos hacen que 29 escenarios sean 41 pruebas, más 1 prueba de Screenplay) al sumar el núcleo común: ingreso, registro y transferencia. El costo fue una página nueva (`registro_page.py`, 29 líneas), métodos nuevos en `login_page.py` y `transferir_page.py` y 16 pasos. **Ningún localizador ni paso existente cambió** y las 20 pruebas anteriores siguen igual. 8 de los 15 escenarios nuevos se escribieron solo en Gherkin, con pasos que ya existían. El patrón también aguantó un cambio en el medio: `transferir_page.py` separó «pedir» de «confirmar» para poder leer el diálogo de confirmación, y el resto de la suite no lo notó porque `transferir()` conserva su firma. **Lo que no escala:** los escenarios comparten una BD y un reloj, así que no corren en paralelo; Selenium Grid reparte por navegador, no por escenario. Si la suite pasara de unos 100 escenarios, habría que dar una BD a cada worker. Antes, 19 casos tardaban de 1 a 2 minutos por navegador; con 42 pruebas falta medir el tiempo en la corrida local. El pipeline las corre en Chrome y en Firefox en paralelo.

Junto a Page Object usamos Component Object (el menú, que aparece en varias páginas), una clase base con las esperas explícitas (`WebDriverWait`, nunca `sleep`), una fábrica de navegadores (local, Grid, móvil) y una fachada de la API para preparar datos. Localizadores: `data-testid` en todos los elementos propios de la pantalla y el texto del enlace en el menú; ningún XPath.

### Pipeline y quality gates

`.github/workflows/pruebas.yml`, por etapas: si una etapa barata falla, las largas no corren.

| Etapa | Jobs | Gate |
|---|---|---|
| 1 · en paralelo | `verificar`, `contrato`, `api` | **verificar:** trazabilidad completa (cada escenario con HU, CP y criterio; cada criterio del núcleo y G5 con caso; cada fallo esperado con su DEF) y Gherkin que compila. **contrato:** sin 500 y respuestas como dice el OpenAPI. **api:** 0 failed; un fallo esperado solo puede fallar por su defecto y, si pasa, el job falla; 0 flaky; 0 `test.only` |
| 2 · en paralelo | `web (chrome)`, `web (firefox)` | Lo mismo con `@defecto`, en los dos navegadores. Solo corren si pasó toda la etapa 1 |
| 3 | `reportes` | Publica portada, trazabilidad con historial, cobertura del contrato y el diagnóstico por prueba en Pages |

Cambios respecto de la Parte 2, por la retroalimentación: el contrato pasó de correr después de la API a correr en la primera etapa, como gate, y la API corre en esa misma etapa, junto al contrato, porque los dos prueban la misma API desde ángulos distintos; el gate del contrato separa lo que bloquea (la API no cumple su propio contrato) de los hallazgos ya analizados, que se reportan sin bloquear, así el job ya no sale en rojo en cada corrida; la web, en Chrome y Firefox a la vez, espera a que pase toda la primera etapa, porque Selenium prepara sus datos y su sesión por la API del producto y un escenario web que falla con la API rota no dice nada (cuesta unos dos minutos más por corrida y se gana un diagnóstico más claro); el pipeline no corre al subir un tag (antes corría dos veces por entrega) ni con cambios solo de documentación; y cada job tiene un tiempo máximo. La tabla completa de gates, con umbrales, está en [`pruebas.md`](pruebas.md#quality-gates).

**Evidencia con o sin capturas.** Al lanzar el pipeline a mano se elige `con` (una captura por paso en la web y la traza de cada petición en la API), `fallos` (solo lo que falla; es lo que usa cada push) o `sin` (reporte liviano). En local: `EVIDENCIA=con npm test` o `scripts/selenium.sh todo --evidencia sin`.

**Reportería a detalle.** Cada herramienta trae un reporte por defecto que dice qué prueba falló; agregamos lo que falta para ver por qué y cruzamos los logs de la app con los resultados. En la API, `diagnostico.py` une cada prueba que no pasó limpia con su tramo del log de uvicorn (cada escenario empieza con un reinicio de datos, así que el tramo N del log es el intento N) y muestra lo que esperaba, los requests que hizo con su código y la traza de Python si hubo un 500; la unión se validó con DEF-09 (los tres 500 caen en `CP-32`) y DEF-11 (las transferencias simultáneas caen en `CP-53` y `CP-86`). En la web, el reporte BDD enseña cada paso con su captura, el error, la traza de nuestro código y la consola del navegador (WebDriver BiDi). En el contrato, cada hallazgo trae el `curl` que lo reproduce y se cruza con lo que probaron nuestros escenarios. En rendimiento se guardan series de tiempo, recursos, el log de la app y la revisión del dinero. El mapa de qué log mapeamos, cuál no y por qué, y la ruta para llegar al fallo desde un job en rojo, está en [`reporteria.md`](reporteria.md).

### Trazabilidad entre corridas y gestión de casos

Cada escenario lleva `@CP-NN`, sus `@HU` y sus criterios (`@CA-N-07-3` = HU-N-07 CA3). La matriz que publica el pipeline muestra la cobertura por historia (casos funcionales y técnicos), la cobertura por criterio y, por cada caso, el resultado de esta corrida y el de las últimas 30 corridas de `main` (`passed 30`, o `passed 28 · failed 2 · último fallo run #45`). Así se ve desde cuándo falla un caso, si un defecto se corrigió y qué casos son inestables, no solo el último resultado.

**Gestión de casos.** Comparamos 14 herramientas (Qase, Testomat.io, BrowserStack, Kiwi TCMS, TestLink, Xray, Zephyr, TestRail, Testmo, Allure TestOps y otras) con cinco criterios: gratis sin vencimiento, resultados desde GitHub Actions, historial por caso, defectos ligados al resultado y acceso para la profesora. Elegimos **Qase** (plan gratis): es la única que cumple los cinco. El job `reportes` crea una corrida de Qase por pipeline de `main` y sube los JUnit de API, contrato y web con `qasectl`; cada escenario acumula su historial y desde un resultado fallido se registra el defecto. Comparación, límites asumidos y cómo activarlo en [`gestion-casos.md`](gestion-casos.md).

**Resultados web:** en la Parte 2, 17 passed y 3 xfailed en Chrome y en Firefox. Con el núcleo común hay 42 pruebas: 37 que deben pasar y 5 xfailed (los 3 defectos de límites más DEF-05 y DEF-13 vistos desde la pantalla). Las 22 pruebas nuevas se comprobaron el 20-nov-2026 con un segundo conductor del navegador (Playwright sobre Chromium, contra la misma app y los mismos datos): las 20 que deben pasar mostraron exactamente los textos y valores de los escenarios, y las 2 de defecto (DEF-05 y DEF-13) fallaron como se espera. Los pasos en Python con Selenium se recolectan sin error con pytest; su corrida real la hace el pipeline en Chrome y Firefox. Reportes: `reportes/selenium/reporte-bdd.html` y el sitio en [kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/).

## 4. Pruebas de rendimiento

**Herramienta:** Grafana k6 v2.3. Cada umbral del requerimiento se escribe tal cual en el script (`'http_req_duration{tipo:consulta}': ['p(95)<800']`) y k6 dice si pasó; corre fuera de Qolqe con poco consumo (4 % de un núcleo con 2000 VUs) y usa JavaScript, como las pruebas de API en TypeScript. Se comparó con JMeter, Gatling, Locust y Artillery (informe de rendimiento, sección 2).

**Entorno:** Qolqe en Docker con `--cpus=1 --memory=1g` (uvicorn con un proceso, SQLite en WAL) y k6 nativo en la misma laptop (MacBook Pro M5, 16 GB). CPU, memoria e hilos de Qolqe y de k6 se miden cada segundo con `tests/performance/monitor.py` (psutil). Es una línea base relativa, no la capacidad de producción.

### Modelo de carga: de qué sale cada valor

**Qué hace un usuario virtual (VU).** Un VU es un cliente de Qolqe con sesión abierta. Cada iteración es una sesión completa: inicia sesión y hace 6 operaciones, esperando antes de cada una (`tests/performance/sesion.js`). Cada operación se sortea con los porcentajes del requerimiento (saldo y perfil 30 %, movimientos 15 %, transferir 15 %, contactos 10 %, recargar 10 %, deudas 6 %, pagar 4 %, otras 10 %). Cada VU usa siempre a su propio usuario, con saldo, deudas y contactos propios (`tests/performance/datos/preparar_datos.py`), así ninguna regla de negocio se dispara por compartir datos.

| Parámetro | Valor | De dónde sale | Cálculo |
|---|---|---|---|
| Usuarios a la vez en hora punta | **100 VUs** | «Unas 3000 sesiones por hora, de 2 minutos cada una» | Ley de Little: usuarios a la vez = llegadas × duración = (3000 / 3600 s) × 120 s = 100 |
| Usuarios a la vez en la campaña | **300 VUs** | «El triple de usuarios simultáneos que en hora punta» | 3 × 100 |
| Operaciones por sesión | **6** y un login | «Cada sesión: iniciar sesión y 6 operaciones» | Da 7.24 peticiones por sesión contando la consulta previa a cada pago |
| Think time | **10 a 25 s, promedio 18 s** | «Entre operaciones, una pausa de 10 a 25 s (18 s en promedio)» | Distribución triangular 10-19-25: (10 + 19 + 25) / 3 = 18 |
| Ramp-up de la hora punta | **120 s** (0 → 100) | Una sesión dura 120 s | Ver abajo |
| Ramp-up de la campaña | **300 s** (100 → 300) | «La mayoría inicia sesión en los primeros 5 minutos» | Dato del requerimiento |
| Ramp-up del estrés | **60 s** por escalón, 180 s sostenidos | Medir cada escalón en régimen | Ver abajo |
| Duración de la hora punta | **20 min** estables | «Unas 3000 sesiones por hora» no dice cuánto probar | 20 min dan unas 1000 sesiones y 7000 peticiones: suficientes para un p95 estable por tipo. La hora completa va en resistencia |

**Por qué ese think time.** (1) Es un dato del requerimiento: el rango y el promedio vienen dados; no lo elegimos. (2) Es lo que convierte 100 VUs en la hora punta real. Cada VU hace 7.24 peticiones en una sesión que dura poco menos de 2 min (6 pausas × 18 s = 108 s, más los tiempos de respuesta), es decir, unas 0.065 peticiones por segundo; con 100 VUs son unas 6.5 peticiones por segundo y medimos 6.7. Con una pausa de 5 s serían unas 22 por segundo, 3.4 veces la hora punta real, y la prueba ya no respondería la pregunta del negocio. (3) Se sortea en un rango en lugar de usar 18 s fijos para que los usuarios no queden sincronizados (todos pidiendo en el mismo segundo, como un reloj), cosa que no pasa con personas reales. La distribución triangular respeta el rango y el promedio exactos. (4) No sumamos los 12 s que faltan para los 2 min de la sesión: así cada VU hace un 10 % más de sesiones de las necesarias (unas 3300 por hora). La prueba queda del lado exigente, y por eso el throughput medido (55.4 sesiones por minuto) supera al mínimo de 50.

**Por qué ese ramp-up.** *Hora punta, 120 s:* con la ley de Little, el sistema llega a régimen cuando los primeros usuarios terminan su primera sesión, es decir, a los 120 s. Subir más rápido llenaría la meseta de logins simultáneos que no existen en la hora punta, que es una carga estable. Por eso la subida y la bajada no cuentan en las cifras: se mide solo la meseta. *Campaña, 300 s:* es el dato del requerimiento (la mayoría entra en los primeros 5 minutos). Antes hay 4 min de hora punta para comparar y 4 min después para ver si se recupera. *Estrés, 60 s por escalón y 180 s sostenidos:* la subida de 60 s evita medir el golpe de entrada de los usuarios nuevos, y 180 s son más de una sesión (120 s), así que cada escalón se mide ya en régimen. Los escalones (100, 300, 600, 800, 1000, 1200, 1400) salen de un sondeo previo: una subida continua de 0 a 2000 usuarios que se quebró entre 1000 y 1100, y se midió con más detalle alrededor.

Entorno y medición: Qolqe y k6 en la misma laptop, Qolqe con 1 CPU y 1 GB; el detalle está en el informe de rendimiento.

**Cómo se corre:** `tests/performance/correr.sh <prueba>` levanta Qolqe limpio, prepara los datos, mide los recursos, corre k6 y al final verifica el dinero (`verificar_dinero.py`: saldos contra movimientos, cada transferencia con su salida y su entrada, ninguna deuda pagada dos veces y operaciones en la BD = respuestas 201 de k6) y genera los gráficos. Todo queda en `tests/performance/resultados/<prueba>/`.

| Prueba | VUs | p95 consultas | p95 dinero | Errores | Throughput | Dinero | Veredicto |
|---|---|---|---|---|---|---|---|
| Carga (hora punta, 20 min) | 100 | 51 ms | 126 ms | 0 % | 55 sesiones/min | cuadra | Cumple |
| Pico (campaña) | 100 → 300 → 100 | 48 ms | 127 ms | 0 % | 166 sesiones/min | cuadra | Cumple, sin degradación |
| Estrés (escalones) | 600 | 51 ms | 126 ms | 0 % | 315 sesiones/min | — | Cumple |
| Estrés (escalones) | 800 | 60 s | 60 s | 86 % | 45 sesiones/min | 6 operaciones sin confirmar | Colapsa (DEF-10) |
| Resistencia (60 min) | 100 | 42 ms | 126 ms | 0 % | 56 sesiones/min | cuadra | Cumple; memoria +5.5 MB/h |
| Concurrencia (misma cuenta) | 1 | — | — | — | — | límite y saldo superados en 5 de 5 rondas | Falla (DEF-11) |

### Resultados frente a los umbrales

Un «cumple» no basta: hay que decir por cuánto, por qué es creíble y qué no dice. Los umbrales salen del requerimiento («el 95 % debe responder en menos de 800 ms», «en menos de 1.5 segundos», «no más del 1 % puede fallar», «sostener el volumen de la hora punta sin acumular retrasos»); para la campaña, «degradación razonable» no trae número y asumimos hasta el doble.

| Prueba | Métrica | Umbral | Resultado | Margen | Veredicto |
|---|---|---|---|---|---|
| Carga · 100 VUs | p95 consultas y login | < 800 ms | 51 ms (login 56 ms) | 15.7 veces mejor | Cumple |
| Carga · 100 VUs | p95 dinero | < 1500 ms | 126 ms | 11.9 veces mejor | Cumple |
| Carga · 100 VUs | Errores | < 1 % | 0.00 % | — | Cumple |
| Carga · 100 VUs | Throughput | ≥ 50 sesiones/min | 55.4 sesiones/min | 11 % más | Cumple |
| Pico · 300 VUs | p95 consultas y login | < 1600 ms (supuesto: el doble) | 48 ms (login 56 ms) | 33 veces mejor | Cumple |
| Pico · 300 VUs | p95 dinero | < 3000 ms (supuesto) | 127 ms | 23.6 veces mejor | Cumple |
| Pico · 300 VUs | Throughput | ≥ 150 sesiones/min (3 × 50) | 165.8 sesiones/min | 10.5 % más | Cumple |
| Resistencia · 60 min | p95 consultas / dinero | < 800 / < 1500 ms | 42 / 126 ms | 19 y 12 veces mejor | Cumple |
| Estrés · 600 VUs | Los tres umbrales de hora punta | — | 51 ms / 126 ms / 0 % | — | Cumple |
| Estrés · 800 VUs | Los tres umbrales de hora punta | — | 60 s / 60 s / 86 % | — | No cumple (DEF-10) |

**Por qué son creíbles.** (1) *Sin cola:* con 100 VUs el CPU de Qolqe promedia 8 %, así que el tiempo de respuesta es casi el tiempo de servicio; por eso los tiempos con 100 y con 300 VUs son iguales (48 contra 51 ms). (2) *Estables:* en las cuatro ventanas de 5 minutos de la meseta el p95 de consultas queda entre 51 y 52 ms y el de dinero entre 123 y 127 ms, así que no se acumulan retrasos. (3) *Sin efecto de la carga:* la mediana con 1 VU es la misma que con 100 (login 52 contra 49 ms, transferir 91 contra 93 ms). (4) *Explicables:* el p95 de dinero de 126 ms es casi todo la pausa de 40 a 120 ms que el antifraude simulado agrega a las transferencias. (5) *El dinero cuadra:* en carga, pico y resistencia se revisaron 13 027 operaciones de dinero, ninguna a medias ni duplicada.

**Qué no dicen.** Que el margen sea de 12 a 33 veces no significa capacidad ilimitada: el límite está entre 600 y 800 usuarios, y ahí el servicio no se degrada, se traba. Es una línea base relativa (una laptop, una instancia de uvicorn, SQLite local), no la capacidad de producción. El «doble» de la campaña es un supuesto nuestro, aunque lo que se midió estaría dentro incluso del umbral de hora punta.

**Cuello de botella:** no es el CPU (al colapsar baja de 35 % a 15 %) ni la memoria (sube después, por la cola). Es el candado de escritura de SQLite combinado con el pool de 40 hilos de FastAPI: las escrituras esperan el candado hasta 10 s ocupando un hilo, y el dueño del candado necesita un hilo libre para validar su respuesta antes del commit. Evidencia: los hilos pasan de 17 a 51 en el mismo minuto en que el p95 salta de 50 ms a 60 s, los 500 llegan a los 10.5 s (el `busy_timeout`) y el log tiene 3878 `database is locked`. Patrón abrupto y sin recuperación.

**Capacidad estimada:** 600 usuarios simultáneos (6 veces la hora punta, el doble de la campaña). Entre 600 y 800 puede colapsar según la ráfaga de logins; en el sondeo, con una subida más suave, aguantó hasta 1000.

**Recomendaciones:** commit dentro del endpoint para que el candado no dependa del pool; `busy_timeout` corto y `--limit-concurrency` para fallar rápido con 503; clave de idempotencia en las operaciones de dinero; validar saldo y límite dentro de la transacción de escritura (DEF-11); PostgreSQL y varios procesos para crecer más allá de 600.

El análisis completo, con el modelo de carga, los supuestos y los gráficos, está en el [informe de rendimiento](Informe_Rendimiento_G5.docx); un resumen para leer en GitHub, en [`rendimiento.md`](rendimiento.md).

## 5. Defectos encontrados

| ID | Título | Regla | Severidad | Estado |
|---|---|---|---|---|
| DEF-02 | Las transferencias interbancarias no cuentan para el límite diario | RN-06 · HU-G5-03 | Crítica | Abierto |
| DEF-04 | Una transferencia interbancaria deja el saldo en negativo | RN-08 | Crítica | Abierto |
| DEF-06 | Se puede transferir a una cuenta cerrada | RN-07 | Crítica | Abierto |
| DEF-11 | Transferencias simultáneas de la misma cuenta se saltan el límite diario y el saldo | HU-N-07 CA5 · HU-G5-03 CA2 | Crítica | Abierto |
| DEF-01 | Una reducción del límite no cancela el aumento pendiente | R-G5-02 | Alta | Abierto |
| DEF-07 | Cerrar sesión no invalida el token | HU-N-03 | Alta | Abierto |
| DEF-10 | Desde unos 800 usuarios simultáneos el servicio se traba y responde 500 | Rendimiento · capacidad | Alta | Abierto |
| DEF-03 | Una alerta notifica más de una vez por día | HU-G5-08 | Media | Abierto |
| DEF-05 | El registro acepta un PIN en secuencia descendente | RN-03 | Media | Abierto |
| DEF-08 | Un ingreso exitoso no reinicia el conteo de intentos | RN-04 | Media | Abierto |
| DEF-09 | Registros simultáneos con el mismo celular responden 500 | HU-N-01 | Media | Abierto |
| DEF-12 | Dos transferencias del mismo usuario en el mismo segundo reciben el mismo código de operación | RN-10 · HU-N-07 CA3 | Media | Abierto |
| DEF-13 | La comisión interbancaria no usa redondeo comercial: un monto cuyo 1.5 % termina en 0.005 cobra un céntimo de menos | RN-09 · HU-N-08 CA2 · HU-N-09 CA1 | Media | Abierto |

Detalle, pasos y evidencia en `docs/defectos.md`. DEF-13 lo encontró la skill de IA `proponer-casos` al recalcular a mano los valores esperados de los casos web del núcleo; los ejemplos que ya tenía la suite nunca caen en un `.005` exacto. Cada defecto tiene un escenario etiquetado `@DEF-xx` que lo detecta, salvo DEF-10, que lo detecta la prueba de estrés de k6 (`tests/performance/escenarios/estres.js`).

## 6. Conclusiones y recomendaciones

**Estado de la calidad.** Qolqe cumple lo que se le pidió en rendimiento: la hora punta (100 usuarios) y la campaña (300) pasan con tiempos de 48 a 127 ms frente a umbrales de 800 y 1500 ms, sin errores, y el dinero cuadra. Pero **no es confiable con el dinero**: hay 13 defectos abiertos (4 críticos, 3 altos y 6 medios) y los críticos son todos reglas de dinero: el límite diario no cuenta las transferencias interbancarias (DEF-02), el saldo puede quedar negativo (DEF-04), se puede transferir a una cuenta cerrada (DEF-06) y las transferencias simultáneas de la misma cuenta se saltan el límite y el saldo (DEF-11). Recomendamos no salir a producción antes de corregirlos.

**Riesgos abiertos.**
- *Dinero bajo concurrencia (DEF-11) y dos veces cobrado (DEF-12 y los reintentos tras un 500):* ningún flujo valida saldo y límite dentro de una transacción; falta una clave de idempotencia.
- *Capacidad (DEF-10):* el límite es de unos 600 usuarios simultáneos y al pasarlo el servicio se traba y no se recupera. SQLite con un solo escritor y un pool de 40 hilos es la causa; hace falta PostgreSQL y varios procesos para crecer.
- *Seguridad:* cerrar sesión no invalida el token (DEF-07) y el conteo de intentos no se reinicia (DEF-08).
- *De nuestra suite:* las pruebas comparten BD y reloj y no corren en paralelo; Qase guarda 30 días de datos (el historial permanente es el de GitHub Pages); la capacidad medida es de una laptop y no de producción.

**Recomendaciones para el equipo de desarrollo.** (1) Corregir primero los 4 defectos críticos y el DEF-10, en ese orden. (2) Validar saldo y límite dentro de la transacción de escritura y hacer el `commit` dentro del endpoint. (3) Usar `ROUND_HALF_UP` al calcular la comisión (DEF-13). (4) Documentar en el OpenAPI los `multipleOf`, mínimos y máximos, para que Schemathesis encuentre reglas de negocio y no solo errores de esquema. (5) Repetir el estrés después de cada cambio y dejar una alarma cuando el pool de hilos pase el 50 %.

**Lecciones aprendidas.**
- *El oráculo es el requisito, no la app.* Los 12 defectos de las partes anteriores salieron de comparar con el requisito; el DEF-13 salió de lo mismo, de hacer a mano una cuenta que la suite nunca había hecho.
- *Lo barato primero.* Mover el contrato a la primera etapa del pipeline (observación de la Parte 2) ahorra minutos de runner y falla antes; un gate bloquea y los hallazgos conocidos solo se reportan.
- *Un número sin explicación no convence.* Las observaciones de la Parte 3 nos pidieron justificar el think time, el ramp-up y los resultados frente a los umbrales: un «cumple» sin margen ni causa no dice nada. Ahora cada valor del modelo de carga lleva su origen.
- *La IA propone, el tester decide.* La IA ahorra el diseño de casos y la redacción de defectos, pero su propuesta solo vale si se contrasta con el requisito. En este proyecto la IA tuvo que corregir su propio dato de prueba antes de proponer y dejó dos casos sin escribir porque el requisito no los respalda (sección 7).

## 7. Anexo · Capacidad de IA

**Qué usamos.** Claude (Claude Code) con dos skills del repo, en `.claude/skills/`:

| Skill | Qué hace | Qué entra y qué sale |
|---|---|---|
| `proponer-casos` | Propone escenarios Gherkin (API o web) para una HU, con técnica (partición, valor límite), esperado citado y preguntas sobre lo que el requisito no dice | Lee `docs/requisitos.md`, `docs/defectos.md`, los `.feature` y los datos semilla; escribe en `propuestas/ia/` |
| `reporte-defecto` | Redacta un `DEF-NN` con el formato de `docs/defectos.md`, reproduciéndolo antes contra la app | Parte de un fallo o una sospecha; escribe un borrador en `propuestas/ia/` |

**Qué aporta.** Amplía la cobertura sin escribir a mano cada caso y encuentra lo que se nos escapa. Con `proponer-casos` se propusieron 15 casos web del núcleo común (login, registro y transferencia), que pasaron de 20 a 42 las pruebas web; y al rehacer los valores esperados apareció el DEF-13, que 260 pruebas no habían detectado.

**Cómo validamos el resultado: «La IA propone, el tester decide».** Lo que escribe la IA queda fuera de `features/` y de `docs/`, y no cuenta como cobertura hasta que una persona lo acepta tras el checklist de [`docs/ia-checklist.md`](ia-checklist.md): el criterio existe, el esperado sale del requisito y no de la app, no hay reglas inventadas, las cuentas están rehechas a mano, no es un duplicado, es determinista, no usa datos reales y pasa `bddgen` y `verificar_etiquetas.py`. Un escenario que falla no se «arregla»: se contrasta con el requisito y, si lo respalda, es un defecto. Aplicado a esta propuesta:
- **Esperado contra la app real, sin tocarla.** Todos coincidían salvo dos: DEF-05 (PIN `4321`, ya conocido) y el nuevo DEF-13 (S/ 67).
- **La IA corrigió su propio dato.** Para el caso «destino no registrado» probó con el celular 900000001, y la app lo aceptó: es un usuario de carga de la semilla. Se usó 900999999, que ya usan los escenarios de API como inexistente.
- **Dos casos sin escribir.** «Los PIN no coinciden» y «Cancelar en el diálogo»: la pantalla los tiene, pero `requisitos.md` no los pide. Sin criterio no hay oráculo; quedaron como preguntas.
- **El equipo decidió** (18-nov-2026): confirmó DEF-13 con severidad Media y aceptó los 15 casos.
- **Comprobado con otro conductor de navegador:** las 22 pruebas web nuevas se repitieron con Playwright sobre Chromium contra la misma app (20 con los textos esperados, 2 de defecto fallan como se espera); la corrida con Selenium queda a cargo del pipeline.

El registro de cada uso, con lo aceptado, lo corregido y lo descartado, está en [`IA.md`](../IA.md).
