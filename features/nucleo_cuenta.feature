# language: en
@nucleo
Feature: Mi cuenta: saldo, perfil y cierre
  Como cliente
  Quiero consultar y mantener mis datos
  Para controlar mi cuenta

  Background:
    Given que los datos de prueba están restaurados
    And que la fecha de la app es "2026-11-10T10:00:00"

  @HU-N-04 @api @CP-41 @CA-N-04-1
  Scenario: Consulto mi saldo en soles
    Given que inicié sesión como Ana
    When consulto mi saldo
    Then mi saldo es S/ 1500.00
    And la moneda es "PEN"

  @HU-N-04 @api @CP-42 @CA-N-04-2
  Scenario: Mi perfil muestra el DNI enmascarado
    Given que inicié sesión como Ana
    When consulto mi perfil
    Then el DNI se muestra con solo los últimos 4 dígitos

  @HU-N-04 @api @CP-43 @CA-N-04-3
  Scenario: Sin token no puedo consultar mi saldo
    When consulto el saldo sin token
    Then el resultado es "NO_AUTENTICADO"

  @HU-N-05 @api @CP-44 @CA-N-05-3
  Scenario: Cambiar el correo envía un SMS de aviso
    Given que inicié sesión como Ana
    When cambio mi correo a "ana.nueva@correo.pe"
    Then el resultado es "exitosa"
    And el celular 987654321 recibe un SMS que contiene "ana.nueva@correo.pe"

  @HU-N-05 @api @CP-45 @CA-N-05-1
  Scenario: El correo de otra cuenta activa no se puede usar
    Given que inicié sesión como Ana
    When cambio mi correo a "Bruno.Diaz@correo.pe"
    Then el resultado es "CORREO_REGISTRADO"

  @HU-N-05 @api @CP-46 @CA-N-05-2
  Scenario: El DNI y el celular no se pueden modificar
    Given que inicié sesión como Ana
    When intento cambiar mi celular a "999999999"
    Then mi perfil sigue con el celular 987654321

  @HU-N-06 @api @CP-47 @CA-N-06-1 @CA-N-06-2 @CA-N-06-3
  Scenario Outline: Reglas para cerrar mi cuenta
    Given que inicié sesión como <usuario>
    And que mi saldo es S/ <saldo>
    When cierro mi cuenta con el PIN <pin>
    Then el resultado es "<resultado>"

    Examples:
      | usuario | saldo | pin  | resultado              |
      | Carla   | 0.00  | 1111 | PIN_INCORRECTO         |
      | Carla   | 0.01  | 5917 | SALDO_PENDIENTE        |
      | Ana     | 0.00  | 4826 | SOLICITUDES_PENDIENTES |
      | Carla   | 0.00  | 5917 | exitosa                |

  @HU-N-06 @api @DEF-06 @fail @CP-48 @CA-N-06-4
  Scenario: Tras cerrar la cuenta nadie puede transferirme
    Given que inicié sesión como Carla
    And que mi saldo es S/ 0.00
    And que cerré mi cuenta con el PIN 5917
    And que inicié sesión como Ana
    When transfiero S/ 10.00 al celular 956781234
    Then el resultado es "DESTINO_INACTIVO"

  # antes de las 10:00: una hora posterior correría los datos semilla del escenario siguiente
  @HU-N-04 @api @CP-100 @CA-N-04-1
  Scenario: El saldo muestra la moneda y la fecha de su última actualización
    Given que la fecha de la app es "2026-11-10T08:15:00"
    And que inicié sesión como Ana
    And que ya transferí S/ 100.00 hoy al celular 912345678
    When consulto mi saldo
    Then mi saldo es S/ 1400.00
    And la moneda es "PEN"
    And mi saldo se actualizó el "2026-11-10T08:15"

  @HU-N-04 @api @CP-101 @CA-N-04-2
  Scenario: Mi perfil muestra mis nombres, mi celular, mi correo y el DNI enmascarado
    Given que inicié sesión como Ana
    When consulto mi perfil
    Then mi perfil muestra los nombres "Ana Torres Quispe", el celular 987654321 y el correo "ana.torres@correo.pe"
    And el DNI se muestra con solo los últimos 4 dígitos

  @HU-N-04 @api @tecnico @CP-102 @CA-N-04-3
  Scenario Outline: Sin un token válido no puedo ver mi saldo ni mi perfil
    Given que inicié sesión como Ana
    When envío GET <ruta> <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

    Examples:
      | ruta                  | acceso                |
      | /api/cuentas/me/saldo | con un token inválido |
      | /api/cuentas/me/saldo | con mi token vencido  |
      | /api/cuentas/me       | sin token             |
      | /api/cuentas/me       | con un token inválido |
      | /api/cuentas/me       | con mi token vencido  |

  @HU-N-04 @api @tecnico @CP-103 @CA-N-04-2
  Scenario: El perfil no expone el DNI completo ni el PIN
    Given que inicié sesión como Ana
    When consulto mi perfil
    Then el perfil no muestra el DNI "45678912" ni el PIN

  @HU-N-05 @api @CP-104 @CA-N-05-1
  Scenario Outline: Los nombres del perfil tienen de 2 a 80 caracteres
    Given que inicié sesión como Ana
    When cambio mis nombres por unos de <largo> caracteres
    Then el resultado es "<resultado>"

    Examples:
      | largo | resultado       |
      | 1     | PERFIL_INVALIDO |
      | 2     | exitosa         |
      | 80    | exitosa         |
      | 81    | PERFIL_INVALIDO |

  @HU-N-05 @api @CP-105 @CA-N-05-1
  Scenario Outline: El correo del perfil tiene un formato válido y es único entre cuentas activas
    Given que inicié sesión como Ana
    When cambio mi correo a "<correo>"
    Then el resultado es "<resultado>"

    Examples:
      | correo                 | resultado       |
      | ana@correo             | CORREO_INVALIDO |
      | ana.correo.pe          | CORREO_INVALIDO |
      | fabian.rojas@correo.pe | exitosa         |

  @HU-N-05 @api @CP-106 @CA-N-05-2
  Scenario: El DNI no se puede modificar
    Given que inicié sesión como Ana
    When intento cambiar mi DNI a "11111111"
    Then el resultado es "exitosa"
    And mi perfil sigue con el DNI "****8912"

  @HU-N-05 @api @tecnico @CP-107 @CA-N-05-1
  Scenario Outline: Sin un token válido no puedo editar mi perfil y no cambia
    Given que inicié sesión como Ana
    When envío PUT /api/cuentas/me con el cuerpo '{"correo": "intruso@correo.pe"}' <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"
    And mi perfil sigue con el correo "ana.torres@correo.pe"

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-05 @api @tecnico @CP-108 @CA-N-05-1
  Scenario Outline: Un campo con un tipo inválido se rechaza sin cambiar el perfil
    Given que inicié sesión como Ana
    When envío PUT /api/cuentas/me con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "<campo>"
    And mi perfil sigue con los nombres "Ana Torres Quispe"
    And mi perfil sigue con el correo "ana.torres@correo.pe"

    Examples:
      | cuerpo                                        | campo   |
      | {"nombres": 123}                              | nombres |
      | {"correo": 123}                               | correo  |
      | {"nombres": ["Ana"], "correo": "a@correo.pe"} | nombres |

  @HU-N-05 @api @tecnico @CP-109 @CA-N-05-1 @CA-N-05-3
  Scenario: Un cambio rechazado no aplica ninguno de los campos ni envía el aviso
    Given que inicié sesión como Ana
    When envío PUT /api/cuentas/me con el cuerpo '{"nombres": "A", "correo": "ana.nueva@correo.pe"}'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "PERFIL_INVALIDO"
    And mi perfil sigue con el correo "ana.torres@correo.pe"
    And el celular 987654321 no recibe un SMS que contiene "ana.nueva@correo.pe"

  @HU-N-06 @api @CP-110 @CA-N-06-4
  Scenario: Al cerrar mi cuenta se cierran todas mis sesiones y no puedo volver a ingresar
    Given que inicié sesión como Carla en dos equipos
    And que mi saldo es S/ 0.00
    When cierro mi cuenta con el PIN 5917
    Then el resultado es "exitosa"
    And ninguno de mis dos equipos puede consultar mi saldo
    And al volver a iniciar sesión el resultado es "CUENTA_CERRADA"

  @HU-N-06 @api @tecnico @CP-111 @CA-N-06-1
  Scenario Outline: Sin un token válido no puedo cerrar mi cuenta
    Given que inicié sesión como Carla
    And que mi saldo es S/ 0.00
    When envío POST /api/cuentas/me/cierre con el cuerpo '{"pin": "5917"}' <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"
    And mi cuenta sigue ACTIVA

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-06 @api @tecnico @CP-112 @CA-N-06-1
  Scenario Outline: Un cierre con cuerpo vacío o un PIN de tipo inválido se rechaza y la cuenta sigue activa
    Given que inicié sesión como Carla
    And que mi saldo es S/ 0.00
    When envío POST /api/cuentas/me/cierre con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "pin"
    And mi cuenta sigue ACTIVA

    Examples:
      | cuerpo        |
      | {}            |
      | {"pin": 5917} |
      | {"pin": null} |

  @HU-N-06 @api @tecnico @CP-113 @CA-N-06-1 @CA-N-06-2
  Scenario Outline: Un cierre rechazado por una regla no cierra la cuenta
    Given que inicié sesión como Carla
    And que mi saldo es S/ <saldo>
    When cierro mi cuenta con el PIN <pin>
    Then la respuesta tiene el código HTTP 422
    And el resultado es "<resultado>"
    And mi cuenta sigue ACTIVA

    Examples:
      | saldo | pin  | resultado       |
      | 0.00  | 1111 | PIN_INCORRECTO  |
      | 0.01  | 5917 | SALDO_PENDIENTE |

  # va al final: adelanta el reloj 48 horas
  @HU-N-06 @api @reloj @CP-114 @CA-N-06-3
  Scenario Outline: Una solicitud de dinero recibida impide cerrar la cuenta hasta que vence
    Given que inicié sesión como Carla
    And que mi saldo es S/ 0.00
    And que Ana me solicitó S/ 20.00
    When pasan <minutos> minutos
    And cierro mi cuenta con el PIN 5917
    Then el resultado es "<resultado>"

    Examples:
      | minutos | resultado              |
      | 2879    | SOLICITUDES_PENDIENTES |
      | 2880    | exitosa                |
