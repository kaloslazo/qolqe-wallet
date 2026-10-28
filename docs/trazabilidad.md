# Matriz de trazabilidad · G5 Límites y núcleo

Generada por `.github/scripts/trazabilidad.py` con los resultados de corrida local · 2026-10-27 22:08 (hora de Lima).

Cada escenario lleva una etiqueta `@CP-NN` y las `@HU` que cubre. Un `xfailed` es un fallo esperado: el escenario describe el comportamiento correcto y falla por un defecto reportado en [`defectos.md`](defectos.md).

## Cobertura por historia

| HU | Historia | Casos |
|---|---|---|
| HU-N-01 | Registrarme | CP-26, CP-27, CP-28, CP-29, CP-30, CP-31, CP-32 |
| HU-N-02 | Iniciar sesión | CP-33, CP-34, CP-35, CP-36, CP-37, CP-38 |
| HU-N-03 | Cerrar sesión | CP-39, CP-40 |
| HU-N-04 | Consultar mi saldo y perfil | CP-41, CP-42, CP-43 |
| HU-N-05 | Editar mi perfil | CP-44, CP-45, CP-46 |
| HU-N-06 | Cerrar mi cuenta | CP-47, CP-48 |
| HU-N-07 | Transferir a otro usuario Qolqe | CP-49, CP-50, CP-51, CP-52, CP-53 |
| HU-N-08 | Transferir a otro banco | CP-54, CP-55 |
| HU-N-09 | Simular la comisión | CP-56 |
| HU-G5-01 | Ver mis límites | CP-01, CP-21, CP-57 |
| HU-G5-02 | Cambiar mi límite diario | CP-02, CP-03, CP-04, CP-05, CP-06, CP-07, CP-22, CP-23, CP-24, CP-57, CP-58, CP-59, CP-67 |
| HU-G5-03 | Respetar el límite al transferir | CP-08, CP-09, CP-10, CP-60, CP-68 |
| HU-G5-04 | Crear una alerta de consumo | CP-11, CP-12, CP-13, CP-14, CP-57, CP-64, CP-65 |
| HU-G5-05 | Ver mis alertas | CP-19 |
| HU-G5-06 | Editar, pausar o reanudar una alerta | CP-15, CP-62, CP-63 |
| HU-G5-07 | Eliminar una alerta | CP-20, CP-62 |
| HU-G5-08 | Recibir la notificación de la alerta | CP-16, CP-17, CP-18, CP-61, CP-69 |

## Casos y resultados

