# Guía de Selenium para la expo · G5 Límites

Esta guía explica, en palabras simples, todo lo que se menciona en la presentación y cómo está armada la suite. Si solo vas a leer una parte antes de exponer, lee **5. Guion de la demo**.

1. [Glosario](#1-glosario)
2. [Cómo funciona una prueba por dentro](#2-cómo-funciona-una-prueba-por-dentro)
3. [Cómo armar una prueba nueva, paso a paso](#3-cómo-armar-una-prueba-nueva-paso-a-paso)
4. [Qué hay en el repositorio](#4-qué-hay-en-el-repositorio)
5. [Guion de la demo](#5-guion-de-la-demo)
6. [Preguntas probables](#6-preguntas-probables)

---

## 1. Glosario

### La web y los estándares

| Término | Qué es |
|---|---|
| **W3C** | *World Wide Web Consortium*. La organización que escribe los estándares de la web (HTML, CSS…). Que algo sea "estándar W3C" significa que todos los navegadores se comprometen a implementarlo igual. |
| **Recomendación W3C** | El nivel final de un estándar del W3C. WebDriver lo alcanzó en junio de 2018. |
| **Protocolo** | Un acuerdo de cómo dos programas se hablan: qué mensajes se mandan y en qué formato. |
| **HTTP** | El protocolo de la web: alguien pide (*request*) y el otro responde (*response*). Siempre pregunta uno y responde el otro. |
| **WebSocket** | Una conexión que queda abierta y por la que **ambos lados** pueden mandar mensajes cuando quieran. Es la base de BiDi. |
| **DOM** | La estructura de la página que arma el navegador a partir del HTML: un árbol de elementos (botones, campos, textos). Selenium busca elementos en el DOM. |
| **Política de mismo origen** | Regla de seguridad del navegador: el JavaScript de una página no puede tocar páginas de otro dominio. Por eso el Selenium de 2004, que era JavaScript dentro de la página, no podía probar otros sitios. |

### Selenium y su historia

| Término | Qué es |
|---|---|
| **Selenium Core** (2004) | El primer Selenium: un motor en JavaScript que se metía en la página y ejecutaba comandos. |
| **Selenese** | El "idioma" de Selenium Core: tablas de tres columnas (comando, objetivo, valor), por ejemplo `type | id=celular | 987654321`. |
| **Selenium IDE** (2006) | Extensión del navegador para **grabar** clics y reproducirlos sin programar. Hoy existe para Chrome y Firefox. No la usamos: sirve para prototipos, no para una suite mantenible. |
| **Selenium RC** (*Remote Control*, Selenium 1) | Un servidor intermedio (proxy) que engañaba al navegador para saltarse la política de mismo origen. Funcionaba, pero era lento y frágil. Se retiró en Selenium 3. |
| **WebDriver** | La idea de Simon Stewart (2006): controlar el navegador **desde afuera**, usando la automatización que el propio navegador ofrece. Se fusionó con Selenium en 2011 (Selenium 2). Hoy "Selenium" y "WebDriver" se usan casi como sinónimos. |
| **W3C WebDriver** | El estándar (2018) que define los mensajes HTTP para controlar un navegador: "abre esta URL", "busca este elemento", "haz clic". |
| **Driver** (chromedriver, geckodriver, msedgedriver, safaridriver) | Un programa pequeño, hecho por **cada fabricante de navegador**, que recibe los mensajes W3C y los ejecuta en su navegador. geckodriver es el de Firefox (lo hace Mozilla). |
| **Bindings** (o librería cliente) | La librería de Selenium para tu lenguaje (Python, Java, C#…). Traduce `driver.find_element(...)` a un mensaje HTTP para el driver. Nosotros usamos los bindings de Python: `pip install selenium`. |
| **Selenium Manager** (Selenium 4.6, 2022) | Busca y descarga el driver correcto (y hasta el navegador si falta). Antes había que bajar el driver a mano y cuidar que su versión coincidiera con la del navegador. En nuestra Mac descargó Firefox solo. |
| **WebDriver BiDi** | *Bidireccional*. Nueva versión del estándar que agrega un WebSocket: además de que la prueba pregunte, **el navegador avisa** (un mensaje de consola, una petición de red). Con eso escuchamos la consola e interceptamos la red. |
| **CDP** (*Chrome DevTools Protocol*) | El protocolo propio de Chrome que usan sus herramientas de desarrollador. Selenium 4 lo expuso para hacer cosas avanzadas, pero solo en Chromium. BiDi es su reemplazo estándar para todos los navegadores. |
| **Selenium Grid** | Un sistema para repartir pruebas en muchas máquinas y navegadores. El **hub** (en el puerto 4444) recibe la sesión y la manda a un **nodo** libre que tiene el navegador. Nosotros levantamos el Grid con Docker. |
| **Sesión** | Una conversación entre la prueba y un navegador abierto. Empieza cuando se crea el `driver` y termina con `driver.quit()`. |
| **Headless** | El navegador corre sin ventana visible. Es más rápido y es lo que se usa en CI. |
| **Emulación móvil** | Chrome finge ser un celular: cambia el tamaño de pantalla y el *user agent*. Nuestro modo `--movil` emula un iPhone 12 Pro. |

### Encontrar elementos y esperar

| Término | Qué es |
|---|---|
| **Localizador** (*locator*) | La "dirección" de un elemento en la página: un par (estrategia, valor), por ejemplo `(By.CSS_SELECTOR, '[data-testid="boton-ingresar"]')`. |
| **Selector CSS** | Una forma corta de describir elementos: `#celular` (por id), `[data-testid="x"]` (por atributo). |
| **XPath** | Otra forma, más potente y más larga: `//li[.//strong[text()='Recargas']]`. La usamos para encontrar "la fila de la alerta que tiene este título". |
| **data-testid** | Un atributo que los desarrolladores ponen en el HTML solo para las pruebas. Es el localizador más estable porque no cambia cuando cambia el diseño. Qolqe lo tiene en todos sus controles. |
| **Localizador relativo** (Selenium 4) | Buscar por posición respecto de otro elemento: "el botón **debajo** de este campo" (`locate_with(...).below(campo)`). |
| **Espera explícita** | Decirle a Selenium "espera **hasta que** este botón sea clickeable, máximo 10 s" (`WebDriverWait` + `expected_conditions`). Es la forma correcta de esperar. |
| **Espera implícita** | Un tiempo general que Selenium espera al buscar cualquier elemento. Es menos precisa; no la usamos. |
| **`time.sleep`** | Esperar un tiempo fijo. Es mala práctica: o esperas de más (lento) o de menos (falla). Solo lo usamos en el modo demo para que el público alcance a ver el resaltado. |
| **TimeoutException** | El error cuando una espera explícita se cumple sin que aparezca lo esperado. |
| **ElementClickInterceptedException** | El error cuando otro elemento tapa al que quieres hacer clic. Nos pasó en móvil: el aviso flotante tapaba el botón "Reanudar". |
| **StaleElementReferenceException** | El elemento que tenías ya no existe porque la página lo redibujó. Se evita volviendo a buscarlo (nuestra `BasePage` lo ignora en las esperas). |
| **Flaky** | Una prueba que a veces pasa y a veces falla sin que cambie el código. Casi siempre es por esperas mal hechas. |

### Pruebas y BDD

| Término | Qué es |
|---|---|
| **Prueba E2E** (*end to end*, extremo a extremo) | Prueba el sistema completo como lo usa una persona: navegador, interfaz, API y base de datos juntos. |
| **Pirámide de pruebas** | Muchas pruebas unitarias (rápidas), menos de API y pocas E2E (lentas y caras). Por eso las reglas de G5 se prueban sobre todo por API (Parte 1) y la UI se reserva para los flujos del usuario. |
| **Happy path** (flujo feliz) | El camino normal, sin errores: Ana entra, baja su límite y crea una alerta. |
| **BDD** (*Behavior Driven Development*) | Escribir primero el comportamiento esperado en lenguaje de negocio, que entienden todos, y después automatizarlo. |
| **Gherkin** | El lenguaje de BDD. Palabras clave en español: `Característica`, `Antecedentes`, `Escenario`, `Esquema del escenario`, `Ejemplos`, `Dado`, `Cuando`, `Entonces`, `Y`. |
| **Característica** (*Feature*) | Un archivo `.feature`: un tema con varios escenarios. |
| **Escenario** | Un caso concreto: preparación (`Dado`), acción (`Cuando`) y resultado esperado (`Entonces`). |
| **Antecedentes** (*Background*) | Pasos que se repiten antes de cada escenario del archivo (reiniciar datos, fijar la fecha). |
| **Esquema del escenario + Ejemplos** | Un escenario con huecos (`<umbral>`) que se ejecuta una vez por cada fila de la tabla de ejemplos. Nuestro esquema de validación de umbral corre 6 veces. |
| **Etiqueta** (*tag*) | `@happy`, `@HU-G5-03`, `@DEF-01`: sirven para filtrar qué correr (`-m happy`). |
| **Step definition** (definición de paso) | La función de Python que ejecuta una frase del Gherkin. Está en `tests/e2e/test_limites_ui.py`. |
| **pytest** | El framework de pruebas de Python: encuentra las pruebas, las corre y reporta. |
| **pytest-bdd** | El plugin que conecta Gherkin con pytest: lee los `.feature` y busca la definición de cada paso. |
| **Fixture** | En pytest, algo que se prepara para una prueba y se limpia al final. Ejemplo: `driver` abre el navegador y lo cierra al terminar. |
| **conftest.py** | El archivo donde pytest busca fixtures, opciones (`--navegador`…) y *hooks*. |
| **Hook** | Una función que pytest o pytest-bdd llaman en un momento dado: "después de cada paso", "cuando un paso falla". Con ellos tomamos las capturas y armamos el reporte. |
| **Page Object** | El patrón de diseño que pide el enunciado: una clase por página (`LimitesPage`) que sabe cómo encontrar sus elementos y ofrece acciones (`cambiar_limite(500)`). Los pasos solo dicen **qué** hacer; el Page Object sabe **cómo**. Si cambia la página, se corrige un solo archivo. |
| **xfail** (*expected failure*) | Una prueba que **se espera que falle** porque describe un defecto conocido. Si falla, sale en amarillo ("defecto conocido"); si un día pasa, pytest avisa porque el defecto se corrigió. Con `--runxfail` se ven como fallas reales, en rojo. |
| **Datos semilla** | Los datos iniciales de la app (Ana, Bruno, Diego…). Cada escenario los restaura para no depender de otro (la propiedad *Independent* de FIRST). |
| **CI** (*integración continua*) | Correr las pruebas automáticamente en cada `push`. Lo hacemos con **GitHub Actions** (`.github/workflows/pruebas.yml`). |

### La app Qolqe y la infraestructura

| Término | Qué es |
|---|---|
| **API de soporte** | Endpoints `/api/pruebas/*` que existen solo para probar: reiniciar datos, fijar el reloj, ver los SMS simulados. |
| **Reloj de la app** | La fecha que usa Qolqe. La fijamos en `2026-11-10 10:00` para que las pruebas sean repetibles, y la adelantamos 24 h para probar el aumento programado. |
| **Token JWT** | La "credencial" que devuelve el login; vence a los 30 minutos. Por eso, al adelantar el reloj 24 h, hay que volver a ingresar. |
| **sessionStorage** | Un almacenamiento del navegador donde Qolqe guarda el token. Nuestro login híbrido pide el token por API y lo escribe ahí con JavaScript, para no pasar por la pantalla de login en cada escenario. |
| **Toast** | El aviso flotante que aparece unos segundos en una esquina ("Alerta creada"). |
| **Docker** | Corre programas en **contenedores**: mini-computadoras aisladas. Así levantamos el Grid con Chromium y Firefox sin instalarlos. |
| **docker compose** | Levanta varios contenedores juntos a partir de un archivo (`docker-compose.grid.yml`). |
| **noVNC** | Un visor web del escritorio del contenedor. En `http://localhost:7900` se ve en vivo el Chromium que está dentro de Docker. |
| **host.docker.internal** | Nombre con el que un contenedor llega a tu Mac. El navegador del Grid abre la app en `http://host.docker.internal:8000`. |

### IA

| Término | Qué es |
|---|---|
| **Self-healing** (auto-reparación) | Cuando un localizador deja de funcionar, la herramienta busca uno nuevo sola en vez de fallar. |
| **Sanador** | Nuestro módulo (`tests/e2e/soporte/sanador.py`): manda a Claude la intención del localizador y los elementos visibles de la página, recibe un selector CSS nuevo, verifica que encuentre **un solo** elemento y deja registro en `reportes/selenium/sanaciones.json`. |
| **Claude API** | La API de Anthropic para usar el modelo Claude desde código. Necesita la variable `ANTHROPIC_API_KEY`. |
| **Healenium** | Una herramienta open source de auto-reparación para Selenium en Java. Es el equivalente "de mercado" de nuestro sanador. |

---

## 2. Cómo funciona una prueba por dentro

Tomemos el paso `Cuando cambia su límite diario a S/ 500`:

```
features/ui/limites_ui.feature      "Cuando cambia su límite diario a S/ 500"
        │  pytest-bdd busca la definición cuyo texto coincide
        ▼
tests/e2e/test_limites_ui.py        @when("cambia su límite diario a S/ {monto:d}")
        │  el paso solo expresa la intención
        ▼                           LimitesPage(driver).cambiar_limite(500)
tests/e2e/pages/limites_page.py     escribir(NUEVO_LIMITE, 500) + clic en Guardar
        │  BasePage espera a que el campo sea visible (WebDriverWait)
        ▼
Selenium (bindings de Python)       POST /session/{id}/element/{id}/value  {"text": "500"}
        │  HTTP, protocolo W3C WebDriver
        ▼
chromedriver                        lo ejecuta con la automatización nativa de Chrome
        ▼
Chrome                              el campo muestra "500"; la app llama PUT /api/limites
```

Y en paralelo:

- **BiDi** (WebSocket): Chrome avisa de cada mensaje de consola; lo guardamos para el reporte.
- **Hooks de pytest-bdd**: después del paso, `conftest.py` toma una captura y la anota en el reporte.

Un escenario completo también usa la **API de la app** por fuera del navegador: reiniciar datos y fijar el reloj (Antecedentes), iniciar sesión rápido (login híbrido) y verificar efectos que la pantalla no muestra, como el SMS.

### Patrones de diseño de la automatización

**¿Selenium nos obliga a usar Page Object?** No. Selenium solo controla el navegador; cómo organizamos nuestro código es decisión nuestra. La documentación de Selenium *recomienda* Page Object, un lenguaje de dominio (nuestro Gherkin) y preparar el estado de la app por API en vez de por la interfaz. Hacemos las tres cosas.

**Cómo aplicamos Page Object y por qué.** Cada pantalla tiene una clase en `tests/e2e/pages/` (`LoginPage`, `LimitesPage`, `TransferirPage`) que hereda de `BasePage`. La clase guarda los localizadores como constantes (`NUEVO_LIMITE = tid("input-nuevo-limite")`) y ofrece acciones con nombre de negocio (`cambiar_limite(500)`). Los pasos de Gherkin solo llaman a esas acciones. **Por qué:** si cambia un `data-testid`, se corrige una línea en la página y los 15 escenarios siguen funcionando; y los pasos se leen como la historia de usuario.

**Sí se combinan varios patrones.** En la suite conviven seis, cada uno para un problema distinto:

| Patrón | Dónde | Para qué |
|---|---|---|
| Page Object | `pages/limites_page.py` | Selectores y acciones de cada pantalla en un solo lugar |
| Component Object | `Menu` en `pages/login_page.py` | Una parte que se repite en varias páginas (el menú) se modela una vez |
| Herencia / Template | `pages/base_page.py` | Esperas, resaltado e IA comunes a todas las páginas |
| Factory | `soporte/navegador.py` | Un solo punto que crea Chrome, Edge, Firefox, Safari o una sesión del Grid |
| Facade + estado por API | `soporte/api.py` | Esconde las llamadas HTTP; prepara datos y sesión sin pasar por la UI |
| Proxy (auto-reparación) | `BasePage.visible` + `soporte/sanador.py` | Se interpone en la búsqueda: si falla, la IA intenta antes de rendirse |

**¿Y si nos piden otro patrón?** El más común es **Screenplay** (popular en Serenity BDD): en vez de páginas, un **actor** con **habilidades** (navegar la web) que realiza **tareas** y hace **preguntas** sobre lo que ve. Está implementado en `tests/e2e/screenplay/` y `tests/e2e/test_screenplay.py` con el mismo flujo de Ana, y pasa:

```python
ana = Actor.llamado("Ana").que_puede(NavegarLaWeb(driver))
ana.intenta(IniciarSesion.como("Ana"), IrA("Límites y alertas"),
            CambiarLimiteDiario.a(500), CrearAlerta.de("Recargas").desde(50))
assert ana.ve(LimiteDiarioVigente("S/ 500.00")) == "S/ 500.00"
```

Las tareas de Screenplay llaman por dentro a `LimitesPage`: **Page Object y Screenplay conviven**. Cambiar de patrón solo afecta a la capa de pasos; el `.feature` y las páginas se quedan. Screenplay conviene en suites grandes, con varios actores y flujos que cruzan muchas páginas; para nuestro módulo, Page Object es más simple y suficiente.

Otros patrones que existen y no usamos: **Page Factory** (anotaciones `@FindBy` de Java; no existe en Python), **Loadable Component** (una página sabe verificar si terminó de cargar; nuestro `esperar_carga()` hace algo parecido) y **Data Builder** (construir datos de prueba paso a paso).

Para correr solo el ejemplo de Screenplay: `.venv/bin/python -m pytest tests/e2e -m screenplay --demo`.

---

## 3. Cómo armar una prueba nueva, paso a paso

Ejemplo: queremos comprobar que **lo disponible baja** después de transferir.

**1. Leer la historia y la regla.** En `docs/requisitos.md`: HU-G5-01 dice que veo lo usado y lo disponible del día.

**2. Escribir el escenario en Gherkin**, en `features/ui/limites_ui.feature`, reutilizando frases que ya existen siempre que se pueda:

```gherkin
  @HU-G5-01
  Escenario: Lo disponible baja después de transferir
    Dado que Diego tiene la sesión iniciada
    Cuando transfiere S/ 300 al celular 912345678
    Y abre la página de límites
    Entonces lo disponible hoy es "S/ 700.00"
```

**3. Correrlo para ver qué falta.** pytest-bdd avisa qué frase no tiene definición:

```bash
.venv/bin/python -m pytest tests/e2e -k disponible
# StepDefinitionNotFoundError: Step definition is not found: Then "lo disponible hoy es "S/ 700.00""
```

**4. Escribir la definición del paso** en `tests/e2e/test_limites_ui.py`. Solo intención, sin selectores:

```python
@then(parsers.parse('lo disponible hoy es "{monto}"'))
def disponible_hoy(driver, monto):
    pagina = LimitesPage(driver)
    real = pagina.esperar_texto(pagina.DISPONIBLE, monto)
    assert real == monto, f"Se esperaba {monto!r} y la pantalla muestra {real!r}"
```

**5. Si el Page Object no conoce el elemento, agregarlo.** Para encontrar el localizador: abrir la app en Chrome, clic derecho sobre el elemento › **Inspeccionar**, y buscar su `data-testid`. Aquí ya existe: `DISPONIBLE = tid("limite-disponible")`.

**6. Correrlo viendo el navegador** y revisar el reporte:

```bash
.venv/bin/python -m pytest tests/e2e -k disponible --demo
scripts/selenium.sh reporte
```

**7. Etiquetarlo** (`@HU-G5-01`) para poder filtrarlo y trazarlo con la historia de usuario.

**Reglas de oro**
- Un escenario no depende de otro: siempre parte de datos restaurados.
- Nada de `sleep`: usar las esperas de `BasePage`.
- Los selectores viven solo en `pages/`.
- El mensaje del `assert` dice qué se esperaba y qué se vio: es lo que leerá el reporte.
- Si el escenario describe un defecto conocido, va en `features/ui/defectos_ui.feature` con `@DEF-xx`.

---

## 4. Qué hay en el repositorio

```
features/ui/limites_ui.feature    15 escenarios (Gherkin en español)
features/ui/defectos_ui.feature   3 escenarios de defectos conocidos (DEF-01, 02, 03)
tests/e2e/
  conftest.py                     opciones, levanta la app si hace falta, capturas, reportes
  test_limites_ui.py              definiciones de pasos
  pages/                          Page Objects: base, login (+ menú), límites, transferir
  screenplay/ + test_screenplay.py  el mismo happy path con el patrón Screenplay
  soporte/
    navegador.py                  crea el driver: local o Grid, con o sin ventana, móvil
    bidi.py                       consola del navegador e intercepción de red
    api.py                        cliente de la API de Qolqe (datos, reloj, SMS)
    sanador.py                    reparación de localizadores con Claude
    reporte.py                    reporte BDD en HTML
docker-compose.grid.yml           Selenium Grid 4: hub + Chromium + Firefox (+ noVNC)
scripts/selenium.sh               todos los modos de ejecución
reportes/selenium/                reportes y capturas (no se suben a git)
```

Comandos (`scripts/selenium.sh <modo>`):

| Modo | Qué hace |
|---|---|
| `preparar` | Levanta el Grid y hace una corrida rápida para calentar todo |
| `todo` | Los 18 escenarios BDD + el ejemplo Screenplay, sin ventana: 16 pasan y 3 son defectos conocidos |
| `demo` | El flujo feliz con Chrome visible y cada elemento resaltado |
| `defectos` | Los 3 defectos como fallas reales (rojo), visibles; abre el reporte |
| `navegadores` | Todo en Chrome, Edge y Firefox |
| `movil` | El flujo feliz emulando un iPhone |
| `grid` | Todo en el Grid (Chromium y Firefox en Docker). Acepta filtros: `grid -m happy --demo` |
| `romper` / `ia` | Un localizador roto: sin IA falla; con IA, Claude lo repara |
| `reporte` | Abre `reportes/selenium/reporte-bdd.html` |
| `grid-parar` | Apaga los contenedores |

---

## 5. Guion de la demo

### El día anterior (una sola vez)

```bash
cd ~/PruebasTestAutomatizacion/proyecto/qolqe-g5-limites
/opt/homebrew/bin/python3.12 -m venv .venv          # si no existe
.venv/bin/pip install -r requirements-e2e.txt
scripts/selenium.sh todo                             # debe decir: 16 passed, 3 xfailed
```

- Abrir **Docker Desktop**, esperar a que diga *Engine running* y correr `scripts/selenium.sh grid -m happy`: la primera vez descarga las imágenes de Docker y tarda varios minutos.
- **Grabar un video** de respaldo de la demo completa (con QuickTime: Archivo › Nueva grabación de pantalla).
- Si van a mostrar la IA: conseguir una clave en console.anthropic.com y guardarla con `export ANTHROPIC_API_KEY=...` en la terminal de la demo. Probar `scripts/selenium.sh ia` antes.

### 10 minutos antes

1. Abrir **Docker Desktop** y esperar *Engine running*.
2. En una terminal:
   ```bash
   cd ~/PruebasTestAutomatizacion/proyecto/qolqe-g5-limites
   scripts/selenium.sh preparar
   ```
   Debe terminar con `1 passed` y `Listo. Grid: http://localhost:4444/ui …`.
3. Dejar abiertas en el navegador, en pestañas: `http://localhost:4444/ui` (consola del Grid) y `http://localhost:7900` (noVNC del Chromium de Docker; clic en **Connect**).
4. Agrandar la letra de la terminal (⌘ +) para que se lea desde el fondo.
5. Cerrar notificaciones y otras apps.

### En vivo (unos 3 minutos)

| # | Comando | Qué se ve | Qué decir |
|---|---|---|---|
| 1 | `scripts/selenium.sh demo` | Se abre Chrome; cada campo se resalta en rojo antes de usarlo; login, límite a 500, alerta de recargas. Termina en `1 passed` | "Esto es el escenario de Gherkin que vieron, ejecutándose. Nadie toca el teclado." |
| 2 | `scripts/selenium.sh defectos` | Chrome corre los 3 escenarios de defectos; terminan en `3 failed` y se abre el reporte en rojo | "Así se ve cuando algo se rompe: el paso exacto, el error en una frase y la captura." Abrir DEF-01 y hacer clic en la captura roja. |
| 3 | Pasar a la pestaña `localhost:7900` y correr `scripts/selenium.sh grid -m happy --demo` | En el visor de noVNC, el Chromium **dentro de Docker** hace el flujo solo; luego Firefox | "Esto ya no es mi Mac: son navegadores en contenedores, coordinados por Selenium Grid." Mostrar `localhost:4444/ui`. |
| 4 | (si hay clave) `scripts/selenium.sh romper` y luego `scripts/selenium.sh ia` | El primero falla con `TimeoutException`; el segundo imprime `[IA] ... -> [data-testid="input-nuevo-limite"]` y pasa | "Rompimos un selector a propósito. Claude propone uno nuevo, Selenium verifica que sea único y lo deja registrado para revisión humana." |

### Plan B

- **Algo falla en vivo:** abrir `scripts/selenium.sh reporte` (el último reporte ya generado) o poner el video.
- **Docker no levanta:** saltar el paso 3; decir que el resultado del Grid está en la diapositiva de resultados.
- **Sin internet o sin clave de API:** saltar el paso 4 y explicar la IA con la diapositiva.

### Problemas comunes

| Síntoma | Causa | Solución |
|---|---|---|
| `La app no responde` o `La app no levantó` | Otra app usa el puerto 8000 | `lsof -i :8000` y cerrar ese proceso |
| El Grid se queda colgado | Docker recién iniciado o sin memoria | `scripts/selenium.sh grid-parar` y volver a `preparar` |
| `SessionNotCreatedException` en Safari | Safari no está habilitado | `sudo safaridriver --enable` y en Safari: Desarrollo › Permitir automatización remota |
| La IA falla con `Could not resolve authentication method` | No hay `ANTHROPIC_API_KEY` en esa terminal | `export ANTHROPIC_API_KEY=...` |
| Chrome muestra "Cambia tu contraseña" | Aviso de contraseñas de Chrome | Ya está desactivado en `navegador.py`; si aparece, usar `--headless` |

---

## 6. Preguntas probables

**¿Por qué Selenium y no Playwright?** Nos tocó por sorteo, pero tiene ventajas reales: es estándar W3C mantenido por los fabricantes, corre en Safari real y funciona en muchos lenguajes. El costo es escribir más código propio (esperas, reportes).

**¿Selenium espera solo como Playwright?** No. Por eso `BasePage` envuelve cada acción con esperas explícitas. Es el precio de Selenium y se paga una sola vez en el Page Object.

**¿Qué diferencia hay entre WebDriver y BiDi?** WebDriver clásico es preguntar y responder por HTTP. BiDi abre un WebSocket y el navegador también avisa por su cuenta: consola, red.

**¿Por qué no corren en paralelo si tienen Grid?** Porque la app tiene una sola base de datos y un solo reloj: dos escenarios a la vez se pisarían los datos. Es una limitación del sistema bajo prueba, no de Selenium.

**¿La IA modifica el código sola?** No. Encuentra un reemplazo para esa corrida y lo deja registrado en `sanaciones.json`; una persona decide si actualiza el Page Object.

**¿Los defectos son reales?** Sí: DEF-01, 02 y 03 están documentados en `docs/defectos.md` desde la Parte 1 (por API), y Selenium los confirma desde la pantalla.

**¿Qué pasa si corrigen un defecto?** El escenario `@DEF` empezaría a pasar y, como está marcado como *xfail* estricto, pytest lo reporta como "pasó inesperadamente": es la señal para quitar la marca.
