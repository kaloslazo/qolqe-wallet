# language: en
@nucleo
Feature: Transferir dinero
  Como cliente
  Quiero enviar dinero a otro usuario Qolqe o a otro banco
  Para pagar de inmediato

  Background:
    Given que los datos de prueba están restaurados
    And que la fecha de la app es "2026-11-10T10:00:00"

  @HU-N-07 @api @CP-49 @CA-N-07-1 @CA-N-07-3
  Scenario: Transferencia exitosa a un usuario registrado
    Given que inicié sesión como Ana
    When transfiero S/ 100.00 al celular 912345678
    Then el resultado es "exitosa"
    And la transferencia tiene un código de operación
    And mi saldo es S/ 1400.00
    And el celular 912345678 recibe un SMS que contiene "100.00"

  @HU-N-07 @api @CP-50 @CA-N-07-2
  Scenario Outline: Validación del monto por operación (RN-05)
    Given que inicié sesión como Ana
    When transfiero S/ <monto> al celular 912345678
    Then el resultado es "<resultado>"

    Examples:
      | monto  | resultado      |
      | 0.00   | MONTO_INVALIDO |
      | 0.01   | exitosa        |
      | 500.00 | exitosa        |
      | 500.01 | MONTO_INVALIDO |
      | 10.005 | MONTO_INVALIDO |

  @HU-N-07 @api @CP-51 @CA-N-07-2
  Scenario Outline: Destinos no permitidos (RN-07)
    Given que inicié sesión como Ana
    When transfiero S/ 10.00 al celular <celular>
    Then el resultado es "<resultado>"

    Examples:
      | celular   | resultado                |
      | 987654321 | TRANSFERENCIA_A_SI_MISMO |
      | 900999999 | DESTINO_NO_REGISTRADO    |

    @DEF-06 @fail
    Examples: Cuenta cerrada
      | celular   | resultado        |
      | 934567812 | DESTINO_INACTIVO |

  @HU-N-07 @api @CP-52 @CA-N-07-2
  Scenario: El saldo debe cubrir el monto (RN-08)
    Given que inicié sesión como Carla
    When transfiero S/ 50.01 al celular 912345678
    Then el resultado es "SALDO_INSUFICIENTE"

  @HU-N-07 @HU-G5-03 @api @rendimiento @DEF-11 @fail @CP-53 @CA-N-07-5 @CA-G5-03-2
  Scenario: Transferencias simultáneas no superan el límite diario
    # Parte 3: lo mismo, en 5 rondas, en tests/performance/escenarios/concurrencia.js
    Given que inicié sesión como Diego
    When envío 5 transferencias simultáneas de S/ 300.00 al celular 912345678
    Then lo usado hoy no supera S/ 1000.00

  @HU-N-07 @api @rendimiento @DEF-11 @fail @CP-86 @CA-N-07-5
  Scenario: Transferencias simultáneas no dejan el saldo negativo
    Given que inicié sesión como Carla
    When envío 2 transferencias simultáneas de S/ 40.00 al celular 912345678
    Then mi saldo es S/ 10.00

  @HU-N-08 @api @CP-54 @CA-N-08-1
  Scenario Outline: Validación del CCI
    Given que inicié sesión como Ana
    When transfiero S/ 100.00 al CCI <cci>
    Then el resultado es "<resultado>"

    Examples:
      | cci                   | resultado   |
      | 0021930012345678901   | CCI_INVALIDO |
      | 00219300123456789012  | exitosa      |
      | 002193001234567890123 | CCI_INVALIDO |

  @HU-N-08 @api @DEF-04 @fail @CP-55 @CA-N-08-2
  Scenario: El saldo debe cubrir el monto más la comisión interbancaria
    Given que inicié sesión como Carla
    When transfiero S/ 50.00 a otro banco
    Then el resultado es "SALDO_INSUFICIENTE"
    And mi saldo es S/ 50.00

  @HU-N-09 @api @CP-56 @CA-N-09-1
  Scenario Outline: Simular la comisión sin realizar la operación (RN-09)
    Given que inicié sesión como Ana
    When simulo la comisión de S/ <monto> a otro banco
    Then la comisión es S/ <comision> y el total S/ <total>
    And mi saldo es S/ 1500.00

    Examples:
      | monto  | comision | total  |
      | 50.00  | 1.00     | 51.00  |
      | 66.67  | 1.00     | 67.67  |
      | 100.00 | 1.50     | 101.50 |
      | 333.33 | 5.00     | 338.33 |
      | 400.00 | 5.00     | 405.00 |

  @HU-N-07 @api @CP-115 @CA-N-07-1
  Scenario: Transferir eligiendo un contacto en lugar del celular
    Given que inicié sesión como Ana
    When transfiero S/ 50.00 a mi contacto "Bruno"
    Then el resultado es "exitosa"
    And el comprobante muestra
      | destinatario.celular | 912345678 |
      | monto                | 50.00     |
    And el saldo de Bruno es S/ 850.00

  @HU-N-07 @api @CP-116 @CA-N-07-1
  Scenario Outline: La descripción admite hasta 60 caracteres
    Given que inicié sesión como Ana
    When transfiero S/ 10.00 al celular 912345678 con una descripción de <largo> caracteres
    Then el resultado es "<resultado>"
    And mi saldo es S/ <saldo>

    Examples:
      | largo | resultado          | saldo   |
      | 60    | exitosa            | 1490.00 |
      | 61    | SOLICITUD_INVALIDA | 1500.00 |

  @HU-N-07 @api @CP-117 @CA-N-07-3
  Scenario: La transferencia acredita al destinatario y los dos vemos el movimiento con el mismo código
    Given que inicié sesión como Ana
    When transfiero S/ 100.00 al celular 912345678
    Then el resultado es "exitosa"
    And mi saldo es S/ 1400.00
    And el saldo de Bruno es S/ 900.00
    And el movimiento de Ana con el código de la transferencia es TRANSFERENCIA_ENVIADA por S/ -100.00
    And el movimiento de Bruno con el código de la transferencia es TRANSFERENCIA_RECIBIDA por S/ 100.00

  @HU-N-07 @api @CP-118 @CA-N-07-4
  Scenario: El comprobante muestra el código, el destinatario enmascarado, los montos, mi nuevo saldo y la fecha
    Given que la fecha de la app es "2026-11-10T08:15:00"
    And que inicié sesión como Ana
    When transfiero S/ 100.00 al celular 912345678
    Then la transferencia tiene un código de operación
    And el comprobante muestra
      | destinatario.nombre  | Bruno D.  |
      | destinatario.celular | 912345678 |
      | monto                | 100.00    |
      | comision             | 0.00      |
      | total                | 100.00    |
      | saldo                | 1400.00   |
    And el comprobante tiene la fecha "2026-11-10T08:15"

  @HU-N-07 @api @DEF-12 @fail @CP-119 @CA-N-07-3
  Scenario: Dos transferencias en el mismo segundo tienen códigos de operación distintos
    Given que inicié sesión como Ana
    When transfiero S/ 10.00 al celular 912345678 y S/ 10.00 al celular 956781234 en el mismo segundo
    Then las dos transferencias tienen códigos de operación distintos

  @HU-N-07 @api @tecnico @CP-120 @CA-N-07-2
  Scenario Outline: Sin un token válido no puedo transferir y ningún saldo cambia
    Given que inicié sesión como Ana
    When envío POST /api/transferencias con el cuerpo '{"celular_destino": "912345678", "monto": 100}' <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"
    And mi saldo es S/ 1500.00
    And el saldo de Bruno es S/ 800.00

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-07 @api @tecnico @CP-121 @CA-N-07-2
  Scenario Outline: Un cuerpo vacío o con un tipo inválido se rechaza indicando el campo y sin mover dinero
    Given que inicié sesión como Ana
    When envío POST /api/transferencias con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "<campo>"
    And mi saldo es S/ 1500.00
    And el saldo de Bruno es S/ 800.00

    Examples:
      | cuerpo                                                             | campo           |
      | {}                                                                 | monto           |
      | {"celular_destino": 912345678, "monto": 100}                       | celular_destino |
      | {"tipo": "OTRO", "celular_destino": "912345678", "monto": 100}     | tipo            |
      | {"contacto_id": "Bruno", "monto": 100}                             | contacto_id     |
      | {"celular_destino": "912345678", "monto": 100, "descripcion": 5}   | descripcion     |

  @HU-N-07 @api @tecnico @CP-122 @CA-N-07-2 @CA-N-07-3
  Scenario: Una transferencia rechazada por una regla no mueve dinero ni avisa al destinatario
    Given que inicié sesión como Carla
    When transfiero S/ 50.01 al celular 912345678
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SALDO_INSUFICIENTE"
    And mi saldo es S/ 50.00
    And el saldo de Bruno es S/ 800.00
    And el celular 912345678 no recibe un SMS que contiene "Recibiste"

  @HU-N-07 @api @tecnico @CP-123 @CA-N-07-1
  Scenario: No puedo transferir usando el contacto de otro usuario
    Given que inicié sesión como Diego
    When transfiero S/ 50.00 al contacto "Bruno" de Ana
    Then la respuesta tiene el código HTTP 404
    And el resultado es "CONTACTO_NO_ENCONTRADO"
    And mi saldo es S/ 2500.00
    And el saldo de Bruno es S/ 800.00

  @HU-N-08 @api @CP-124 @CA-N-08-2
  Scenario Outline: Una transferencia a otro banco cobra la comisión de RN-09
    Given que inicié sesión como Ana
    When transfiero S/ <monto> a otro banco
    Then el resultado es "exitosa"
    And la comisión es S/ <comision> y el total S/ <total>
    And mi saldo es S/ <saldo>

    Examples:
      | monto  | comision | total  | saldo   |
      | 50.00  | 1.00     | 51.00  | 1449.00 |
      | 100.00 | 1.50     | 101.50 | 1398.50 |
      | 400.00 | 5.00     | 405.00 | 1095.00 |

  @HU-N-08 @api @CP-125 @CA-N-08-2
  Scenario Outline: El monto de una transferencia a otro banco cumple RN-05
    Given que inicié sesión como Ana
    When transfiero S/ <monto> a otro banco
    Then el resultado es "<resultado>"

    Examples:
      | monto  | resultado      |
      | 0.00   | MONTO_INVALIDO |
      | 0.01   | exitosa        |
      | 500.00 | exitosa        |
      | 500.01 | MONTO_INVALIDO |
      | 10.005 | MONTO_INVALIDO |

  @HU-N-08 @api @CP-126 @CA-N-08-3
  Scenario: El comprobante y el movimiento muestran el CCI enmascarado
    Given que inicié sesión como Ana
    When transfiero S/ 100.00 a otro banco
    Then el comprobante muestra
      | destinatario.cci | ****************9012 |
    And el movimiento de Ana con el código de la transferencia muestra la contraparte "****************9012"

  @HU-N-08 @api @tecnico @CP-127 @CA-N-08-1
  Scenario Outline: Sin un token válido no puedo transferir a otro banco y mi saldo no cambia
    Given que inicié sesión como Ana
    When envío POST /api/transferencias con el cuerpo '{"tipo": "INTERBANCARIA", "cci": "00219300123456789012", "monto": 100}' <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"
    And mi saldo es S/ 1500.00

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-08 @api @tecnico @CP-128 @CA-N-08-1
  Scenario Outline: Un CCI o un monto de tipo inválido se rechaza indicando el campo y sin cobrar nada
    Given que inicié sesión como Ana
    When envío POST /api/transferencias con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "<campo>"
    And mi saldo es S/ 1500.00

    Examples:
      | cuerpo                                                                    | campo |
      | {"tipo": "INTERBANCARIA", "cci": 219300123456789012, "monto": 100}        | cci   |
      | {"tipo": "INTERBANCARIA", "cci": "00219300123456789012"}                  | monto |
      | {"tipo": "INTERBANCARIA", "cci": "00219300123456789012", "monto": "cien"} | monto |

  @HU-N-08 @api @tecnico @CP-129 @CA-N-08-1
  Scenario Outline: Una transferencia a otro banco sin CCI o con letras en el CCI se rechaza sin cobrar nada
    Given que inicié sesión como Ana
    When envío POST /api/transferencias con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "<resultado>"
    And mi saldo es S/ 1500.00

    Examples:
      | cuerpo                                                                 | resultado         |
      | {"tipo": "INTERBANCARIA", "monto": 100}                                | DESTINO_REQUERIDO |
      | {"tipo": "INTERBANCARIA", "cci": "0021930012345678901A", "monto": 100} | CCI_INVALIDO      |

  @HU-N-09 @api @CP-130 @CA-N-09-1
  Scenario: Simular una transferencia entre cuentas Qolqe no cobra comisión ni mueve dinero
    Given que inicié sesión como Ana
    When simulo la comisión de S/ 100.00 a otro usuario Qolqe
    Then la comisión es S/ 0.00 y el total S/ 100.00
    And mi saldo es S/ 1500.00
    And lo usado hoy es S/ 0.00

  @HU-N-09 @api @tecnico @CP-131 @CA-N-09-1
  Scenario Outline: Sin un token válido no puedo simular la comisión
    Given que inicié sesión como Ana
    When envío GET /api/transferencias/comision?monto=100&tipo=INTERBANCARIA <acceso>
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

    Examples:
      | acceso                |
      | sin token             |
      | con un token inválido |
      | con mi token vencido  |

  @HU-N-09 @api @tecnico @CP-132 @CA-N-09-1
  Scenario Outline: Una simulación sin monto o con parámetros inválidos se rechaza indicando el parámetro
    Given que inicié sesión como Ana
    When envío GET <ruta>
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el parámetro "<parametro>"

    Examples:
      | ruta                                                       | parametro |
      | /api/transferencias/comision?tipo=INTERBANCARIA            | monto     |
      | /api/transferencias/comision?monto=cien&tipo=INTERBANCARIA | monto     |
      | /api/transferencias/comision?monto=100&tipo=OTRO           | tipo      |
