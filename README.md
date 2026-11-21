# Qolqe Wallet · G5 Límites

[![Pipeline](https://github.com/kaloslazo/qolqe-wallet/actions/workflows/pruebas.yml/badge.svg)](https://github.com/kaloslazo/qolqe-wallet/actions/workflows/pruebas.yml)

Qolqe es una billetera digital ficticia: registro, transferencias, recargas, pago de servicios, contactos y seguridad. Acá la probamos, no la reparamos. Nos toca el módulo G5, límites y alertas de consumo, más el núcleo de la cuenta: cuánto puedes gastar al día, cuándo entra en vigencia un cambio de límite y cuándo te avisa una alerta.

**Informe final:** [`Informe_Final_G5.pdf`](Informe_Final_G5.pdf) (fuente: [`docs/informe.md`](docs/informe.md)) · **Presentación:** [`docs/expo/entrega-final.pdf`](docs/expo/entrega-final.pdf) · **Guion de la demo:** [`docs/demo.md`](docs/demo.md)

```gherkin
Scenario: Una reducción cancela el aumento pendiente
  Given que inicié sesión como Diego
  And que solicité aumentar mi límite diario a S/ 1500
  When cambio mi límite diario a S/ 500
  And pasan 1500 minutos
  Then mi límite diario vigente es S/ 500.00
  And no tengo un aumento pendiente
```

Diego tiene un límite de S/ 1,000. Un aumento tarda 24 horas en aplicarse, y una reducción debería cancelarlo. La app no lo cancela: al día siguiente Diego queda con S/ 1,500. Es uno de los 13 defectos que encontramos, documentados en [`docs/defectos.md`](docs/defectos.md).

## Cómo lo probamos

| capa | herramienta | qué cubre |
|---|---|---|
| API | Playwright + playwright-bdd | 263 pruebas en Gherkin del G5 y del núcleo: cada criterio con casos funcionales y técnicos |
| Contrato | Schemathesis | que cada endpoint responda lo que dice su OpenAPI |
| Interfaz web | Selenium 4 + pytest-bdd | límites y el núcleo común (registro, ingreso, transferencia), con Page Object, Screenplay, Grid, móvil y reparación de localizadores con IA |
| IA | Claude Code (skills `proponer-casos`, `reporte-defecto` y `reporte-calidad`) | propone casos desde los requisitos y redacta defectos; el tester decide con un checklist ([`docs/ia-checklist.md`](docs/ia-checklist.md)) |
| Rendimiento | k6 | hora punta, campaña, estrés y resistencia sobre la API, con Qolqe en Docker ([resultados](docs/rendimiento.md)) |

Cada push y cada pull request corren el pipeline en GitHub Actions por etapas: primero, en paralelo, la verificación de la trazabilidad, el gate del contrato y la API; si pasan las tres, la interfaz en Chrome y Firefox, también en paralelo (la web prepara sus datos por la API). Al final, los reportes con un [diagnóstico por prueba](docs/reporteria.md) que lleva del fallo al request y a la traza del servidor. Los fallos esperados son los defectos ya reportados; cualquier otro fallo, o un escenario que pasa solo al reintentar, deja el pipeline en rojo. Al correrlo a mano se elige la evidencia de los reportes: con capturas, solo de los fallos o sin capturas. Desde `main`, los reportes y la [matriz de trazabilidad](docs/trazabilidad.md) se publican en [kaloslazo.github.io/qolqe-wallet](https://kaloslazo.github.io/qolqe-wallet/).

## Correrlo en local

Hace falta Python 3.11+ y Node 20+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-pruebas.txt
npm install

npm test                           # levanta la app y corre la suite de API
npm run diagnostico                # API + diagnóstico por prueba (reportes/diagnostico/)
npm run tablero                    # tablero de calidad con antes y después (reportes/tablero/)
```

Resultado esperado: `263 passed`. El contrato, Selenium y sus modos de demo están en [`docs/pruebas.md`](docs/pruebas.md).

Para usar la app a mano: `uvicorn qolqe.main:app --reload` y abre `localhost:8000` (Swagger en `/docs`). Usuarios, datos semilla y la API de soporte para pruebas están en [`docs/qolqe.md`](docs/qolqe.md).

## El repo

```
qolqe/              la app bajo prueba (sin cambios)
features/           escenarios en Gherkin con @HU, @CP y @CA; ui/ para los de interfaz
tests/
  api/              pasos de los escenarios de API (TypeScript) y resultados de su ejecución
  e2e/              Selenium: pasos, Page Objects, Screenplay y soporte
  performance/      k6: sesión, escenarios, datos, monitor y resultados
scripts/            contrato, demo y modos de Selenium
.github/
  workflows/        el pipeline
  scripts/          verificación de etiquetas, resumen del run, trazabilidad, portada de Pages y Qase
docs/
  qolqe.md          la app: instalación, endpoints, datos de prueba
  requisitos.md     historias de usuario y reglas de negocio
  pruebas.md        cómo correr cada suite y cómo funciona el pipeline
  defectos.md       los defectos encontrados
  trazabilidad.md   HU → criterio → casos → resultado, con el historial de corridas
  gestion-casos.md  comparación de herramientas de gestión de casos y la integración con Qase
  reporteria.md     reporte de cada etapa, ruta del job en rojo a la causa, y mapa de logs (cuáles se mapean y por qué)
  rendimiento.md    Parte 3: hallazgos de rendimiento, con cifras y gráficos
  informe.md        informe final del proyecto (las tres partes, con el feedback resuelto)
  ia-checklist.md   «La IA propone, el tester decide»: checklist de revisión
  guia-selenium.md  glosario de Selenium y sus modos de demo
  demo.md           guion de la demo: qué se muestra, en qué orden y qué se dice
  evidencia/        reportes de la última corrida
  expo/             diapositivas de la exposición
IA.md               declaración y registro de uso de IA
.claude/skills/     skills de IA del proyecto: proponer-casos, reporte-defecto y reporte-calidad
calidad/            instantánea de la entrega anterior (antes.json) para el tablero de antes y después
propuestas/ia/      lo que propone la IA, antes de que una persona lo acepte
```

## Contexto

Proyecto 2 del curso CS5383 Pruebas y Verificación de Software (UTEC, 2026-2). Grupo 5: Kalos y Gianpier. La app la entrega el curso; todos los datos son ficticios.
