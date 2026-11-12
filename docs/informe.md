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

**Alcance y nivel de prueba**

| HU | Prioridad | Nivel | Justificación |
|---|---|---|---|
| HU-N-01 a HU-N-09 (núcleo) | Alta / Media | API | Reglas de dinero, credenciales y sesión: observables en la API; la concurrencia de HU-N-07 CA5 va a rendimiento |
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
| Selenium + pytest-bdd (web) | ¿El usuario puede hacerlo en la pantalla, en Chrome y en Firefox? | Navegador real por el estándar W3C WebDriver; datos y sesión preparados por API | Las reglas finas: un caso por interfaz tarda y se rompe más que por API (19 casos web tardan 1 a 2 minutos por navegador), así que en la web van los flujos y lo que es propio de la pantalla → Playwright |
| k6 (rendimiento) | ¿Responde a tiempo con 100 y 300 usuarios, y dónde se rompe? | Usuarios virtuales con el modelo de carga del requerimiento | No revisa funcionalidad → Playwright; detecta, eso sí, reglas que se rompen bajo concurrencia (DEF-11) |
| GitHub Actions + Pages | ¿Se corrió todo, en cada cambio, y qué pasó? | Pipeline por etapas con quality gates; reportes y trazabilidad publicados | — |

El costo de combinarlas es mantener dos lenguajes (TypeScript para API y Python para web). Lo compensa que las dos suites leen el mismo formato (Gherkin con las mismas etiquetas `@HU`, `@CP`, `@CA` y `@DEF`), así la trazabilidad es una sola. Selenium nos tocó por sorteo para la web; Playwright lo elegimos para API porque su cliente `request` prueba la API sin abrir un navegador, levanta la app sola (`webServer`) y su traza guarda cada petición y respuesta como evidencia.

**Cobertura de Gherkin:** 5 archivos `.feature` (`limites`, `nucleo_registro`, `nucleo_sesion`, `nucleo_cuenta`, `nucleo_transferencias`), con todas las HU del núcleo y del módulo. Cada escenario lleva su HU, su caso, su nivel y los criterios que cubre (`@HU-G5-02 @api @CP-02 @CA-G5-02-1`). Los 48 criterios del núcleo y de G5 tienen al menos un caso de API, y la etapa `verificar` del pipeline falla si alguno se queda sin caso.

**Casos funcionales y técnicos:** los funcionales verifican las reglas de negocio (R-G5-01 a R-G5-05, RN-01 a RN-09) con particiones y valores límite. Los técnicos (`@tecnico`) verifican la interfaz de cada HU del núcleo y del módulo: autenticación (sin token, con un token inválido o vencido → 401 `NO_AUTENTICADO`), cuerpo vacío, campo faltante o tipo inválido (422 `SOLICITUD_INVALIDA` que indica el campo), ausencia de efecto tras un rechazo (el saldo, el límite o el perfil no cambian y no se envía el SMS) y propiedad de los datos (la alerta o el contacto de otro usuario responden 404 y no se modifican; el gasto de otro usuario no consume mi límite ni dispara mis alertas). Registro e inicio de sesión son públicos, así que ahí no aplica el 401. Hay 92 casos funcionales y 39 técnicos; la matriz por criterio está en [`trazabilidad.md`](trazabilidad.md).

## 2. Pruebas de API

**Herramienta:** Playwright Test (cliente `request` / `APIRequestContext`) + playwright-bdd. Los escenarios de `features/*.feature` se enlazan con pasos en TypeScript (`tests/api-playwright/pasos.ts`, `pasos_nucleo.ts`); `bddgen` los convierte en specs de Playwright.

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

**Resultados:** 108 escenarios (8 técnicos): 97 pasan, 10 fallan como se espera porque detectan 9 defectos (DEF-06 tiene dos escenarios) y 1 quedaba para la Parte 3 (`@rendimiento`). En la Parte 3 ese escenario se activó (CP-53) junto con CP-86 y los dos detectan DEF-11; hoy la suite tiene 260 pruebas (131 casos con sus ejemplos) y todas pasan, contando los 13 fallos esperados. Tras la retroalimentación de la Parte 2 se agregaron 58 casos (CP-87 a CP-144) para cubrir cada criterio con casos funcionales y técnicos; uno de ellos encontró DEF-12.

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

**El problema.** La pantalla de límites cambia (textos, `data-testid`, orden de campos), la suite la mantienen dos personas y los pasos de Gherkin tienen que leerse como la historia de usuario. Elegimos el patrón con cuatro criterios: (1) un cambio de interfaz se corrige en un solo lugar; (2) los pasos hablan el idioma del negocio; (3) poco código extra para el tamaño de la suite (16 escenarios en 4 pantallas); (4) que los dos podamos explicarlo y mantenerlo; (5) expresar escenarios con varios usuarios a la vez, porque en Qolqe el dinero pasa de un usuario a otro y la Parte 3 trata justamente de usuarios simultáneos.

