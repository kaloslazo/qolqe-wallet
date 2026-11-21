# Guion de la demo

Qué se muestra, en qué orden y qué se dice. Dura unos 10 minutos si los reportes pesados ya están generados (el pipeline de GitHub y la web de Selenium se dejan corridos antes de empezar). Se muestra, no se espera: lo que tarda se abre ya hecho.

**Antes de empezar:** `.venv` activo, `npm ci` hecho, app detenida (`scripts/demo.sh parar`), una corrida verde en la pestaña Actions y el sitio de Pages abierto en otra pestaña, la web corrida una vez con `scripts/selenium.sh todo --evidencia con` para tener `reportes/selenium/reporte-bdd.html`, y Docker abierto con la imagen construida (`docker build -f tests/performance/Dockerfile -t qolqe-perf .`, una vez) para la prueba en vivo de k6.

| # | Qué se muestra | Cómo | Qué se ve | Qué se dice |
|---|---|---|---|---|
| 1 | El pipeline | Pestaña Actions → la última corrida de `main` | `verificar`, `contrato` y `api` en paralelo; después `web (chrome)` y `web (firefox)`; al final `reportes` | Lo barato primero, la API junto al contrato, la web solo si lo anterior pasó. Cada job tiene su gate |
| 2 | La trazabilidad rota y arreglada | `python .github/scripts/verificar_etiquetas.py`; luego quitar un `@CP-NN` de un `.feature` y repetir | `Trazabilidad completa: 162 escenarios, 48 de 48 criterios`; tras el cambio, el archivo, la línea y la regla rota | Es el gate más barato: un escenario sin su historia o su caso no llega a ejecutarse. Se restaura con `git checkout features/` |
| 3 | Un escenario de API que detecta un defecto | `scripts/demo.sh suite @CP-32` (DEF-09, registros simultáneos) | El escenario falla *como se espera* y queda verde por `@fail` | El requisito dice «201 y 409, nunca 500»; la app responde 500. El esperado sale del requisito |
| 4 | Del fallo a la causa | `npm run diagnostico` y abrir `reportes/diagnostico/diagnostico.html` en `CP-32` | Los cuatro `POST /api/usuarios` con su código, tres 500, y `sqlite3.IntegrityError: UNIQUE constraint failed` | Aquí se ve por qué falló, no solo qué falló. Se une con el log de la app porque cada escenario empieza reiniciando los datos |
| 5 | El contrato | `npm run contrato` y abrir el HTML del gate | 4 fases en verde sobre 13 operaciones; en los hallazgos, el `curl` que reproduce cada uno | Schemathesis genera entradas que no imaginamos; el gate bloquea, los hallazgos conocidos se reportan |
| 6 | La web | Abrir `reportes/selenium/reporte-bdd.html` (ya generado) | Un escenario con cada paso de Gherkin, su captura y la consola del navegador; uno de los `@defecto` | Page Object y Screenplay; el núcleo común (registro, ingreso, transferencia) |
| 7 | El rendimiento, en vivo y ya cargado | **En vivo:** `tests/performance/correr.sh demo 100` (100 usuarios, unos 4 minutos). Usa el puerto 8000 como la app de la demo, así que se lanza al llegar a este paso, después de `scripts/demo.sh parar`; mientras corre se explica con el panel ya cargado y se vuelve a mirar el de k6 en `http://localhost:5665`. **Ya cargado:** abrir `tests/performance/resultados/carga/reporte.html` (el mismo panel de la prueba de carga de 23 minutos) y `estres/graficos.png` | En vivo: las peticiones por segundo, los usuarios virtuales y el tiempo de respuesta moviéndose. Ya cargado: p95 de 51 ms con 100 usuarios; en el estrés, el colapso con 800 y el `database is locked` | El panel en vivo es lo que k6 ve mientras corre; el ya cargado es la corrida completa, con sus umbrales. DEF-10 es el límite del sistema |
| 8 | Trazabilidad e historial | Pages: matriz de trazabilidad; luego Qase | Historia → caso → criterio, con `passed 28 · failed 2 · último fallo run #45` | Una prueba se ejecuta muchas veces: lo que importa es su historial |
| 9 | La IA propone, el tester decide | `/proponer-casos HU-N-08 web`, abrir `propuestas/ia/` y `docs/ia-checklist.md` | Escenarios con técnica y esperado citado; las preguntas sobre lo que el requisito no dice | DEF-13 salió de una propuesta; el esperado lo valida una persona, no la IA |
| 10 | Antes y después | `npm run tablero` y abrir `reportes/tablero/tablero.html` | 145 → 162 escenarios, 20 → 42 pruebas web, 12 → 13 defectos, mapeado por historia | La skill `reporte-calidad` junta mapeado, testing y defectos; cada número sale de un archivo |

## Si algo falla en vivo

- **k6 en vivo no arranca (Docker, puerto 8000 ocupado):** se muestra solo el panel ya cargado, que es la misma vista de una corrida completa. Si el puerto 8000 está ocupado por la app de la demo, `scripts/demo.sh parar` antes.
- **La app no levanta o el puerto está ocupado:** `scripts/demo.sh parar` y de nuevo. El sitio de Pages tiene todos los reportes de la última corrida.
- **Selenium no abre el navegador:** se muestra el `reporte-bdd.html` ya generado y la pestaña `web (chrome)` de Actions.
- **Internet cae:** todo lo de los pasos 2 a 7 y 10 corre en local; solo el 1 y el 8 necesitan GitHub y Qase, y se muestran con capturas del informe.

## Preguntas que conviene tener a mano

- *¿Por qué la web espera a la API?* Selenium prepara datos y sesión por la API; con la API rota, un fallo web no dice nada.
- *¿Por qué la API va junto al contrato?* Los dos prueban la misma API desde ángulos distintos y no dependen entre sí.
- *¿Dónde está el BDD?* En todo: `features/*.feature` (API, con playwright-bdd) y `features/ui/*.feature` (web, con pytest-bdd).
- *¿Por qué no mapean el log de la app en la web?* Un escenario puede abrir dos navegadores y esa unión no se validó; para la web el camino es el reporte BDD. Está en [`reporteria.md`](reporteria.md).
