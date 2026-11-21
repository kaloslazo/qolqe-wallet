# Gestión de casos de prueba

La retroalimentación de la Parte 2 pidió dos cosas: que la trazabilidad tome en cuenta que el pipeline corre muchas veces, y considerar una herramienta de gestión de casos para la entrega final. Lo primero ya está en el pipeline (historial de las últimas 30 corridas en la matriz de [`trazabilidad.md`](trazabilidad.md)). Este documento cubre lo segundo: qué herramientas revisamos, cuál elegimos y cómo se conecta.

Precios y planes revisados el 12 de noviembre de 2026 en las páginas oficiales (fuentes al final).

## Qué necesitamos

1. **Gratis sin vencimiento.** Un trial de 14 o 30 días se acaba antes de que el curso termine.
2. **Recibir resultados desde GitHub Actions**: reporter de Playwright, plugin de pytest o importación de JUnit XML (lo producen las tres suites: Playwright, Selenium y Schemathesis).
3. **Historial por caso**: cada corrida del pipeline queda como una corrida en la herramienta.
4. **Defectos ligados al resultado** que los detecta.
5. **Que la profesora pueda entrar** a verlo.

## Comparación

| Herramienta | Modelo | Plan gratis | Desde CI | Historial | Defectos | Para nosotros |
|---|---|---|---|---|---|---|
| **Qase** | SaaS | Sí, sin vencimiento: 4 usuarios, 2 proyectos, 30 días de datos, 5000 resultados al mes por API | Reporter de Playwright, plugin de pytest con pytest-bdd, CLI `qasectl` que sube JUnit | Sí (30 días en el plan gratis) | Nativos, incluidos en el plan gratis | **Elegida** |
| Testomat.io | SaaS | Sí: 2 usuarios, sin lectores, historial de 30 corridas | El mejor soporte de Gherkin: importa los `.feature` y les pone ID | Sí | GitHub y Jira solo en el plan pago | Segunda opción: la profesora no podría entrar |
| BrowserStack Test Management | SaaS | Sí: 5 usuarios, 30 días de historial | Importar JUnit está en el plan pago | 30 días | Jira | Lo esencial para CI no está en el plan gratis |
| Kiwi TCMS | Open source, se instala | Gratis | Plugins de JUnit XML y pytest | Completo, sin límite | GitHub Issues | Hay que mantener un servidor público con HTTPS para que Actions llegue |
| TestLink | Open source, se instala | Gratis | Sin reporters oficiales | Sí | Sí | Sin versiones desde 2020 |
| Xray (Jira) | App de Jira | No (US$ 10/mes hasta 10 usuarios) | Importa JUnit y Cucumber | Sí | La cadena más completa: historia → prueba → ejecución → bug | Pago |
| Zephyr (Jira) | App de Jira | No (US$ 10/mes) | Importa JUnit y Cucumber | Sí | Jira | Pago |
| TestRail | SaaS | No, trial de 30 días | CLI `trcli` con JUnit | Sí | Sí | Pago |
| Testmo | SaaS | No, solo trial | CLI con JUnit | Sí | Sí | Pago |
| Allure TestOps | SaaS | No, solo trial | Allure para Playwright y pytest-bdd | Sí | Sí | Pago |
| TestQuality, Tuskr, Testiny, TestFiesta | SaaS | Sí, pero sin API o sin automatización en el plan gratis (Tuskr: 0 llamadas por hora; TestFiesta: 1 usuario) | Solo pagando | — | — | No sirven para CI gratis |

## Por qué Qase

- Es la única que cumple los cinco puntos sin pagar: plan gratis sin vencimiento, piezas oficiales para nuestras tres suites, historial por corrida, defectos dentro de la herramienta y 4 usuarios (los dos y la profesora).
- Sube resultados con una sola pieza (`qasectl`), desde el job que ya junta todos los reportes, sin cambiar las pruebas.

**Lo que asumimos:**

