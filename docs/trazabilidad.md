# Matriz de trazabilidad · G5 Límites y núcleo

Generada por `.github/scripts/trazabilidad.py` con los resultados de corrida local · 2026-11-12 18:29 (hora de Lima).

Cada escenario lleva una etiqueta `@CP-NN`, las `@HU` que cubre y sus criterios (`@CA-N-07-3` = HU-N-07 CA3). Un `xfailed` es un fallo esperado: el escenario describe el comportamiento correcto y falla por un defecto reportado en [`defectos.md`](defectos.md).

## Cobertura por historia

| HU | Historia | Funcionales | Técnicos | Criterios con caso |
|---|---|---|---|---|
| HU-N-01 | Registrarme | CP-26, CP-27, CP-28, CP-29, CP-30, CP-31, CP-32, CP-87, CP-88, CP-89 | CP-90, CP-91 | 6/6 |
| HU-N-02 | Iniciar sesión | CP-33, CP-34, CP-35, CP-36, CP-37, CP-38, CP-92, CP-93, CP-94 | CP-95, CP-96, CP-97 | 6/6 |
| HU-N-03 | Cerrar sesión | CP-39, CP-40 | CP-98, CP-99 | 2/2 |
| HU-N-04 | Consultar mi saldo y perfil | CP-41, CP-42, CP-43, CP-100, CP-101, CP-145 | CP-102, CP-103 | 3/3 |
| HU-N-05 | Editar mi perfil | CP-44, CP-45, CP-46, CP-104, CP-105, CP-106 | CP-107, CP-108, CP-109 | 3/3 |
| HU-N-06 | Cerrar mi cuenta | CP-47, CP-48, CP-110, CP-114 | CP-111, CP-112, CP-113 | 4/4 |
| HU-N-07 | Transferir a otro usuario Qolqe | CP-49, CP-50, CP-51, CP-52, CP-53, CP-86, CP-115, CP-116, CP-117, CP-118, CP-119, CP-145 | CP-120, CP-121, CP-122, CP-123 | 5/5 |
| HU-N-08 | Transferir a otro banco | CP-54, CP-55, CP-124, CP-125, CP-126 | CP-127, CP-128, CP-129 | 3/3 |
| HU-N-09 | Simular la comisión | CP-56, CP-130 | CP-131, CP-132 | 1/1 |
| HU-G5-01 | Ver mis límites | CP-01, CP-57, CP-70, CP-133 | CP-21 | 1/1 |
| HU-G5-02 | Cambiar mi límite diario | CP-02, CP-03, CP-04, CP-05, CP-06, CP-07, CP-57, CP-58, CP-59, CP-67, CP-71, CP-72, CP-73, CP-74, CP-134 | CP-22, CP-23, CP-24 | 3/3 |
| HU-G5-03 | Respetar el límite al transferir | CP-08, CP-09, CP-10, CP-53, CP-60, CP-68, CP-73, CP-75, CP-135 | CP-138, CP-139, CP-140, CP-141 | 2/2 |
| HU-G5-04 | Crear una alerta de consumo | CP-11, CP-12, CP-13, CP-14, CP-57, CP-64, CP-65, CP-74 | CP-85 | 2/2 |
| HU-G5-05 | Ver mis alertas | CP-19, CP-136 | CP-85 | 1/1 |
| HU-G5-06 | Editar, pausar o reanudar una alerta | CP-15, CP-62, CP-63, CP-76, CP-77, CP-78, CP-79, CP-137 | CP-25, CP-80, CP-85 | 2/2 |
| HU-G5-07 | Eliminar una alerta | CP-20, CP-62, CP-81 | CP-25, CP-82, CP-85 | 1/1 |
| HU-G5-08 | Recibir la notificación de la alerta | CP-16, CP-17, CP-18, CP-61, CP-69, CP-83, CP-84 | CP-142, CP-143, CP-144 | 3/3 |

## Cobertura por criterio