| Opción | (1) Un cambio, un lugar | (2) Pasos de negocio | (3) Código extra | (4) Mantenerlo entre dos | (5) Varios usuarios | Decisión |
|---|---|---|---|---|---|---|
| Script lineal, sin patrón | no: el mismo localizador se repite en cada paso que lo usa | no: los pasos se llenan de `find_element` | ninguno | fácil al inicio, frágil después | no | descartado |
| **Page Object** | **sí: cada localizador vive en su página** | **sí: `cambiar_limite(500)`** | **4 páginas y una base** | **sí** | no: la página no sabe quién la usa | **elegido para las pantallas** |
| **Screenplay** | sí, porque usa las páginas por dentro | **sí, aún más: «Ana le transfiere a Bruno»** | alto: actores, tareas y preguntas | más conceptos que aprender | **sí: cada actor con su navegador y su sesión** | **elegido para los flujos entre usuarios** |
| Page Factory | sí | sí | — | — | — | no existe en Python (`@FindBy` es de Java) |

**La evidencia de que cumple.** Los 34 localizadores están en `pages/limites_page.py` (17), `transferir_page.py` (10), `login_page.py` (4) e `inicio_page.py` (3); de los 37 pasos, ninguno busca un elemento por su cuenta (solo uno lee el texto completo de la página para verificar un mensaje). `scripts/selenium.sh romper` cambia a propósito un localizador y el flujo feliz falla; arreglarlo es una línea en `limites_page.py` y los 15 escenarios vuelven a pasar. Screenplay, en `tests/e2e/screenplay/`, resuelve lo que Page Object no: **quién** hace cada cosa. En CP-145 (`features/ui/dos_usuarios_ui.feature`) Ana y Bruno ingresan cada uno en su propio navegador, con su propia sesión; Ana le transfiere S/ 50 a Bruno, y Bruno ve el dinero en su saldo y en sus movimientos. El escenario se lee igual que el código: `ana.intenta(Transferir.a("Bruno").por(50))` y `bruno.ve(SaldoDisponible("S/ 850.00"))`. Pasa en Chrome y en Firefox. Las tareas usan las páginas por dentro (`TransferirPage`, `InicioPage`), así que no se duplica ningún localizador: Page Object responde «dónde está cada botón» y Screenplay, «quién hace qué».

Junto a Page Object usamos Component Object (el menú, que aparece en varias páginas), una clase base con las esperas explícitas (`WebDriverWait`, nunca `sleep`), una fábrica de navegadores (local, Grid, móvil) y una fachada de la API para preparar datos. Localizadores: `data-testid` en todos los elementos propios de la pantalla y el texto del enlace en el menú; ningún XPath.

### Pipeline y quality gates

`.github/workflows/pruebas.yml`, por etapas: si una etapa barata falla, las largas no corren.

| Etapa | Jobs (en paralelo) | Gate |
|---|---|---|
| 1 · ~1 min | `verificar`, `contrato` | Trazabilidad completa (cada escenario con HU, CP y criterio; cada criterio del núcleo y G5 con caso; cada fallo esperado con su DEF) y Gherkin que compila. Contrato: sin 500 y respuestas como dice el OpenAPI |
| 2 | `api`, `web (chrome)`, `web (firefox)` | 0 failed; un fallo esperado solo puede fallar por su defecto y, si pasa, el job falla; 0 flaky; 0 `test.only` |
| 3 | `reportes` | Publica portada, trazabilidad con historial y cobertura del contrato en Pages |