- Guarda 30 días de datos. Los reportes de GitHub Pages y el historial de [`trazabilidad.md`](trazabilidad.md) siguen siendo el registro permanente, y antes de cada entrega se exporta la corrida a PDF.
- El plan gratis no tiene módulo de requisitos. Las HU quedan como etiquetas y la matriz HU → criterio → caso la sigue generando nuestro script.
- Admite 5000 resultados al mes. Cada pipeline sube 359 (263 de API, 14 del gate del contrato y 41 por navegador), así que solo se sube desde `main` y el pipeline no corre con cambios de documentación: alcanza para unas 13 corridas al mes.

## Cómo se conecta

```
pipeline en main ─▶ reportes ─┬─▶ GitHub Pages (portada, trazabilidad, historial)
                              └─▶ Qase: una corrida por pipeline con los JUnit de api, contrato y web
```

[`.github/scripts/qase.sh`](../.github/scripts/qase.sh) baja `qasectl` (versión fija) y sigue tres pasos:

1. Crea una corrida titulada `Pipeline #N · <commit>`, con el enlace al run de Actions.
2. Sube cada JUnit con su suite: `API`, `Contrato`, `Web chrome` y `Web firefox`.
3. Cierra la corrida.

Qase empareja cada resultado con su caso por título y suite. Así, cada escenario acumula su historial de corridas y, desde un resultado fallido, se crea el defecto con su `DEF-NN`.

El paso solo corre si existe el secreto. Sin él, el pipeline funciona igual. Si Qase no responde, el reporte en Pages se publica de todas formas (`continue-on-error`).

## Para activarlo

Lo hace una persona, una sola vez:

1. Crear la cuenta gratis en [app.qase.io](https://app.qase.io) y un proyecto con código `QOLQE`. Invitar al compañero y a la profesora.
2. Crear un token de API en [app.qase.io/user/api/token](https://app.qase.io/user/api/token). Se ve una sola vez.
3. Guardarlo como secreto del repo:

   ```bash
   gh secret set QASE_TESTOPS_API_TOKEN -R kaloslazo/qolqe-wallet
   ```

4. Si el proyecto tiene otro código, guardarlo como variable: `gh variable set QASE_PROYECTO -R kaloslazo/qolqe-wallet`.
5. Correr el pipeline a mano (Actions › Pipeline › *Run workflow*) y revisar la corrida en Qase.

Activado el 12 de noviembre de 2026. La primera corrida, *Pipeline #35 · b900935*, creó 312 casos en cuatro suites (API, Contrato, Web chrome y Web firefox): 299 passed y 6 skipped, que son los 3 defectos de interfaz conocidos en cada navegador. Los `@fail` de Playwright llegan como passed, igual que en el reporte de Playwright: pasan mientras el defecto siga ahí.

## Fuentes

- Precios: [qase.io/pricing](https://qase.io/pricing), [testomat.io/pricing](https://testomat.io/pricing/), [browserstack.com/pricing?product=test-management](https://www.browserstack.com/pricing?product=test-management), [kiwitcms.org](https://kiwitcms.org/), [testrail.com/pricing](https://www.testrail.com/pricing/), [testmo.com/pricing](https://www.testmo.com/pricing/), [qameta.io/pricing](https://qameta.io/pricing/), [testquality.com/pricing](https://www.testquality.com/pricing), [tuskr.app/pricing](https://tuskr.app/pricing), [testiny.io/pricing](https://www.testiny.io/pricing/), [testfiesta.com/pricing](https://www.testfiesta.com/pricing), [Xray y Zephyr](https://www.getxray.app/xray-vs-zephyr-comparison-pricing), [TestLink en GitHub](https://github.com/TestLinkOpenSourceTRMS/testlink-code)
- Integración: [qasectl](https://github.com/qase-tms/qasectl) (comandos en `docs/command.md`), [reporter de Playwright](https://github.com/qase-tms/qase-javascript/tree/main/qase-playwright), [qase-pytest](https://github.com/qase-tms/qase-python/tree/main/qase-pytest), [API de Qase](https://docs.qase.io/en/articles/6664958-qase-api)
