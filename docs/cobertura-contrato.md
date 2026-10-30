# Cobertura de la API: nuestros escenarios frente a Schemathesis

Operaciones del producto probadas: **16** de 61 · con nuestros escenarios: **16** · con Schemathesis: **13** · con casos que nos faltan: **7**.

Sale de los logs de la app en cada suite: cada solicitud se lleva a su operación del OpenAPI y se cuentan los códigos HTTP. *Solo Schemathesis* son los códigos que él provocó y nuestros escenarios no.

| Operación | Nuestros escenarios | Schemathesis | Solo Schemathesis | Hallazgos | Lectura |
|---|---|---|---|---|---|
| `GET /api/limites` | 200 ×25, 401 ×4 | 200 ×3, 401 ×3 | — | — | cubierto |
| `PUT /api/limites` | 200 ×21, 401 ×1, 422 ×8 | 200 ×2, 401 ×3, 422 ×2 | — | ST205 Allow header mismatch → 405<br>ST202 Schema-valid request rejected → 422 | faltan casos: 405 |
| `GET /api/limites/alertas` | 200 ×24, 401 ×1 | 200 ×61, 401 ×3 | — | — | cubierto |
| `POST /api/limites/alertas` | 201 ×15, 401 ×1, 409 ×1, 422 ×9 | 201 ×10, 401 ×3, 409 ×1, 422 ×34 | — | ST205 Allow header mismatch → 405<br>ST202 Schema-valid request rejected → 422 | faltan casos: 405 |
| `DELETE /api/limites/alertas/{alerta_id}` | 204 ×2, 401 ×1, 404 ×2, 422 ×1 | 204 ×10, 401 ×3, 404 ×33, 422 ×12 | — | ST202 Schema-valid request rejected → 422 | hallazgo ya cubierto |
| `PUT /api/limites/alertas/{alerta_id}` | 200 ×4, 401 ×1, 404 ×1, 409 ×1, 422 ×6 | 200 ×16, 401 ×3, 404 ×19, 422 ×22 | — | ST205 Allow header mismatch → 405<br>ST202 Schema-valid request rejected → 422 | faltan casos: 405 |
| `POST /api/auth/login` | 200 ×113, 401 ×11, 423 ×5 | 200 ×3, 401 ×3, 422 ×12, 423 ×2 | 422 | ST201 Schema-violating request accepted → 423<br>ST202 Schema-valid request rejected → 423 | faltan casos: 422 |
| `POST /api/auth/logout` | 204 ×2 | — | — | — | cubierto |
| `GET /api/cuentas/me` | 200 ×3 | 200 ×3, 401 ×3 | 401 | — | faltan casos: 401 |
| `PUT /api/cuentas/me` | 200 ×2, 409 ×1 | 200 ×2, 401 ×3, 409 ×1, 422 ×2 | 401, 422 | ST205 Allow header mismatch → 405<br>ST202 Schema-valid request rejected → 422 | faltan casos: 401, 405, 422 |
| `POST /api/cuentas/me/cierre` | 204 ×2, 409 ×1, 422 ×2 | — | — | — | cubierto |
| `GET /api/cuentas/me/saldo` | 200 ×10, 401 ×1 | 200 ×3, 401 ×3 | — | — | cubierto |
| `POST /api/recargas` | 201 ×1 | — | — | — | cubierto |
| `POST /api/transferencias` | 201 ×36, 401 ×1, 404 ×1, 422 ×10 | 201 ×3, 401 ×3, 404 ×2, 422 ×17 | — | ST201 Schema-violating request accepted → 201<br>ST202 Schema-valid request rejected → 422 | hallazgo ya cubierto |
| `GET /api/transferencias/comision` | 200 ×5 | 200 ×3, 401 ×2, 422 ×2 | 401, 422 | ST202 Schema-valid request rejected → 422 | faltan casos: 401, 422 |
| `POST /api/usuarios` | 201 ×5, 409 ×3, 422 ×10, 500 ×3 | 201 ×1, 409 ×11, 422 ×50 | — | ST202 Schema-valid request rejected → 422 | hallazgo ya cubierto |
