# language: en
@nucleo
Feature: Iniciar y cerrar sesión
  Como cliente
  Quiero ingresar con mi celular y PIN
  Para acceder a mi cuenta de forma segura

  Background:
    Given que los datos de prueba están restaurados
    And que la fecha de la app es "2026-11-10T10:00:00"

  @HU-N-02 @api @CP-33 @CA-N-02-1
  Scenario: Ingreso con credenciales correctas
    When inicio sesión con el celular 987654321 y el PIN 4826
    Then recibo un token válido por 30 minutos

  @HU-N-02 @api @CP-34 @CA-N-02-2
  Scenario Outline: Credenciales incorrectas con mensaje genérico
    When inicio sesión con el celular <celular> y el PIN <pin>
    Then el resultado es "CREDENCIALES_INVALIDAS"
    And la respuesta tiene el código HTTP 401

    Examples:
      | celular   | pin  |
      | 987654321 | 1111 |
      | 900999999 | 4826 |

  @HU-N-02 @api @CP-35 @CA-N-02-3
  Scenario: Bloqueo al tercer intento fallido consecutivo
    Given que ya fallé 2 veces el PIN del celular 912345678
    When inicio sesión con el celular 912345678 y el PIN 0000
    Then el resultado es "CUENTA_BLOQUEADA"
    And la respuesta tiene el código HTTP 423
    And el celular 912345678 recibe un SMS que contiene "bloqueada"

  @HU-N-02 @api @CP-36 @CA-N-02-4
  Scenario Outline: Durante el bloqueo ni el PIN correcto permite ingresar
    Given que la cuenta del celular 912345678 quedó bloqueada
    When pasan <minutos> minutos
    And inicio sesión con el celular 912345678 y el PIN 7391
    Then el resultado es "<resultado>"

    Examples:
      | minutos | resultado        |
      | 14      | CUENTA_BLOQUEADA |
      | 15      | exitosa          |

  @HU-N-02 @api @DEF-08 @fail @CP-37 @CA-N-02-3
  Scenario: Un ingreso exitoso reinicia el conteo de intentos
    Given que ya fallé 2 veces el PIN del celular 912345678
    And que inicié sesión como Bruno
    When inicio sesión con el celular 912345678 y el PIN 0000
    Then el resultado es "CREDENCIALES_INVALIDAS"

  @HU-N-02 @api @CP-38 @CA-N-02-5
  Scenario: Una cuenta cerrada no puede iniciar sesión
    When inicio sesión con el celular 934567812 y el PIN 6029
    Then el resultado es "CUENTA_CERRADA"

  @HU-N-03 @api @DEF-07 @fail @CP-39 @CA-N-03-1
  Scenario: Al cerrar sesión el token deja de ser válido
    Given que inicié sesión como Ana
    When cierro sesión
    Then mi token anterior responde 401

  @HU-N-03 @api @CP-40 @CA-N-03-2
  Scenario: Cerrar una sesión no afecta las otras sesiones activas
    Given que inicié sesión como Ana en dos equipos
    When cierro sesión en el primer equipo
    Then el segundo equipo sigue consultando mi saldo

  @HU-N-02 @api @CP-92 @CA-N-02-1
  Scenario: Al ingresar se crea una sesión activa de 30 minutos
    Given que inicié sesión como Ana
    When consulto mis sesiones activas
    Then veo mi sesión actual, que vence a los 30 minutos

  @HU-N-02 @api @reloj @CP-93 @CA-N-02-1
  Scenario Outline: El token deja de valer a los 30 minutos
    Given que inicié sesión como Ana
    When pasan <minutos> minutos
    And consulto mi saldo sin volver a iniciar sesión
    Then la respuesta tiene el código HTTP <http>

    Examples:
      | minutos | http |
      | 29      | 200  |
      | 30      | 401  |

  # a1b2c3d4e5f60718 es el celular de ana, dispositivo de confianza de los datos semilla (HU-G6-05)
  @HU-N-02 @api @CP-94 @CA-N-02-6
  Scenario Outline: Ingresar desde un dispositivo que no es de confianza envía una alerta por SMS
    When inicio sesión con el celular 987654321, el PIN 4826 y el dispositivo <dispositivo>
    Then la respuesta tiene el código HTTP 200
    And el celular 987654321 recibe <sms> SMS que contienen "nuevo dispositivo"

    Examples:
      | dispositivo      | sms |
      | a1b2c3d4e5f60718 | 0   |
      | f0e1d2c3b4a59687 | 1   |

  @HU-N-02 @api @tecnico @CP-95 @CA-N-02-1
  Scenario Outline: Un ingreso con cuerpo vacío, un campo faltante o un tipo inválido se rechaza
    When envío POST /api/auth/login con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "<campo>"

    Examples:
      | cuerpo                                  | campo   |
      | {}                                      | celular |
      | {"celular": "912345678"}                | pin     |
      | {"celular": "912345678", "pin": 7391}   | pin     |
      | {"celular": 912345678, "pin": "7391"}   | celular |

  @HU-N-02 @api @tecnico @CP-96 @CA-N-02-3
  Scenario: Los ingresos con datos inválidos no cuentan como intentos fallidos
    Given que envié 3 veces POST /api/auth/login con el cuerpo '{"celular": "912345678", "pin": 7391}'
    When inicio sesión con el celular 912345678 y el PIN 0000
    Then la respuesta tiene el código HTTP 401
    And el resultado es "CREDENCIALES_INVALIDAS"

  @HU-N-02 @api @tecnico @CP-97 @CA-N-02-2
  Scenario: La respuesta no revela si falló el celular o el PIN
    When inicio sesión con el celular 900999999 y el PIN 4826, y luego con el celular 987654321 y el PIN 1111
    Then las dos respuestas son idénticas

  @HU-N-03 @api @tecnico @CP-98 @CA-N-03-1
  Scenario Outline: Sin un token válido no puedo cerrar sesión
    Given que inicié sesión como Ana
    When envío POST /api/auth/logout <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-03 @api @tecnico @CP-99 @CA-N-03-2
  Scenario: Un cierre de sesión rechazado no afecta mi sesión
    Given que inicié sesión como Ana
    When envío POST /api/auth/logout con un token inválido
    Then la respuesta tiene el código HTTP 401
    And mi token sigue consultando mi saldo
