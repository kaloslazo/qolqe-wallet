# Borrador de defecto · comisión interbancaria con redondeo equivocado

Redactado con la skill `reporte-defecto` (Claude). **Confirmado por el equipo el 2026-11-18 con severidad Media**; ya está en `docs/defectos.md` como DEF-13.

**Cómo apareció.** No lo detectó una prueba que fallara. Salió al rehacer a mano los valores esperados de la propuesta
`HU-N-web-2026-11-18.md` (punto 4 del checklist: «los cálculos están bien»). Los ejemplos que hoy tiene la suite (50, 66.67,
100, 333.33, 400) nunca caen en un `.005` exacto, así que ninguna prueba ejercitaba la regla de redondeo.

**Falso positivo descartado.** No es un error de la prueba, del reloj ni de los datos: es una cuenta, y el mismo resultado
sale por la simulación (`GET /api/transferencias/comision`) y por la operación real (`POST /api/transferencias`).
**Duplicado descartado.** No coincide con ningún DEF-01 a DEF-12.

## DEF-13: La comisión interbancaria no usa redondeo comercial: un monto cuyo 1.5 % termina en 0.005 cobra de menos

| Campo | Valor |
|---|---|
| Módulo / regla | Núcleo · RN-09 · HU-N-08 CA2 · HU-N-09 CA1 |
| Severidad | Media (propuesta) |
| Prioridad | Alta (HU-N-08 y HU-N-09 según `requisitos.md`: Alta y Media; se toma la de HU-N-08) |
| Entorno | Qolqe Wallet, API REST y web |
| Prueba que lo detecta | `features/nucleo_transferencias.feature` → «La comisión interbancaria usa redondeo comercial» (`@DEF-13`) y `features/ui/defectos_ui.feature` → mismo nombre (`@DEF-13`) |

**Pasos para reproducir**
1. `POST /api/pruebas/reiniciar` y `PUT /api/pruebas/reloj` con `{"ahora": "2026-11-10T10:00:00"}`.
2. Iniciar sesión como Ana (987654321 / 4826; saldo S/ 1,500.00).
3. `GET /api/transferencias/comision?monto=67&tipo=INTERBANCARIA`.
4. `POST /api/transferencias` con `{"tipo": "INTERBANCARIA", "cci": "00219300123456789012", "monto": "67"}` y luego `GET /api/cuentas/me/saldo`.

**Resultado esperado:** RN-09 dice que la comisión se redondea a 2 decimales con redondeo comercial («0.005 sube»). 1.5 % de S/ 67 es 1.005, así que la comisión es **S/ 1.01** y el total **S/ 68.01**; el saldo queda en S/ 1,431.99.

**Resultado obtenido:** comisión **S/ 1.00**, total S/ 68.00 y saldo S/ 1,432.00. Cada transferencia así cobra un céntimo de menos.

**Evidencia (respuestas reales de la app):**
```json
GET  /api/transferencias/comision?monto=67&tipo=INTERBANCARIA  → {"monto":"67.00","comision":"1.00","total":"68.00"}
POST /api/transferencias                                       → {"monto":"67.00","comision":"1.00","total":"68.00", ... ,"saldo":"1432.00"}
GET  /api/transferencias/comision?monto=267&tipo=INTERBANCARIA → {"monto":"267.00","comision":"4.00","total":"271.00"}   # esperado 4.01
```
Cálculo de referencia (Python `Decimal`): `67 × 0.015 = 1.005` → redondeo al par: `1.00`; redondeo comercial (`ROUND_HALF_UP`): `1.01`. Lo mismo con 267 (4.005 → 4.00 frente a 4.01).

**Causa probable** (solo orientativa para el equipo de desarrollo; no se modifica `qolqe/`): `qolqe/reglas/nucleo.py:59` redondea con `.quantize(Decimal("0.01"))` sin indicar el modo, y `Decimal` usa por defecto `ROUND_HALF_EVEN` (al par), no el redondeo comercial que pide RN-09.

**Impacto:** bajo en dinero por operación (1 céntimo) pero sistemático en los montos afectados, y la comisión que se muestra no es la que dice el requisito. Se propone severidad Media; el tester la confirma.

## Decisión del tester

| Confirmado como defecto | Severidad final | Quién | Fecha |
|---|---|---|---|
| Sí, confirmado | Media | Equipo del G5 | 2026-11-18 |
