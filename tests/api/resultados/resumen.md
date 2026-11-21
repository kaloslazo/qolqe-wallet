# Resultados de la ejecución de las pruebas de API

Playwright + playwright-bdd, `CI=true npx playwright test` (un worker, un reintento permitido, `failOnFlakyTests`).
Corrida del 20-nov-2026 sobre el código de la entrega final.

| Resultado | Cantidad |
|---|---|
| Pruebas ejecutadas | 263 (133 casos con sus ejemplos) |
| Pasaron | **263** (0 failed, 0 flaky, 0 skipped) |
| De ellas, fallos esperados (`@DEF-xx @fail`) | 16: la prueba pasa porque detecta el defecto |
| Duración | 1.4 min |

Fallos esperados por defecto (escenarios `@fail`; un escenario con varios ejemplos cuenta uno por ejemplo):

| Defecto | Pruebas | Casos |
|---|---|---|
| DEF-01 | 1 | CP-06 |
| DEF-02 | 1 | CP-10 |
| DEF-03 | 1 | CP-17 |
| DEF-04 | 1 | CP-55 |
| DEF-05 | 1 | CP-30 |
| DEF-06 | 2 | CP-48, CP-51 |
| DEF-07 | 1 | CP-39 |
| DEF-08 | 1 | CP-37 |
| DEF-09 | 1 | CP-32 |
| DEF-11 | 2 | CP-53, CP-86 |
| DEF-12 | 1 | CP-119 |
| DEF-13 | 3 | CP-161, CP-162 |

Archivos: [`junit-api.xml`](junit-api.xml) (el que sube el pipeline a Qase). El reporte HTML y la traza de cada petición se generan con
`npm run report` o `EVIDENCIA=con npm test`; el pipeline los publica en GitHub Pages.
