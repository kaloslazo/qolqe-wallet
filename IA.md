# Declaración de uso de IA

Usamos IA (Claude, con Claude Code) en tres tareas del proyecto, cada una con su skill en `.claude/skills/`: proponer casos
de prueba, redactar reportes de defecto y armar el tablero de calidad. En las dos primeras la IA **propone y una persona
decide**: lo que produce queda en `propuestas/ia/`, fuera de `features/` y de `docs/`, y solo entra al repo si pasa el
checklist de [`docs/ia-checklist.md`](docs/ia-checklist.md). La tercera solo reporta: lee archivos del repo y no modifica nada.

## Qué aporta y cómo se validó

| Capacidad | Dónde está | Qué aporta | Cómo validamos su resultado |
|---|---|---|---|
| Proponer casos de prueba desde los requisitos | `.claude/skills/proponer-casos/` | Amplía la cobertura de una HU con particiones, valores límite y casos técnicos. Cada esperado cita su regla (`RN-xx`, `CA`); lo que el requisito no dice queda como pregunta, no como caso | Checklist de 9 puntos por escenario: criterio y regla existen en `docs/requisitos.md`, cuentas rehechas a mano, sin duplicados ni reglas inventadas. Luego `bddgen`, `verificar_etiquetas.py` y la suite. Si un escenario aceptado falla, se contrasta con el requisito antes de tocarlo |
| Redactar reportes de defecto | `.claude/skills/reporte-defecto/` | Ahorra la redacción y la reproducción mecánica: arma el `DEF` con el formato de `docs/defectos.md` y evidencia real | El tester repite los pasos en una base reiniciada, confirma que el esperado sale del requisito, descarta duplicados y falsos positivos y decide la severidad |
| Tablero de calidad con antes y después | `.claude/skills/reporte-calidad/` y `.github/scripts/tablero.py` | Junta el mapeado (historia → escenario → criterio), el testing, los defectos, el rendimiento y lo que aportaron las otras dos skills, frente a la entrega anterior | Todo sale de archivos del repo y se recalcula con `scripts/tablero.sh`; lo que no se midió aparece como «—». Solo reporta: las acciones que sugiere las decide el tester |

## Riesgos que controlamos

- **La IA copia el comportamiento de la app como esperado.** Por eso el oráculo es siempre `docs/requisitos.md` y cada esperado lleva su fuente.
- **La IA «arregla» una aserción para que pase.** Está prohibido: un fallo se investiga contra el requisito. Puede ser un defecto.
- **Datos sensibles en el prompt (shadow AI).** Solo se usan los datos semilla ficticios de `docs/qolqe.md`.
- **Cobertura inflada.** Lo propuesto no cuenta hasta que se acepta: la etapa `verificar` del pipeline solo ve lo que está en `features/`.

## Registro de uso

Una fila por uso. «Propuso» es lo que generó la IA; los otros tres suman lo mismo.

| Fecha | Herramienta | Tarea | Propuso | Aceptamos tal cual | Corregimos | Descartamos | Qué corregimos o descartamos y por qué |
|---|---|---|---|---|---|---|---|
| 2026-11-18 | Claude (Claude Code) · skill `proponer-casos` | Casos web del núcleo común: HU-N-01, 02, 07, 08 y 09 (`propuestas/ia/HU-N-web-2026-11-18.md`) | 15 casos + 3 preguntas sobre el requisito | 15 | 0 tras la revisión del equipo | 0 | **El equipo aceptó los 15** leyendo el resumen y el Gherkin. **Antes de proponer, la IA se corrigió una vez:** probó el celular 900000001 como «destino no registrado» y la app lo aceptó (es un usuario de carga de la semilla); se usó 900999999. **Dejó 2 casos sin escribir** («Los PIN no coinciden» y «Cancelar en el diálogo»): la pantalla los tiene pero `requisitos.md` no los pide, y sin criterio no hay oráculo. **2 de los 15 son escenarios de defecto** (DEF-05 y DEF-13). Verificado el 20-nov: las 22 pruebas web repetidas con otro conductor de navegador (Playwright sobre Chromium); 20 con los textos esperados y 2 de defecto que fallan como se espera. La corrida con Selenium queda a cargo del pipeline |
| 2026-11-18 | Claude (Claude Code) · skill `reporte-defecto` | Borrador del DEF-13: comisión interbancaria con redondeo equivocado (`propuestas/ia/DEF-borrador-redondeo-comision.md`) | 1 defecto | 1 | 0 | 0 | La IA lo reprodujo contra la app (simulación y operación real) y descartó que fuera un falso positivo o un duplicado de DEF-01 a DEF-12. Propuso severidad Media y **el equipo la confirmó**. Salió de rehacer a mano los valores esperados de la propuesta anterior (RN-09: 67 × 1.5 % = 1.005, la app cobra 1.00 y el requisito pide 1.01); los 260 escenarios que ya existían no lo detectaban porque ninguno cae en un `.005` exacto |