Cambios respecto de la Parte 2, por la retroalimentación: el contrato pasó de correr después de la API a correr primero, como gate; el gate del contrato separa lo que bloquea (la API no cumple su propio contrato) de los hallazgos ya analizados, que se reportan sin bloquear, así el job ya no sale en rojo en cada corrida; `api` y `web` corren en paralelo; el pipeline no corre al subir un tag (antes corría dos veces por entrega) ni con cambios solo de documentación; y cada job tiene un tiempo máximo. La tabla completa de gates, con umbrales, está en [`pruebas.md`](pruebas.md#quality-gates).

**Evidencia con o sin capturas.** Al lanzar el pipeline a mano se elige `con` (una captura por paso en la web y la traza de cada petición en la API), `fallos` (solo lo que falla; es lo que usa cada push) o `sin` (reporte liviano). En local: `EVIDENCIA=con npm test` o `scripts/selenium.sh todo --evidencia sin`.

### Trazabilidad entre corridas y gestión de casos

Cada escenario lleva `@CP-NN`, sus `@HU` y sus criterios (`@CA-N-07-3` = HU-N-07 CA3). La matriz que publica el pipeline muestra la cobertura por historia (casos funcionales y técnicos), la cobertura por criterio y, por cada caso, el resultado de esta corrida y el de las últimas 30 corridas de `main` (`passed 30`, o `passed 28 · failed 2 · último fallo run #45`). Así se ve desde cuándo falla un caso, si un defecto se corrigió y qué casos son inestables, no solo el último resultado.

**Gestión de casos.** Comparamos 14 herramientas (Qase, Testomat.io, BrowserStack, Kiwi TCMS, TestLink, Xray, Zephyr, TestRail, Testmo, Allure TestOps y otras) con cinco criterios: gratis sin vencimiento, resultados desde GitHub Actions, historial por caso, defectos ligados al resultado y acceso para la profesora. Elegimos **Qase** (plan gratis): es la única que cumple los cinco. El job `reportes` crea una corrida de Qase por pipeline de `main` y sube los JUnit de API, contrato y web con `qasectl`; cada escenario acumula su historial y desde un resultado fallido se registra el defecto. Comparación, límites asumidos y cómo activarlo en [`gestion-casos.md`](gestion-casos.md).

**Resultados web:** 17 passed y 3 xfailed en Chrome y en Firefox (los escenarios de límites, el de dos usuarios con Screenplay, el ejemplo de Screenplay de un actor y los 3 defectos de interfaz conocidos). Reportes: `reportes/selenium/reporte-bdd.html` y el sitio en [kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/).

## 4. Pruebas de rendimiento

**Herramienta:** Grafana k6 v2.3. Cada umbral del requerimiento se escribe tal cual en el script (`'http_req_duration{tipo:consulta}': ['p(95)<800']`) y k6 dice si pasó; corre fuera de Qolqe con poco consumo (4 % de un núcleo con 2000 VUs) y usa JavaScript, como las pruebas de API en TypeScript. Se comparó con JMeter, Gatling, Locust y Artillery (informe de rendimiento, sección 2).

**Entorno:** Qolqe en Docker con `--cpus=1 --memory=1g` (uvicorn con un proceso, SQLite en WAL) y k6 nativo en la misma laptop (MacBook Pro M5, 16 GB). CPU, memoria e hilos de Qolqe y de k6 se miden cada segundo con `tests/performance/monitor.py` (psutil). Es una línea base relativa, no la capacidad de producción.

**Modelo:** una iteración de k6 es una sesión: login y 6 operaciones sorteadas con los porcentajes del requerimiento, con una pausa de 10 a 25 s (triangular, promedio exacto de 18 s). Hora punta: 3000 sesiones/h × 2 min = **100 VUs** (ley de Little). Campaña: **300 VUs**, con la subida en los primeros 5 minutos. Un usuario distinto por VU, con saldo, deudas y contactos propios (`tests/performance/datos/preparar_datos.py`).

**Cómo se corre:** `tests/performance/correr.sh <prueba>` levanta Qolqe limpio, prepara los datos, mide los recursos, corre k6 y al final verifica el dinero (`verificar_dinero.py`: saldos contra movimientos, cada transferencia con su salida y su entrada, ninguna deuda pagada dos veces y operaciones en la BD = respuestas 201 de k6) y genera los gráficos. Todo queda en `tests/performance/resultados/<prueba>/`.

| Prueba | VUs | p95 consultas | p95 dinero | Errores | Throughput | Dinero | Veredicto |
|---|---|---|---|---|---|---|---|
| Carga (hora punta, 20 min) | 100 | 51 ms | 126 ms | 0 % | 55 sesiones/min | cuadra | Cumple |
| Pico (campaña) | 100 → 300 → 100 | 48 ms | 127 ms | 0 % | 166 sesiones/min | cuadra | Cumple, sin degradación |
| Estrés (escalones) | 600 | 51 ms | 126 ms | 0 % | 315 sesiones/min | — | Cumple |
| Estrés (escalones) | 800 | 60 s | 60 s | 86 % | 45 sesiones/min | 6 operaciones sin confirmar | Colapsa (DEF-10) |
| Resistencia (60 min) | 100 | 42 ms | 126 ms | 0 % | 56 sesiones/min | cuadra | Cumple; memoria +5.5 MB/h |
| Concurrencia (misma cuenta) | 1 | — | — | — | — | límite y saldo superados en 5 de 5 rondas | Falla (DEF-11) |

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

Detalle, pasos y evidencia en `docs/defectos.md`. Cada defecto tiene un escenario etiquetado `@DEF-xx` que lo detecta, salvo DEF-10, que lo detecta la prueba de estrés de k6 (`tests/performance/escenarios/estres.js`).
