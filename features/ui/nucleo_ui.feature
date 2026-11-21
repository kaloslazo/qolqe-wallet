# language: es
@nucleo @ui
Característica: Núcleo común desde la interfaz web
  Como cliente de Qolqe
  Quiero registrarme, ingresar y transferir desde la pantalla
  Para usar mi billetera sin depender de la API

  # Propuesta de casos con IA (skill proponer-casos): propuestas/ia/HU-N-web-2026-11-18.md. Aquí solo lo que es propio
  # de la pantalla: el mensaje que ve el usuario, el diálogo de confirmación, el comprobante y que un rechazo no mueva
  # dinero. Las particiones finas de cada regla siguen en los escenarios de API.

  Antecedentes:
    Dado que los datos de prueba están restaurados
    Y que la fecha de la app es "2026-11-10T10:00:00"

  # ---------------------------------------------------------------- HU-N-02 · HU-N-04
  @HU-N-02 @HU-N-04 @CP-146 @CA-N-02-1 @CA-N-04-1
  Escenario: Ana ingresa con su celular y PIN y ve su saldo
    Dado que Ana ingresa a Qolqe desde la pantalla de login
    Entonces su saldo disponible es "S/ 1,500.00"

  @HU-N-02 @CP-147 @CA-N-02-2
  Esquema del escenario: Las credenciales incorrectas no revelan cuál dato falló
    Dado que abre la pantalla de login
    Cuando intenta ingresar con el celular "<celular>" y el PIN "<pin>"
    Entonces ve el error de ingreso "Celular o PIN incorrectos"
    Y sigue en la pantalla de login

    Ejemplos:
      | celular   | pin  |
      | 987654321 | 1111 |
      | 900999999 | 4826 |

  @HU-N-02 @CP-148 @CA-N-02-3
  Escenario: El tercer intento fallido bloquea la cuenta 15 minutos
    Dado que abre la pantalla de login
    Cuando intenta ingresar con el celular "912345678" y el PIN "0000"
    Y intenta ingresar con el celular "912345678" y el PIN "0000"
    Y intenta ingresar con el celular "912345678" y el PIN "0000"
    Entonces ve el error de ingreso "Superaste los intentos permitidos. Tu cuenta está bloqueada hasta las 10:15."

  @HU-N-02 @CP-149 @CA-N-02-4
  Escenario: Durante el bloqueo ni el PIN correcto permite ingresar
    Dado que abre la pantalla de login
    Cuando intenta ingresar con el celular "912345678" y el PIN "0000"
    Y intenta ingresar con el celular "912345678" y el PIN "0000"
    Y intenta ingresar con el celular "912345678" y el PIN "0000"
    Y intenta ingresar con el celular "912345678" y el PIN "7391"
    Entonces ve el error de ingreso "Tu cuenta está bloqueada hasta las 10:15. Puedes solicitar un código de desbloqueo."
    Y sigue en la pantalla de login

  # ---------------------------------------------------------------- HU-N-01
  @HU-N-01 @CP-150 @CA-N-01-1
  Escenario: Una cuenta nueva se crea con saldo cero
    Dado que abre la pantalla de registro
    Cuando se registra con DNI "12345678", nombres "Luis Pérez", celular "911222333" y PIN "4826"
    Entonces ve el aviso de ingreso "Tu cuenta fue creada. Ya puedes ingresar."
    Cuando intenta ingresar con el celular "911222333" y el PIN "4826"
    Entonces su saldo disponible es "S/ 0.00"

  @HU-N-01 @CP-151 @CA-N-01-4
  Esquema del escenario: El registro rechaza un PIN que incumple RN-03
    Dado que abre la pantalla de registro
    Cuando se registra con DNI "12345678", nombres "Luis Pérez", celular "911222333" y PIN "<pin>"
    Entonces ve el error de registro "<mensaje>"

    Ejemplos:
      | pin  | mensaje                                         |
      | 1111 | El PIN no puede tener todos los dígitos iguales |
      | 1234 | El PIN no puede ser una secuencia de dígitos    |

  @HU-N-01 @CP-152 @CA-N-01-3
  Escenario: El registro rechaza un celular que ya existe
    Dado que abre la pantalla de registro
    Cuando se registra con DNI "12345678", nombres "Luis Pérez", celular "987654321" y PIN "4826"
    Entonces ve el error de registro "El celular ya está registrado"

  @HU-N-01 @CP-153 @CA-N-01-2
  Escenario: El registro rechaza un DNI que no tiene 8 dígitos
    Dado que abre la pantalla de registro
    Cuando se registra con DNI "1234", nombres "Luis Pérez", celular "911222333" y PIN "4826"
    Entonces ve el error de registro "El DNI debe tener exactamente 8 dígitos"

  # ---------------------------------------------------------------- HU-N-07 · HU-N-08 · HU-N-09
  @HU-N-07 @HU-N-09 @CP-154 @CA-N-07-4 @CA-N-09-1
  Escenario: El diálogo y el comprobante de una transferencia muestran monto, comisión y total
    Dado que Ana tiene la sesión iniciada
    Cuando pide transferir S/ 50 al celular 912345678
    Entonces el diálogo de confirmación muestra monto "S/ 50.00", comisión "S/ 0.00" y total "S/ 50.00"
    Cuando confirma la transferencia
    Entonces el comprobante muestra monto "S/ 50.00", comisión "S/ 0.00", total "S/ 50.00" y saldo "S/ 1,450.00"
    Y el comprobante muestra a "Bruno D. (912345678)" como destino y un código de operación

  @HU-N-08 @HU-N-09 @CP-155 @CA-N-08-2 @CA-N-09-1
  Esquema del escenario: El diálogo calcula la comisión interbancaria de RN-09
    Dado que Ana tiene la sesión iniciada
    Cuando pide transferir S/ <monto> a otro banco a la cuenta 00219300123456789012
    Entonces el diálogo de confirmación muestra monto "S/ <monto>.00", comisión "S/ <comision>" y total "S/ <total>"

    Ejemplos:
      | monto | comision | total  |
      | 10    | 1.00     | 11.00  |
      | 100   | 1.50     | 101.50 |
      | 400   | 5.00     | 405.00 |

  @HU-N-07 @CP-156 @CA-N-07-2
  Esquema del escenario: Una transferencia rechazada muestra el motivo y no mueve el saldo
    Dado que Ana tiene la sesión iniciada
    Cuando transfiere S/ <monto> al celular <celular>
    Entonces ve el error de transferencia "<mensaje>"
    Y su saldo disponible es "S/ 1,500.00" al volver al inicio

    Ejemplos:
      | celular   | monto | mensaje                                              |
      | 987654321 | 10    | No puedes transferirte a ti mismo                    |
      | 900999999 | 10    | El celular de destino no está registrado en Qolqe    |
      | 912345678 | 501   | El monto supera el límite por operación de S/ 500.00 |
      | 912345678 | 0     | El monto debe ser mayor a cero                       |

  @HU-N-07 @CP-157 @CA-N-07-2
  Escenario: El saldo debe cubrir el monto
    Dado que Carla tiene la sesión iniciada
    Cuando transfiere S/ 100 al celular 987654321
    Entonces ve el error de transferencia "Saldo insuficiente para realizar la operación"
    Y su saldo disponible es "S/ 50.00" al volver al inicio

  @HU-N-08 @CP-158 @CA-N-08-1
  Escenario: El CCI debe tener 20 dígitos
    Dado que Ana tiene la sesión iniciada
    Cuando transfiere S/ 10 a otro banco a la cuenta 123
    Entonces ve el error de transferencia "El CCI debe tener 20 dígitos"
