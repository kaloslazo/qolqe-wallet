---
name: reporte-calidad
description: Arma el tablero de calidad de Qolqe (mapeado, testing, defectos y rendimiento) comparando el estado actual con la entrega anterior (antes y después), y resume qué cambió y qué falta. Úsala al cerrar una entrega o cuando se pida «cómo estamos», un dashboard o un antes y después. Solo reporta: el tester decide qué hacer con lo que muestra.
---

# Tablero de calidad: antes y después

Tercera capacidad de IA del proyecto. Junta lo que ya producen las demás herramientas (los `.feature` y `docs/requisitos.md` para el
mapeado, los resultados de Playwright y Selenium para el testing, `docs/defectos.md`, los resúmenes de k6 y lo que dejaron
las skills `proponer-casos` y `reporte-defecto` en `propuestas/ia/`) y lo compara con una entrega anterior. **No mide nada
por su cuenta y no inventa números**: todo sale de archivos del repo y se puede recalcular.

## Entrada

- El árbol actual del repo.
- `calidad/antes.json`: la entrega anterior, medida con sus propios resultados y congelada en el repo. Si no existe o el
  tester pide otra referencia: `scripts/tablero.sh --antes <tag|commit>` (cuenta solo lo estático: escenarios, criterios,
  defectos; los resultados de las suites los pone quien tenga la corrida de ese árbol).
- Los resultados de la corrida actual, si existen: `reportes/resultados-api.json` (`npm test`) y `reportes/selenium/junit.xml`
  (`scripts/selenium.sh todo`). Si faltan, el tablero deja «—» en esa fila; **no se rellena con ceros ni se estima**.

## Pasos

1. **Ver qué hay.** Listar los resultados disponibles y su fecha. Si son viejos respecto de los últimos cambios de
   `features/`, decirlo y pedir que se vuelvan a correr antes de seguir: un tablero con resultados de ayer no sirve de evidencia.
2. **Verificar la base.** `python .github/scripts/verificar_etiquetas.py` debe terminar bien; si no, el mapeado no es confiable.
3. **Generar el tablero.** `scripts/tablero.sh` (o `npm run tablero`) escribe `reportes/tablero/tablero.html` y
   `calidad/despues.json`. En el pipeline lo hace el job `reportes` y lo publica en Pages.
4. **Leer el tablero antes de resumirlo.** Abrirlo (o leer `calidad/despues.json` y `calidad/antes.json`) y revisar:
   - *Mapeado:* historias con pocos escenarios o sin escenarios de web; criterios sin escenario de API.
   - *Testing:* pruebas que fallan sin esperarlo, flaky, omitidas; si el total de pruebas cambió sin que cambiaran los
     `.feature`, algo se rompió en la recolección.
   - *Defectos:* los nuevos frente al antes y si cada uno tiene su escenario (`@DEF-NN`).
   - *Rendimiento:* los p95 y las fallas frente a los umbrales (800 ms, 1500 ms, 1 %), y si la prueba de estrés sigue
     mostrando el colapso conocido (DEF-10).
   - *IA:* cuántas propuestas se revisaron y si las aceptadas pasaron el checklist de `docs/ia-checklist.md`.
5. **Resumir en pocas líneas**: qué mejoró (con el número del antes y del después), qué sigue igual, qué empeoró y qué no
   se pudo medir y por qué. Citar el archivo de donde sale cada cifra.
6. **Proponer los pasos que siguen, sin ejecutarlos**: una historia con pocos casos → «correr `proponer-casos` sobre
   HU-X»; un fallo inesperado → «correr `reporte-defecto` sobre CP-NN». La decisión es del tester.

## Reglas

- Una cifra que no está en un archivo del repo no se escribe.
- «Sin cambio» es un resultado válido: 48 de 48 criterios antes y después significa que la cobertura ya estaba completa,
  y el aporte está en otra fila.
- No se edita `calidad/antes.json` a mano ni se «ajusta» un resultado para que el tablero se vea mejor.
- La web solo aparece medida si hay un JUnit de una corrida real de Selenium. Si la corrida no se hizo, el resumen lo dice.
- Lo que sugiere esta skill queda como propuesta; no se acepta nada en `features/` ni en `docs/` sin que una persona lo decida.
