# Qolqe Wallet · G5 Límites

[![Pruebas de API](https://github.com/kaloslazo/qolqe-wallet/actions/workflows/pruebas.yml/badge.svg)](https://github.com/kaloslazo/qolqe-wallet/actions/workflows/pruebas.yml)

Qolqe es una billetera digital ficticia: registro, transferencias, recargas, pago de servicios, contactos y seguridad. Acá la probamos, no la reparamos. Nos toca el módulo G5, límites y alertas de consumo, más el núcleo de la cuenta: cuánto puedes gastar al día, cuándo entra en vigencia un cambio de límite y cuándo te avisa una alerta.

```gherkin
Scenario: Una reducción cancela el aumento pendiente
  Given que inicié sesión como Diego
  And que solicité aumentar mi límite diario a S/ 1500
  When cambio mi límite diario a S/ 500
  And pasan 1500 minutos
  Then mi límite diario vigente es S/ 500.00
  And no tengo un aumento pendiente
```

Diego tiene un límite de S/ 1,000. Un aumento tarda 24 horas en aplicarse, y una reducción debería cancelarlo. La app no lo cancela: al día siguiente Diego queda con S/ 1,500. Es uno de los 9 defectos que encontramos, documentados en [`docs/defectos.md`](docs/defectos.md).

## Cómo lo probamos

| capa | herramienta | qué cubre |
|---|---|---|
| API | Playwright + playwright-bdd | 108 escenarios en Gherkin del G5 y del núcleo |
| Contrato | Schemathesis | que cada endpoint responda lo que dice su OpenAPI |
| Interfaz web | Selenium 4 + pytest-bdd | la pantalla de límites, con Page Objects, Grid, móvil y reparación de localizadores con IA |
| Rendimiento | por definir | Parte 3 |

Cada push corre la suite de API en GitHub Actions.

## Correrlo en local

Hace falta Python 3.11+ y Node 20+.

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements-pruebas.txt
npm install

npm test                           # levanta la app y corre la suite de API
```

Resultado esperado: `107 passed, 1 skipped`. El contrato, Selenium y sus modos de demo están en [`docs/pruebas.md`](docs/pruebas.md).

Para usar la app a mano: `uvicorn qolqe.main:app --reload` y abre `localhost:8000` (Swagger en `/docs`). Usuarios, datos semilla y la API de soporte para pruebas están en [`docs/qolqe.md`](docs/qolqe.md).

## El repo

```
qolqe/              la app bajo prueba (sin cambios)
features/           escenarios en Gherkin; ui/ para los de interfaz
tests/
  api-playwright/   pasos de los escenarios de API (TypeScript)
  e2e/              Selenium: pasos, Page Objects, Screenplay y soporte
  performance/      Parte 3
scripts/            contrato, demo y modos de Selenium
docs/
  qolqe.md          la app: instalación, endpoints, datos de prueba
  requisitos.md     historias de usuario y reglas de negocio
  pruebas.md        cómo correr cada suite
  defectos.md       los defectos encontrados
  informe.md        informe del proyecto
  guia-selenium.md  glosario y guion de la demo
  evidencia/        reportes de la última corrida
  expo/             diapositivas de la exposición
IA.md               declaración de uso de IA
```

## Contexto

Proyecto 2 del curso CS5383 Pruebas y Verificación de Software (UTEC, 2026-2). Grupo 5: Kalos y Gianpier. La app la entrega el curso; todos los datos son ficticios.
