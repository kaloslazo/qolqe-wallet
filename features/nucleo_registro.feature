# language: en
@nucleo
Feature: Registrarme
  Como visitante
  Quiero crear una cuenta con mi DNI y celular
  Para usar la billetera

  Background:
    Given que los datos de prueba están restaurados
    And que la fecha de la app es "2026-11-10T10:00:00"

  @HU-N-01 @api @CP-26 @CA-N-01-1 @CA-N-01-6
  Scenario: Registro exitoso con saldo cero, límite por defecto y SMS de bienvenida
    When me registro con DNI "45678912", celular "987000111" y PIN "4826"
    Then la respuesta tiene el código HTTP 201
    And el celular 987000111 recibe un SMS que contiene "Bienvenido a Qolqe"
    And al iniciar sesión con el celular 987000111 y el PIN 4826 mi saldo es S/ 0.00
    And mi límite diario vigente es S/ 2000.00

  @HU-N-01 @api @CP-27 @CA-N-01-2
  Scenario Outline: Validación del DNI (RN-01)
    When me registro con DNI "<dni>", celular "987000111" y PIN "4826"
    Then el resultado es "<resultado>"

    Examples:
      | dni       | resultado    |
      | 1234567   | DNI_INVALIDO |
      | 12345678  | exitosa      |
      | 123456789 | DNI_INVALIDO |
      | 1234567A  | DNI_INVALIDO |

  @HU-N-01 @api @CP-28 @CA-N-01-3
  Scenario Outline: Validación del celular (RN-02)
    When me registro con DNI "45678912", celular "<celular>" y PIN "4826"
    Then el resultado es "<resultado>"

    Examples:
      | celular    | resultado          |
      | 98700011   | CELULAR_INVALIDO   |
      | 9870001112 | CELULAR_INVALIDO   |
      | 887000111  | CELULAR_INVALIDO   |
      | 987654321  | CELULAR_REGISTRADO |
      | 934567812  | CELULAR_REGISTRADO |

  @HU-N-01 @api @CP-29 @CA-N-01-4
  Scenario Outline: Validación del PIN (RN-03)
    When me registro con DNI "45678912", celular "987000111" y PIN "<pin>"
    Then el resultado es "<resultado>"

    Examples:
      | pin   | resultado   |
      | 482   | PIN_INVALIDO |
      | 48260 | PIN_INVALIDO |
      | 1111  | PIN_INVALIDO |
      | 1234  | PIN_INVALIDO |
      | 2580  | exitosa      |

  @HU-N-01 @api @DEF-05 @fail @CP-30 @CA-N-01-4
  Scenario: Un PIN en secuencia descendente se rechaza (RN-03)
    When me registro con DNI "45678912", celular "987000111" y PIN "4321"
    Then el resultado es "PIN_INVALIDO"

  @HU-N-01 @api @CP-31 @CA-N-01-5
  Scenario: Correo ya usado por otra cuenta activa, sin distinguir mayúsculas
    When me registro con DNI "45678912", celular "987000111", PIN "4826" y correo "ANA.TORRES@correo.pe"
    Then el resultado es "CORREO_REGISTRADO"

  @HU-N-01 @api @DEF-09 @fail @CP-32 @CA-N-01-3
  Scenario: Dos registros simultáneos con el mismo celular responden 201 y 409, nunca 500
    When 4 visitantes se registran a la vez con el celular "987000111"
    Then una respuesta es 201 y las demás son 409 con "CELULAR_REGISTRADO"

  # requisitos no da un código para los nombres: la api responde 422 SOLICITUD_INVALIDA
  @HU-N-01 @api @CP-87 @CA-N-01-1
  Scenario Outline: Los nombres tienen de 2 a 80 caracteres
    When me registro con nombres de <largo> caracteres
    Then el resultado es "<resultado>"

    Examples:
      | largo | resultado          |
      | 1     | SOLICITUD_INVALIDA |
      | 2     | exitosa            |
      | 80    | exitosa            |
      | 81    | SOLICITUD_INVALIDA |

  @HU-N-01 @api @CP-88 @CA-N-01-5
  Scenario Outline: Validación del formato del correo
    When me registro con DNI "45678912", celular "987000111", PIN "4826" y correo "<correo>"
    Then el resultado es "<resultado>"

    Examples:
      | correo           | resultado       |
      | lucia@correo     | CORREO_INVALIDO |
      | lucia.correo.pe  | CORREO_INVALIDO |
      | lucia@@correo.pe | CORREO_INVALIDO |
      | lucia@correo.pe  | exitosa         |

  @HU-N-01 @api @CP-89 @CA-N-01-5
  Scenario: El correo de una cuenta cerrada se puede volver a usar
    When me registro con DNI "45678912", celular "987000111", PIN "4826" y correo "FABIAN.ROJAS@correo.pe"
    Then la respuesta tiene el código HTTP 201

  @HU-N-01 @api @tecnico @CP-90 @CA-N-01-1
  Scenario Outline: Un registro con cuerpo vacío, un campo faltante o un tipo inválido se rechaza y no crea la cuenta
    When envío POST /api/usuarios con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "<campo>"
    And el celular 987000111 sigue sin cuenta

    Examples:
      | cuerpo                                                                                 | campo   |
      | {}                                                                                     | dni     |
      | {"dni": "45678912", "nombres": "Lucía Fernández", "celular": "987000111"}              | pin     |
      | {"dni": 45678912, "nombres": "Lucía Fernández", "celular": "987000111", "pin": "4826"} | dni     |
      | {"dni": "45678912", "nombres": "Lucía Fernández", "celular": 987000111, "pin": "4826"} | celular |
      | {"dni": "45678912", "nombres": null, "celular": "987000111", "pin": "4826"}            | nombres |

  @HU-N-01 @api @tecnico @CP-91 @CA-N-01-2 @CA-N-01-6
  Scenario: Un registro rechazado por una regla no crea la cuenta ni envía el SMS de bienvenida
    When me registro con DNI "1234567", celular "987000111" y PIN "4826"
    Then la respuesta tiene el código HTTP 422
    And el resultado es "DNI_INVALIDO"
    And el celular 987000111 sigue sin cuenta
    And el celular 987000111 no recibe un SMS que contiene "Bienvenido"