| HU | Caso | Nivel | Resultado (corrida local) |
|---|---|---|---|
| HU-N-01 | CP-26 Registro exitoso con saldo cero, límite por defecto y SMS de bienvenida | api | passed |
| HU-N-01 | CP-27 Validación del DNI (RN-01) | api | passed 4/4 |
| HU-N-01 | CP-28 Validación del celular (RN-02) | api | passed 5/5 |
| HU-N-01 | CP-29 Validación del PIN (RN-03) | api | passed 5/5 |
| HU-N-01 | CP-30 Un PIN en secuencia descendente se rechaza (RN-03) | api | xfailed → DEF-05 |
| HU-N-01 | CP-31 Correo ya usado por otra cuenta activa, sin distinguir mayúsculas | api | passed |
| HU-N-01 | CP-32 Dos registros simultáneos con el mismo celular responden 201 y 409, nunca 500 | api | xfailed → DEF-09 |
| HU-N-02 | CP-33 Ingreso con credenciales correctas | api | passed |
| HU-N-02 | CP-34 Credenciales incorrectas con mensaje genérico | api | passed 2/2 |
| HU-N-02 | CP-35 Bloqueo al tercer intento fallido consecutivo | api | passed |
| HU-N-02 | CP-36 Durante el bloqueo ni el PIN correcto permite ingresar | api | passed 2/2 |
| HU-N-02 | CP-37 Un ingreso exitoso reinicia el conteo de intentos | api | xfailed → DEF-08 |
| HU-N-02 | CP-38 Una cuenta cerrada no puede iniciar sesión | api | passed |
| HU-N-03 | CP-39 Al cerrar sesión el token deja de ser válido | api | xfailed → DEF-07 |
| HU-N-03 | CP-40 Cerrar una sesión no afecta las otras sesiones activas | api | passed |
| HU-N-04 | CP-41 Consulto mi saldo en soles | api | passed |
| HU-N-04 | CP-42 Mi perfil muestra el DNI enmascarado | api | passed |
| HU-N-04 | CP-43 Sin token no puedo consultar mi saldo | api | passed |
| HU-N-05 | CP-44 Cambiar el correo envía un SMS de aviso | api | passed |
| HU-N-05 | CP-45 El correo de otra cuenta activa no se puede usar | api | passed |
| HU-N-05 | CP-46 El DNI y el celular no se pueden modificar | api | passed |
| HU-N-06 | CP-47 Reglas para cerrar mi cuenta | api | passed 4/4 |
| HU-N-06 | CP-48 Tras cerrar la cuenta nadie puede transferirme | api | xfailed → DEF-06 |
| HU-N-07 | CP-49 Transferencia exitosa a un usuario registrado | api | passed |
| HU-N-07 | CP-50 Validación del monto por operación (RN-05) | api | passed 5/5 |
| HU-N-07 | CP-51 Destinos no permitidos (RN-07) | api | xfailed 1/3 → DEF-06 |
| HU-N-07 | CP-52 El saldo debe cubrir el monto (RN-08) | api | passed |
| HU-N-07 | CP-53 Transferencias simultáneas no superan el límite ni dejan saldo negativo | api | skipped |
| HU-N-08 | CP-54 Validación del CCI | api | passed 3/3 |
| HU-N-08 | CP-55 El saldo debe cubrir el monto más la comisión interbancaria | api | xfailed → DEF-04 |
| HU-N-09 | CP-56 Simular la comisión sin realizar la operación (RN-09) | api | passed 5/5 |
| HU-G5-01 | CP-01 Veo mis límites con lo usado y lo disponible del día | api | passed |
| HU-G5-01 | CP-21 Sin token no puedo consultar mis límites | api | passed |
| HU-G5-01 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | chrome: passed |
| HU-G5-02 | CP-02 Validación del nuevo límite diario (valores límite de R-G5-01) | api | passed 8/8 |
| HU-G5-02 | CP-03 Una reducción del límite es inmediata | api | passed |
| HU-G5-02 | CP-04 Un aumento del límite queda programado para 24 horas después | api | passed |
| HU-G5-02 | CP-05 El aumento entra en vigencia exactamente a las 24 horas | api | passed 2/2 |
| HU-G5-02 | CP-06 Una reducción cancela el aumento pendiente | api | xfailed → DEF-01 |
| HU-G5-02 | CP-07 Reducir el límite por debajo del umbral pausa la alerta de transferencias | api | passed |
| HU-G5-02 | CP-22 Con un token inválido no puedo cambiar mi límite | api | passed |
| HU-G5-02 | CP-23 Un cuerpo vacío o con un tipo inválido se rechaza sin cambiar el límite | api | passed 3/3 |
| HU-G5-02 | CP-24 Un cambio rechazado por regla de negocio no tiene efecto | api | passed |
| HU-G5-02 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | chrome: passed |
| HU-G5-02 | CP-58 Un aumento del límite entra en vigencia 24 horas después | web | chrome: passed |
| HU-G5-02 | CP-59 Bajar el límite pausa la alerta que queda por encima | web | chrome: passed |
| HU-G5-02 | CP-67 Una reducción del límite cancela el aumento programado | web | chrome: xfailed → DEF-01 |
| HU-G5-03 | CP-08 Transferir respetando el límite diario vigente | api | passed 3/3 |
| HU-G5-03 | CP-09 La transferencia que supera el límite diario por un céntimo se rechaza | api | passed |
| HU-G5-03 | CP-10 Las transferencias interbancarias también cuentan para el límite diario | api | xfailed → DEF-02 |
| HU-G5-03 | CP-60 Una transferencia que supera el límite diario es rechazada | web | chrome: passed |
| HU-G5-03 | CP-68 Las transferencias a otro banco cuentan para el límite diario | web | chrome: xfailed → DEF-02 |
| HU-G5-04 | CP-11 Validación del umbral de una alerta (valores límite de R-G5-03) | api | passed 7/7 |
| HU-G5-04 | CP-12 El umbral de TRANSFERENCIAS o TODAS no supera el límite diario vigente | api | passed 4/4 |
| HU-G5-04 | CP-13 No se permiten dos alertas con el mismo tipo y umbral | api | passed |
| HU-G5-04 | CP-14 No se puede crear una sexta alerta | api | passed |
| HU-G5-04 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | chrome: passed |
| HU-G5-04 | CP-64 Validación del umbral al crear una alerta | web | chrome: passed 6/6 |
| HU-G5-04 | CP-65 El umbral de TODAS no puede superar el límite diario vigente | web | chrome: passed |
| HU-G5-05 | CP-19 Veo mis alertas con su gasto de hoy | api | passed |
| HU-G5-06 | CP-15 No se puede reanudar una alerta cuyo umbral supera el límite vigente | api | passed |
| HU-G5-06 | CP-62 Pausar, reanudar y eliminar una alerta | web | chrome: passed |
| HU-G5-06 | CP-63 Editar el umbral de una alerta | web | chrome: passed |
| HU-G5-07 | CP-20 Una alerta eliminada deja de notificar | api | passed |
| HU-G5-07 | CP-62 Pausar, reanudar y eliminar una alerta | web | chrome: passed |
| HU-G5-08 | CP-16 La alerta notifica al alcanzar o superar el umbral | api | passed 3/3 |
| HU-G5-08 | CP-17 Cada alerta notifica como máximo una vez por día | api | xfailed → DEF-03 |
| HU-G5-08 | CP-18 Una alerta pausada no notifica | api | passed |
| HU-G5-08 | CP-61 Ana recibe un SMS al alcanzar el umbral de su alerta | web | chrome: passed |
| HU-G5-08 | CP-69 Una alerta avisa como máximo una vez por día | web | chrome: xfailed → DEF-03 |
| — | CP-25 La alerta de otro usuario responde como si no existiera | api | passed 2/2 |
| — | CP-66 La interfaz avisa si el servidor falla al guardar el límite | web | chrome: passed |
