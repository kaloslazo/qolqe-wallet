---
name: proponer-casos
description: Propone escenarios Gherkin (API o web) para una historia de usuario de Qolqe a partir de docs/requisitos.md, con valores límite, resultado esperado concreto y su fuente. Úsala cuando el equipo quiera ampliar la cobertura de una HU o de un criterio sin caso. Solo propone: el tester decide.
---

# Proponer casos de prueba desde los requisitos

Esta skill es la capacidad de IA del proyecto para **diseñar casos**. Funciona como un RAG sobre el propio repo: la IA no
inventa reglas, las lee de `docs/requisitos.md` y cita de dónde sale cada resultado esperado. Lo que produce son
**propuestas**; ninguna entra a `features/` sin que una persona la revise con `docs/ia-checklist.md`.

## Entrada

Una HU (`HU-N-07`, `HU-G5-03`...) o un criterio (`HU-N-02 CA6`) y el nivel: `api` o `web`. Si falta el nivel, usar el que
indica la tabla de alcance de `docs/informe.md` (sección 1).

## Pasos

1. **Leer las fuentes, en este orden** y no usar nada más como oráculo:
   - `docs/requisitos.md`: la HU, sus criterios `CA`, y las reglas `RN-xx` / `R-Gx-xx` que cita.
   - `docs/defectos.md`: los defectos ya conocidos de esa HU (para no re-proponer lo que ya detecta un `@DEF`).
   - `features/**/*.feature`: los escenarios que ya existen para esa HU. Sacar de ahí el número más alto de `@CP-NN`
     (`grep -rhoE "@CP-[0-9]+" features | sort -t- -k2 -n | tail -1`) y qué criterios ya tienen caso.
   - `docs/qolqe.md`: usuarios y datos semilla. Usar **solo** esos; no inventar usuarios, celulares ni saldos.
   - Los pasos ya definidos (`tests/api/pasos*.ts` para API; `tests/e2e/test_limites_ui.py` y
     `tests/e2e/pages/` para web). Reutilizar sus frases tal cual.

2. **Diseñar con técnica explícita**, una por escenario: partición de equivalencia, valores límite (n−1, n, n+1),
   tabla de decisión, transición de estado. Para API, incluir los casos técnicos que corresponden a la interfaz de la HU:
   sin token o token inválido (401 `NO_AUTENTICADO`), cuerpo vacío o campo faltante (422), ausencia de efecto tras un
   rechazo (saldo, límite o perfil no cambian) y propiedad de los datos (recurso de otro usuario → 404).

3. **El resultado esperado sale del requisito, nunca del comportamiento de la app.** Cada esperado lleva su fuente
   textual (`RN-05`, `HU-N-07 CA2`). Si el requisito es ambiguo o no dice qué debe pasar, **no escribas el escenario**:
   anótalo en «Preguntas sobre el requisito».

4. **Autoverificación antes de entregar** (lo que la IA sí puede comprobar sola):
   - Cada `@CA-<mod>-<hu>-<n>` existe en `docs/requisitos.md` y es de una HU del escenario.
   - Cada valor límite está bien calculado (rehacer la cuenta: montos, comisión con redondeo comercial, 24 h = 1440 min).
   - Ningún escenario repite uno existente ni el de un `@DEF` conocido.
   - Los pasos que no existen aún están marcados como **paso nuevo**.

5. **Escribir la propuesta** en `propuestas/ia/<HU>-<AAAA-MM-DD>.md` (crear la carpeta si falta). **No tocar `features/`**
   ni `docs/`. La carpeta `propuestas/ia/` queda fuera de `bddgen`, de pytest y del pipeline a propósito.

## Formato de la propuesta

````markdown
# Propuesta de casos · <HU> · <fecha>
Fuentes leídas: <lista de archivos y líneas>
Siguiente @CP libre: CP-<n>

## Resumen
| # | Criterio | Técnica | Nivel | Esperado | Fuente del esperado | Pasos nuevos |
|---|---|---|---|---|---|---|

## Gherkin
```gherkin
@HU-N-07 @api @CP-?? @CA-N-07-2
Scenario: ...
```

## Preguntas sobre el requisito
- <ambigüedad que impide escribir un caso>

## Decisión del tester
| # | Aceptado / Modificado / Descartado | Por qué | Quién | Fecha |
|---|---|---|---|---|
````

Los `@CP-??` son provisionales: el tester los numera al aceptar.

## Lo que la IA no hace

- No ejecuta ni «arregla» escenarios para que pasen. Si un escenario aceptado falla, puede ser un defecto: lo decide el
  tester contra el requisito, y el defecto se documenta con la skill `reporte-defecto`.
- No usa datos reales de personas (DNI, celulares, CCI). Todo es dato semilla ficticio.
- No decide la prioridad ni el nivel final: propone.

## Cuando el tester acepta un escenario

1. Pasarlo a `features/` (o `features/ui/`) con su `@CP` definitivo.
2. Implementar los **pasos nuevos** (TypeScript en `tests/api/`, Python en `tests/e2e/`).
3. `npx bddgen` y `python .github/scripts/verificar_etiquetas.py` deben pasar; luego correr la suite.
4. Registrar en `IA.md` qué se aceptó, qué se corrigió y qué se descartó, con el porqué.
