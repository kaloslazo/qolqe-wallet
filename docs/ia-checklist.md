# La IA propone, el tester decide

Todo lo que la IA produce en este proyecto es una **propuesta**. Entra al repo solo después de pasar esta lista, y cada
decisión queda en [`IA.md`](../IA.md). La IA se usa en dos tareas, cada una con su skill en `.claude/skills/`:

| Tarea | Skill | Qué propone | Dónde queda |
|---|---|---|---|
| Diseñar casos | `proponer-casos` | Escenarios Gherkin (API o web) para una HU, con valores límite y esperado citado | `propuestas/ia/<HU>-<fecha>.md` |
| Reportar defectos | `reporte-defecto` | Borrador de `DEF-NN` reproducido contra la app, con severidad propuesta | `propuestas/ia/DEF-borrador-<slug>.md` |

`propuestas/ia/` está fuera de `features/` y de `docs/`: nada de lo que escribe la IA corre en el pipeline ni cuenta como
cobertura hasta que una persona lo acepta y lo mueve.

## Checklist de revisión de casos propuestos

Una persona revisa **cada** escenario. Se acepta solo si cumple todo; si no, se corrige o se descarta.

| # | Pregunta | Cómo se comprueba |
|---|---|---|
| 1 | ¿El criterio existe y el escenario lo cubre de verdad? | Abrir `docs/requisitos.md`: el `@CA-…` y la HU existen y el escenario ejercita ese criterio |
| 2 | ¿El resultado esperado sale del requisito y no del comportamiento de la app? | La fuente citada (`RN-xx`, `CA`) dice eso, palabra por palabra. Si la IA lo dedujo mirando la app, se descarta |
| 3 | ¿Hay reglas inventadas? | Ninguna regla, código de error o mensaje que no esté en el requisito. Los mensajes literales de la UI se verifican en la pantalla |
| 4 | ¿Los valores límite y los cálculos están bien? | Rehacer la cuenta a mano: montos, comisión con redondeo comercial, ventanas de 24 h o 15 min, usuarios y saldos semilla de `docs/qolqe.md` |
| 5 | ¿Es un duplicado? | Buscar en `features/` y en `docs/defectos.md`; un `@DEF` ya existente detecta ese comportamiento |
| 6 | ¿Es verificable y determinista? | Reloj fijado con `/api/pruebas/reloj`, datos reiniciados, sin esperas fijas, un solo resultado esperado |
| 7 | ¿Los pasos nuevos son implementables? | Revisar que el paso se pueda escribir con la API de soporte o con un Page Object (`data-testid`), sin XPath |
| 8 | ¿Usa datos reales? | Solo datos semilla ficticios. Nada de DNI, celulares o CCI reales en el prompt ni en el resultado |
| 9 | ¿Pasa el pipeline? | `npx bddgen`, `python .github/scripts/verificar_etiquetas.py` y la suite. Si falla un escenario aceptado, se investiga: puede ser un defecto o una propuesta mala |

## Checklist de revisión de un defecto redactado

| # | Pregunta | Cómo se comprueba |
|---|---|---|
| 1 | ¿Se reprodujo? | Repetir los pasos en una base reiniciada y obtener la misma respuesta. Una evidencia que no se puede repetir se descarta |
| 2 | ¿El esperado viene del requisito? | La regla citada dice lo que el reporte dice que debía pasar |
| 3 | ¿Es un defecto de la app o de la prueba? | Datos, reloj, localizador o aserción mal escrita no son defectos |
| 4 | ¿Es un duplicado de un `DEF` existente? | Comparar con `docs/defectos.md` |
| 5 | ¿La severidad es la correcta? | El tester la confirma con el criterio de la skill (dinero → crítica) y decide |
| 6 | ¿La evidencia es real y sin datos personales? | Las respuestas pegadas son las que devolvió la app |

## Regla para los fallos de pruebas generadas con IA

Si un escenario propuesto por la IA falla, **no se cambia la aserción para que pase**. Primero se contrasta con el
requisito: si el requisito respalda la aserción, es un hallazgo y va a `reporte-defecto`; si no, se corrige o se descarta
la propuesta. Este es el riesgo que ya identificamos en el Healer de Playwright (informe, sección 2).

## Qué se mide

En cada uso se anota en `IA.md`: cuántos casos propuso la IA, cuántos se aceptaron tal cual, cuántos se modificaron,
cuántos se descartaron y por qué, y cuántos defectos nuevos salieron. La tasa de aceptación sin cambios dice cuánto
confiar; los motivos de descarte dicen qué ajustar en la skill.