| Criterio | Qué pide | Casos |
|---|---|---|
| HU-N-01 CA1 | Con DNI, nombres (2 a 80 caracteres), celular, PIN y correo opcional válidos, la cuenta se crea con saldo S... | CP-26, CP-87, CP-90 |
| HU-N-01 CA2 | DNI que no cumple RN-01 (error `DNI_INVALIDO`). | CP-27, CP-91 |
| HU-N-01 CA3 | Celular que no cumple RN-02 (error `CELULAR_INVALIDO`), o que ya está registrado (error `CELULAR_REGISTRADO... | CP-28, CP-32 |
| HU-N-01 CA4 | PIN que no cumple RN-03 (error `PIN_INVALIDO`). | CP-29, CP-30 |
| HU-N-01 CA5 | Correo con formato inválido (error `CORREO_INVALIDO`) o ya usado por otra cuenta activa, sin distinguir may... | CP-31, CP-88, CP-89 |
| HU-N-01 CA6 | Se envía un SMS de bienvenida al celular registrado. | CP-26, CP-91 |
| HU-N-02 CA1 | Con credenciales correctas recibo un token válido por 30 minutos y se crea una sesión activa. | CP-33, CP-92, CP-93, CP-95 |
| HU-N-02 CA2 | Con celular inexistente o PIN incorrecto recibo un mensaje genérico, sin revelar cuál dato falló (error `CR... | CP-34, CP-97 |
| HU-N-02 CA3 | Se aplica RN-04. Al tercer intento fallido consecutivo la respuesta es (error `CUENTA_BLOQUEADA`, 423) y se... | CP-35, CP-37, CP-96 |
| HU-N-02 CA4 | Durante el bloqueo, ni siquiera el PIN correcto permite ingresar (423). Pasados los 15 minutos puedo ingres... | CP-36 |
| HU-N-02 CA5 | Una cuenta cerrada no puede iniciar sesión (error `CUENTA_CERRADA`, 401). | CP-38 |
| HU-N-02 CA6 | Si envío el identificador de un dispositivo que no está en mis dispositivos de confianza (HU-G6-05), puedo... | CP-94 |
| HU-N-03 CA1 | Al cerrar sesión, el token deja de ser válido: cualquier uso posterior responde 401. | CP-39, CP-98 |
| HU-N-03 CA2 | Cerrar sesión no afecta mis otras sesiones activas. | CP-40, CP-99 |
| HU-N-04 CA1 | Veo mi saldo disponible, la moneda (PEN) y la fecha de la última actualización. | CP-41, CP-100, CP-145 |
| HU-N-04 CA2 | Veo mi perfil: nombres, celular, correo y DNI enmascarado (solo los últimos 4 dígitos). | CP-42, CP-101, CP-103 |
| HU-N-04 CA3 | Sin token o con token vencido o inválido (error `NO_AUTENTICADO`, 401). | CP-43, CP-102 |
| HU-N-05 CA1 | Puedo modificar nombres (2 a 80 caracteres) y correo (formato válido, único entre cuentas activas sin disti... | CP-45, CP-104, CP-105, CP-107, CP-108, CP-109 |
| HU-N-05 CA2 | El DNI y el celular no se pueden modificar: si se envían, se ignoran. | CP-46, CP-106 |
| HU-N-05 CA3 | Al cambiar el correo se envía un SMS de aviso. | CP-44, CP-109 |
| HU-N-06 CA1 | Debo confirmar con mi PIN (error `PIN_INCORRECTO`). | CP-47, CP-111, CP-112, CP-113 |
| HU-N-06 CA2 | Solo puedo cerrarla con saldo exactamente S/ 0.00 (error `SALDO_PENDIENTE`). | CP-47, CP-113 |
| HU-N-06 CA3 | No puedo cerrarla si tengo solicitudes de dinero pendientes (no vencidas), enviadas o recibidas (error `SOL... | CP-47, CP-114 |
| HU-N-06 CA4 | Al cerrarla, todas mis sesiones se cierran, no puedo volver a ingresar y nadie puede transferirme (RN-07). | CP-48, CP-110 |
| HU-N-07 CA1 | Indico el celular de destino (o un contacto) y el monto; opcionalmente una descripción de hasta 60 caracteres. | CP-49, CP-115, CP-116, CP-123 |
| HU-N-07 CA2 | Se validan RN-05, RN-06, RN-07 y RN-08 (errores `MONTO_INVALIDO`, `LIMITE_DIARIO_EXCEDIDO`, `TRANSFERENCIA_... | CP-50, CP-51, CP-52, CP-120, CP-121, CP-122 |
| HU-N-07 CA3 | Si es exitosa: se debita mi saldo, se acredita al destinatario, ambos vemos el movimiento con el mismo códi... | CP-49, CP-117, CP-119, CP-122, CP-145 |
| HU-N-07 CA4 | El comprobante muestra el código de operación, el destinatario (nombre enmascarado y celular), el monto, la... | CP-118 |
| HU-N-07 CA5 | Las reglas se cumplen también bajo concurrencia: varias transferencias simultáneas no pueden superar el lím... | CP-53, CP-86 |
| HU-N-08 CA1 | Indico un CCI de 20 dígitos (error `CCI_INVALIDO`) y el monto. | CP-54, CP-127, CP-128, CP-129 |
| HU-N-08 CA2 | Se cobra la comisión de RN-09 y se aplican RN-05, RN-06 y RN-08. | CP-55, CP-124, CP-125 |
| HU-N-08 CA3 | El movimiento muestra el CCI enmascarado (solo los últimos 4 dígitos). | CP-126 |
| HU-N-09 CA1 | Antes de transferir puedo ver el monto, la comisión y el total según el tipo de transferencia, sin que se r... | CP-56, CP-130, CP-131, CP-132 |
| HU-G5-01 CA1 | Veo el límite por operación (S/ 500.00), el límite diario vigente, el aumento pendiente con su fecha de vig... | CP-01, CP-21, CP-57, CP-70, CP-133 |
| HU-G5-02 CA1 | Se aplican R-G5-01 (error `LIMITE_INVALIDO`) y R-G5-02. La respuesta indica si el cambio fue INMEDIATO o PR... | CP-02, CP-03, CP-04, CP-05, CP-06, CP-22, CP-23, CP-24, CP-57, CP-58, CP-67, CP-71, CP-72, CP-73, CP-74 |
| HU-G5-02 CA2 | Recibo un SMS con el resultado del cambio. | CP-03, CP-04, CP-57 |
| HU-G5-02 CA3 | Si una reducción deja el límite por debajo del umbral de alertas de tipo TRANSFERENCIAS o TODAS, esas alert... | CP-07, CP-59, CP-134 |
| HU-G5-03 CA1 | Toda transferencia (Qolqe, interbancaria o por solicitud aceptada) respeta RN-06 con el límite vigente al m... | CP-08, CP-09, CP-10, CP-60, CP-68, CP-73, CP-75, CP-135, CP-138, CP-139, CP-140, CP-141 |
| HU-G5-03 CA2 | La regla se cumple también con transferencias simultáneas (HU-N-07 CA5). | CP-53 |
| HU-G5-04 CA1 | Indico el tipo y el umbral (R-G5-03, R-G5-04) (errores `ALERTA_INVALIDA`, `ALERTA_DUPLICADA` 409, `LIMITE_A... | CP-11, CP-12, CP-13, CP-14, CP-57, CP-64, CP-65, CP-74, CP-85 |
| HU-G5-04 CA2 | La alerta se crea en estado ACTIVA. | CP-11, CP-57 |
| HU-G5-05 CA1 | Veo cada alerta con su tipo, umbral, estado (ACTIVA o PAUSADA), gasto de hoy de ese tipo y la fecha de su ú... | CP-19, CP-85, CP-136 |
| HU-G5-06 CA1 | Puedo cambiar el umbral (con las reglas de R-G5-03 y R-G5-04) y pausarla o reanudarla. | CP-25, CP-62, CP-63, CP-76, CP-77, CP-78, CP-79, CP-80, CP-85, CP-137 |
| HU-G5-06 CA2 | Reanudar una alerta cuyo umbral supera el límite vigente no está permitido (error `ALERTA_INVALIDA`). | CP-15 |
| HU-G5-07 CA1 | La alerta se elimina y deja de notificar. | CP-20, CP-25, CP-62, CP-81, CP-82, CP-85 |
| HU-G5-08 CA1 | Cuando una operación hace que el gasto del día (R-G5-05) alcance o supere el umbral de una alerta ACTIVA de... | CP-16, CP-61, CP-83, CP-84, CP-142, CP-143, CP-144 |
| HU-G5-08 CA2 | Cada alerta notifica como máximo una vez por día. | CP-17, CP-69 |
| HU-G5-08 CA3 | Las alertas PAUSADAS no notifican. | CP-18 |

## Casos y resultados

| HU | Caso | Nivel | Tipo | Resultado (corrida local) |
|---|---|---|---|---|
| HU-N-01 | CP-26 Registro exitoso con saldo cero, límite por defecto y SMS de bienvenida | api | funcional | passed |
| HU-N-01 | CP-27 Validación del DNI (RN-01) | api | funcional | passed 4/4 |
| HU-N-01 | CP-28 Validación del celular (RN-02) | api | funcional | passed 5/5 |
| HU-N-01 | CP-29 Validación del PIN (RN-03) | api | funcional | passed 5/5 |
| HU-N-01 | CP-30 Un PIN en secuencia descendente se rechaza (RN-03) | api | funcional | xfailed → DEF-05 |
| HU-N-01 | CP-31 Correo ya usado por otra cuenta activa, sin distinguir mayúsculas | api | funcional | passed |
| HU-N-01 | CP-32 Dos registros simultáneos con el mismo celular responden 201 y 409, nunca 500 | api | funcional | xfailed → DEF-09 |
| HU-N-01 | CP-87 Los nombres tienen de 2 a 80 caracteres | api | funcional | passed 4/4 |
| HU-N-01 | CP-88 Validación del formato del correo | api | funcional | passed 4/4 |
| HU-N-01 | CP-89 El correo de una cuenta cerrada se puede volver a usar | api | funcional | passed |
| HU-N-01 | CP-90 Un registro con cuerpo vacío, un campo faltante o un tipo inválido se rechaza y no crea la cuenta | api | técnico | passed 5/5 |
| HU-N-01 | CP-91 Un registro rechazado por una regla no crea la cuenta ni envía el SMS de bienvenida | api | técnico | passed |
| HU-N-02 | CP-33 Ingreso con credenciales correctas | api | funcional | passed |
| HU-N-02 | CP-34 Credenciales incorrectas con mensaje genérico | api | funcional | passed 2/2 |
| HU-N-02 | CP-35 Bloqueo al tercer intento fallido consecutivo | api | funcional | passed |
| HU-N-02 | CP-36 Durante el bloqueo ni el PIN correcto permite ingresar | api | funcional | passed 2/2 |
| HU-N-02 | CP-37 Un ingreso exitoso reinicia el conteo de intentos | api | funcional | xfailed → DEF-08 |
| HU-N-02 | CP-38 Una cuenta cerrada no puede iniciar sesión | api | funcional | passed |
| HU-N-02 | CP-92 Al ingresar se crea una sesión activa de 30 minutos | api | funcional | passed |
| HU-N-02 | CP-93 El token deja de valer a los 30 minutos | api | funcional | passed 2/2 |
| HU-N-02 | CP-94 Ingresar desde un dispositivo que no es de confianza envía una alerta por SMS | api | funcional | passed 2/2 |
| HU-N-02 | CP-95 Un ingreso con cuerpo vacío, un campo faltante o un tipo inválido se rechaza | api | técnico | passed 4/4 |
| HU-N-02 | CP-96 Los ingresos con datos inválidos no cuentan como intentos fallidos | api | técnico | passed |
| HU-N-02 | CP-97 La respuesta no revela si falló el celular o el PIN | api | técnico | passed |
| HU-N-03 | CP-39 Al cerrar sesión el token deja de ser válido | api | funcional | xfailed → DEF-07 |
| HU-N-03 | CP-40 Cerrar una sesión no afecta las otras sesiones activas | api | funcional | passed |
| HU-N-03 | CP-98 Sin un token válido no puedo cerrar sesión | api | técnico | passed 3/3 |
| HU-N-03 | CP-99 Un cierre de sesión rechazado no afecta mi sesión | api | técnico | passed |
| HU-N-04 | CP-41 Consulto mi saldo en soles | api | funcional | passed |
| HU-N-04 | CP-42 Mi perfil muestra el DNI enmascarado | api | funcional | passed |
| HU-N-04 | CP-43 Sin token no puedo consultar mi saldo | api | funcional | passed |
| HU-N-04 | CP-100 El saldo muestra la moneda y la fecha de su última actualización | api | funcional | passed |
| HU-N-04 | CP-101 Mi perfil muestra mis nombres, mi celular, mi correo y el DNI enmascarado | api | funcional | passed |
| HU-N-04 | CP-102 Sin un token válido no puedo ver mi saldo ni mi perfil | api | técnico | passed 5/5 |
| HU-N-04 | CP-103 El perfil no expone el DNI completo ni el PIN | api | técnico | passed |
| HU-N-04 | CP-145 Ana le transfiere a Bruno y Bruno lo ve en su cuenta | web | funcional | chrome: passed · firefox: passed |
| HU-N-05 | CP-44 Cambiar el correo envía un SMS de aviso | api | funcional | passed |
| HU-N-05 | CP-45 El correo de otra cuenta activa no se puede usar | api | funcional | passed |
| HU-N-05 | CP-46 El DNI y el celular no se pueden modificar | api | funcional | passed |
| HU-N-05 | CP-104 Los nombres del perfil tienen de 2 a 80 caracteres | api | funcional | passed 4/4 |
| HU-N-05 | CP-105 El correo del perfil tiene un formato válido y es único entre cuentas activas | api | funcional | passed 3/3 |
| HU-N-05 | CP-106 El DNI no se puede modificar | api | funcional | passed |
| HU-N-05 | CP-107 Sin un token válido no puedo editar mi perfil y no cambia | api | técnico | passed 3/3 |
| HU-N-05 | CP-108 Un campo con un tipo inválido se rechaza sin cambiar el perfil | api | técnico | passed 3/3 |
| HU-N-05 | CP-109 Un cambio rechazado no aplica ninguno de los campos ni envía el aviso | api | técnico | passed |
| HU-N-06 | CP-47 Reglas para cerrar mi cuenta | api | funcional | passed 4/4 |
| HU-N-06 | CP-48 Tras cerrar la cuenta nadie puede transferirme | api | funcional | xfailed → DEF-06 |
| HU-N-06 | CP-110 Al cerrar mi cuenta se cierran todas mis sesiones y no puedo volver a ingresar | api | funcional | passed |
| HU-N-06 | CP-111 Sin un token válido no puedo cerrar mi cuenta | api | técnico | passed 3/3 |
| HU-N-06 | CP-112 Un cierre con cuerpo vacío o un PIN de tipo inválido se rechaza y la cuenta sigue activa | api | técnico | passed 3/3 |
| HU-N-06 | CP-113 Un cierre rechazado por una regla no cierra la cuenta | api | técnico | passed 2/2 |
| HU-N-06 | CP-114 Una solicitud de dinero recibida impide cerrar la cuenta hasta que vence | api | funcional | passed 2/2 |
| HU-N-07 | CP-49 Transferencia exitosa a un usuario registrado | api | funcional | passed |
| HU-N-07 | CP-50 Validación del monto por operación (RN-05) | api | funcional | passed 5/5 |
| HU-N-07 | CP-51 Destinos no permitidos (RN-07) | api | funcional | xfailed 1/3 → DEF-06 |
| HU-N-07 | CP-52 El saldo debe cubrir el monto (RN-08) | api | funcional | passed |
| HU-N-07 | CP-53 Transferencias simultáneas no superan el límite diario | api | funcional | xfailed → DEF-11 |
| HU-N-07 | CP-86 Transferencias simultáneas no dejan el saldo negativo | api | funcional | xfailed → DEF-11 |
| HU-N-07 | CP-115 Transferir eligiendo un contacto en lugar del celular | api | funcional | passed |
| HU-N-07 | CP-116 La descripción admite hasta 60 caracteres | api | funcional | passed 2/2 |
| HU-N-07 | CP-117 La transferencia acredita al destinatario y los dos vemos el movimiento con el mismo código | api | funcional | passed |
| HU-N-07 | CP-118 El comprobante muestra el código, el destinatario enmascarado, los montos, mi nuevo saldo y la fecha | api | funcional | passed |
| HU-N-07 | CP-119 Dos transferencias en el mismo segundo tienen códigos de operación distintos | api | funcional | xfailed → DEF-12 |
| HU-N-07 | CP-120 Sin un token válido no puedo transferir y ningún saldo cambia | api | técnico | passed 3/3 |
| HU-N-07 | CP-121 Un cuerpo vacío o con un tipo inválido se rechaza indicando el campo y sin mover dinero | api | técnico | passed 5/5 |
| HU-N-07 | CP-122 Una transferencia rechazada por una regla no mueve dinero ni avisa al destinatario | api | técnico | passed |
| HU-N-07 | CP-123 No puedo transferir usando el contacto de otro usuario | api | técnico | passed |
| HU-N-07 | CP-145 Ana le transfiere a Bruno y Bruno lo ve en su cuenta | web | funcional | chrome: passed · firefox: passed |
| HU-N-08 | CP-54 Validación del CCI | api | funcional | passed 3/3 |
| HU-N-08 | CP-55 El saldo debe cubrir el monto más la comisión interbancaria | api | funcional | xfailed → DEF-04 |
| HU-N-08 | CP-124 Una transferencia a otro banco cobra la comisión de RN-09 | api | funcional | passed 3/3 |
| HU-N-08 | CP-125 El monto de una transferencia a otro banco cumple RN-05 | api | funcional | passed 5/5 |
| HU-N-08 | CP-126 El comprobante y el movimiento muestran el CCI enmascarado | api | funcional | passed |
| HU-N-08 | CP-127 Sin un token válido no puedo transferir a otro banco y mi saldo no cambia | api | técnico | passed 3/3 |
| HU-N-08 | CP-128 Un CCI o un monto de tipo inválido se rechaza indicando el campo y sin cobrar nada | api | técnico | passed 3/3 |
| HU-N-08 | CP-129 Una transferencia a otro banco sin CCI o con letras en el CCI se rechaza sin cobrar nada | api | técnico | passed 2/2 |
| HU-N-09 | CP-56 Simular la comisión sin realizar la operación (RN-09) | api | funcional | passed 5/5 |
| HU-N-09 | CP-130 Simular una transferencia entre cuentas Qolqe no cobra comisión ni mueve dinero | api | funcional | passed |
| HU-N-09 | CP-131 Sin un token válido no puedo simular la comisión | api | técnico | passed 3/3 |
| HU-N-09 | CP-132 Una simulación sin monto o con parámetros inválidos se rechaza indicando el parámetro | api | técnico | passed 3/3 |
| HU-G5-01 | CP-01 Veo mis límites con lo usado y lo disponible del día | api | funcional | passed |
| HU-G5-01 | CP-21 Sin token no puedo consultar mis límites | api | técnico | passed |
| HU-G5-01 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | funcional | chrome: passed · firefox: passed |
| HU-G5-01 | CP-70 Lo disponible hoy se recalcula al bajar el límite y nunca es negativo | api | funcional | passed 3/3 |
| HU-G5-01 | CP-133 Veo el aumento pendiente con la fecha en que entra en vigencia | api | funcional | passed |
| HU-G5-02 | CP-02 Validación del nuevo límite diario (valores límite de R-G5-01) | api | funcional | passed 8/8 |
| HU-G5-02 | CP-03 Una reducción del límite es inmediata | api | funcional | passed |
| HU-G5-02 | CP-04 Un aumento del límite queda programado para 24 horas después | api | funcional | passed |
| HU-G5-02 | CP-05 El aumento entra en vigencia exactamente a las 24 horas | api | funcional | passed 2/2 |
| HU-G5-02 | CP-06 Una reducción cancela el aumento pendiente | api | funcional | xfailed → DEF-01 |
| HU-G5-02 | CP-07 Reducir el límite por debajo del umbral pausa la alerta de transferencias | api | funcional | passed |
| HU-G5-02 | CP-22 Con un token inválido no puedo cambiar mi límite | api | técnico | passed |
| HU-G5-02 | CP-23 Un cuerpo vacío o con un tipo inválido se rechaza sin cambiar el límite | api | técnico | passed 3/3 |
| HU-G5-02 | CP-24 Un cambio rechazado por regla de negocio no tiene efecto | api | técnico | passed |
| HU-G5-02 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | funcional | chrome: passed · firefox: passed |
| HU-G5-02 | CP-58 Un aumento del límite entra en vigencia 24 horas después | web | funcional | chrome: passed · firefox: passed |
| HU-G5-02 | CP-59 Bajar el límite pausa la alerta que queda por encima | web | funcional | chrome: passed · firefox: passed |
| HU-G5-02 | CP-67 Una reducción del límite cancela el aumento programado | web | funcional | chrome: xfailed → DEF-01 · firefox: xfailed → DEF-01 |
| HU-G5-02 | CP-71 Pedir el mismo límite vigente no programa un aumento | api | funcional | passed |
| HU-G5-02 | CP-72 Un segundo aumento reemplaza al aumento pendiente | api | funcional | passed |
| HU-G5-02 | CP-73 Mientras el aumento está pendiente, al transferir rige el límite anterior | api | funcional | passed |
| HU-G5-02 | CP-74 Con un aumento pendiente, el umbral se compara con el límite vigente | api | funcional | passed |
| HU-G5-02 | CP-134 Reducir el límite pausa las alertas TODAS que quedan por encima, pero no las de otros tipos | api | funcional | passed |
| HU-G5-03 | CP-08 Transferir respetando el límite diario vigente | api | funcional | passed 3/3 |
| HU-G5-03 | CP-09 La transferencia que supera el límite diario por un céntimo se rechaza | api | funcional | passed |
| HU-G5-03 | CP-10 Las transferencias interbancarias también cuentan para el límite diario | api | funcional | xfailed → DEF-02 |
| HU-G5-03 | CP-53 Transferencias simultáneas no superan el límite diario | api | funcional | xfailed → DEF-11 |
| HU-G5-03 | CP-60 Una transferencia que supera el límite diario es rechazada | web | funcional | chrome: passed · firefox: passed |
| HU-G5-03 | CP-68 Las transferencias a otro banco cuentan para el límite diario | web | funcional | chrome: xfailed → DEF-02 · firefox: xfailed → DEF-02 |
| HU-G5-03 | CP-73 Mientras el aumento está pendiente, al transferir rige el límite anterior | api | funcional | passed |
| HU-G5-03 | CP-75 El límite diario se reinicia al día siguiente | api | funcional | passed |
| HU-G5-03 | CP-135 Aceptar una solicitud de dinero también respeta el límite diario vigente | api | funcional | passed 2/2 |
| HU-G5-03 | CP-138 Sin un token válido la transferencia se rechaza y no consume el límite | api | técnico | passed 3/3 |
| HU-G5-03 | CP-139 Un monto faltante o de tipo inválido se rechaza sin consumir el límite | api | técnico | passed 4/4 |
| HU-G5-03 | CP-140 Una transferencia rechazada por el límite no cambia ningún saldo ni lo usado hoy | api | técnico | passed |
| HU-G5-03 | CP-141 Lo que transfiere otro usuario no consume mi límite diario, aunque me lo transfiera a mí | api | técnico | passed |
| HU-G5-04 | CP-11 Validación del umbral de una alerta (valores límite de R-G5-03) | api | funcional | passed 7/7 |
| HU-G5-04 | CP-12 El umbral de TRANSFERENCIAS o TODAS no supera el límite diario vigente | api | funcional | passed 4/4 |
| HU-G5-04 | CP-13 No se permiten dos alertas con el mismo tipo y umbral | api | funcional | passed |
| HU-G5-04 | CP-14 No se puede crear una sexta alerta | api | funcional | passed |
| HU-G5-04 | CP-57 Ana baja su límite diario y crea una alerta de recargas | web | funcional | chrome: passed · firefox: passed |
| HU-G5-04 | CP-64 Validación del umbral al crear una alerta | web | funcional | chrome: passed 6/6 · firefox: passed 6/6 |
| HU-G5-04 | CP-65 El umbral de TODAS no puede superar el límite diario vigente | web | funcional | chrome: passed · firefox: passed |
| HU-G5-04 | CP-74 Con un aumento pendiente, el umbral se compara con el límite vigente | api | funcional | passed |
| HU-G5-04 | CP-85 Sin token no puedo usar mis alertas | api | técnico | passed 4/4 |
| HU-G5-05 | CP-19 Veo mis alertas con su gasto de hoy | api | funcional | passed |
| HU-G5-05 | CP-85 Sin token no puedo usar mis alertas | api | técnico | passed 4/4 |
| HU-G5-05 | CP-136 Una alerta muestra la fecha de su última notificación | api | funcional | passed |
| HU-G5-06 | CP-15 No se puede reanudar una alerta cuyo umbral supera el límite vigente | api | funcional | passed |
| HU-G5-06 | CP-25 La alerta de otro usuario responde como si no existiera | api | técnico | passed 2/2 |
| HU-G5-06 | CP-62 Pausar, reanudar y eliminar una alerta | web | funcional | chrome: passed · firefox: passed |
| HU-G5-06 | CP-63 Editar el umbral de una alerta | web | funcional | chrome: passed · firefox: passed |
| HU-G5-06 | CP-76 Validación del nuevo umbral al editar una alerta | api | funcional | passed 4/4 |
| HU-G5-06 | CP-77 El umbral editado no puede superar el límite diario vigente | api | funcional | passed |
| HU-G5-06 | CP-78 Editar el umbral a uno que ya existe se rechaza | api | funcional | passed |
| HU-G5-06 | CP-79 Reanudar una alerta pausada que cabe en el límite | api | funcional | passed |
| HU-G5-06 | CP-80 Un estado que no es ACTIVA ni PAUSADA se rechaza | api | técnico | passed |
| HU-G5-06 | CP-85 Sin token no puedo usar mis alertas | api | técnico | passed 4/4 |
| HU-G5-06 | CP-137 Pausar una alerta activa | api | funcional | passed |
| HU-G5-07 | CP-20 Una alerta eliminada deja de notificar | api | funcional | passed |
| HU-G5-07 | CP-25 La alerta de otro usuario responde como si no existiera | api | técnico | passed 2/2 |
| HU-G5-07 | CP-62 Pausar, reanudar y eliminar una alerta | web | funcional | chrome: passed · firefox: passed |
| HU-G5-07 | CP-81 Eliminar una alerta libera un cupo | api | funcional | passed |
| HU-G5-07 | CP-82 Eliminar una alerta con un identificador que no existe | api | técnico | passed 2/2 |
| HU-G5-07 | CP-85 Sin token no puedo usar mis alertas | api | técnico | passed 4/4 |
| HU-G5-08 | CP-16 La alerta notifica al alcanzar o superar el umbral | api | funcional | passed 3/3 |
| HU-G5-08 | CP-17 Cada alerta notifica como máximo una vez por día | api | funcional | xfailed → DEF-03 |
| HU-G5-08 | CP-18 Una alerta pausada no notifica | api | funcional | passed |
| HU-G5-08 | CP-61 Ana recibe un SMS al alcanzar el umbral de su alerta | web | funcional | chrome: passed · firefox: passed |
| HU-G5-08 | CP-69 Una alerta avisa como máximo una vez por día | web | funcional | chrome: xfailed → DEF-03 · firefox: xfailed → DEF-03 |
| HU-G5-08 | CP-83 Una transferencia a otro banco cuenta para la alerta por su monto, sin la comisión | api | funcional | passed |
| HU-G5-08 | CP-84 La alerta TODAS suma recargas y transferencias | api | funcional | passed |
| HU-G5-08 | CP-142 Una transferencia rechazada no cuenta para la alerta ni la dispara | api | técnico | passed 3/3 |
| HU-G5-08 | CP-143 Sin un token válido la transferencia no cuenta para la alerta | api | técnico | passed 3/3 |
| HU-G5-08 | CP-144 El gasto de otro usuario no dispara mis alertas, aunque me transfiera a mí | api | técnico | passed |
| — | CP-66 La interfaz avisa si el servidor falla al guardar el límite | web | funcional | chrome: passed · firefox: passed |
