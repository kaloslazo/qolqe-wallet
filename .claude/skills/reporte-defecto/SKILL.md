---
name: reporte-defecto
description: Redacta el borrador de un reporte de defecto de Qolqe (formato de docs/defectos.md) a partir de un fallo de Playwright, Selenium o k6, reproduciéndolo contra la app antes de escribir. Úsala cuando un escenario falle de forma inesperada o se sospeche un defecto. Solo redacta: el tester confirma.
---

# Redactar un reporte de defecto

Segunda capacidad de IA del proyecto: pasar de «el escenario falló» a un reporte reproducible con el mismo formato que
`docs/defectos.md`. La IA ahorra la redacción y la reproducción mecánica; **la confirmación del defecto y su
severidad la decide el tester**.

## Entrada

Una de estas: la salida de un escenario fallido (`reportes/`, `docs/evidencia/`), el `resumen.md` de una prueba de k6,
o la descripción de lo que se vio. Con el nombre del escenario o el `@CP-NN`.

## Pasos

1. **Entender qué se esperaba.** Leer el escenario (`features/**`) y el criterio o regla que cita en `docs/requisitos.md`.
   El esperado sale del requisito. Si el requisito no lo dice, no hay defecto que reportar: hay una pregunta para el equipo.

2. **Descartar que sea un falso positivo de la prueba.** Revisar si el paso falla por datos (el reloj no estaba fijo, la
   BD no se reinició, un usuario sin el saldo semilla), por un localizador roto o por una expectativa mal escrita. Si es
   eso, decirlo y no armar el reporte.

3. **Revisar duplicados** contra `docs/defectos.md` (DEF-01 a DEF-12 y los que se agreguen) y contra los escenarios
   `@fail` / `@defecto`. Si ya está, indicar el `DEF-NN` y parar.

4. **Reproducir de verdad.** Levantar la app (`uvicorn qolqe.main:app --port 8000`), reiniciar con
   `POST /api/pruebas/reiniciar`, fijar el reloj con `PUT /api/pruebas/reloj` y ejecutar los pasos con `curl`. Pegar las
   respuestas **reales** como evidencia. Si no se logra reproducir, el borrador lo dice y no inventa un resultado.
   Para rendimiento, citar el `resumen.md` y las cifras de `tests/performance/resultados/<prueba>/`.

5. **Proponer severidad con el criterio de abajo**, indicando por qué. El tester la confirma o la cambia.

6. **Escribir el borrador** en `propuestas/ia/DEF-borrador-<slug>.md`, con este formato (el mismo de `docs/defectos.md`):

````markdown
## DEF-??: <título en una frase, lo que falla y no cómo se arregla>

| Campo | Valor |
|---|---|
| Módulo / regla | <módulo · HU-xx · CA / RN-xx> |
| Severidad | <propuesta> |
| Prioridad | <la de la HU en requisitos.md> |
| Entorno | Qolqe Wallet, <API REST / Chrome / k6> |
| Prueba que lo detecta | `<archivo.feature>` → escenario «<nombre>» (`@DEF-??`) |

**Pasos para reproducir**
1. ...

**Resultado esperado:** <con la regla citada>

**Resultado obtenido:** <lo observado>

**Evidencia:** <respuestas reales, código HTTP, captura o gráfico>
````

## Criterio de severidad (el que ya usa `docs/defectos.md`)

| Severidad | Cuándo |
|---|---|
| Crítica | Se viola una regla de dinero: saldo negativo, límite superado, transferencia a cuenta cerrada |
| Alta | Falla de seguridad o de una regla de la HU que no mueve dinero directamente (token, límite pendiente) o caída del servicio |
| Media | Una regla de negocio se incumple con efecto acotado (alerta repetida, PIN débil, conteo de intentos) |
| Baja | Presentación o comodidad |

## Lo que la IA no hace

- No cambia `docs/defectos.md` ni las etiquetas de los `.feature`: el tester asigna el `DEF-NN`, lo mueve a
  `docs/defectos.md` y etiqueta el escenario (`@DEF-NN @fail` en API, `@DEF-NN @defecto` en web). La etapa `verificar`
  del pipeline exige que ese `DEF` exista.
- No ajusta una aserción para que la prueba pase: si el escenario detecta algo, es información.
- No pega datos reales ni credenciales en la evidencia.
