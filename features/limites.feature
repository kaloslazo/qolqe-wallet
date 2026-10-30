# language: en
@G5 @limites
Feature: Límites y alertas de consumo
  Como cliente de Qolqe
  Quiero controlar mi límite diario de transferencias y recibir alertas de consumo
  Para proteger mi dinero y controlar mis gastos

  Background:
    Given que los datos de prueba están restaurados
    And que la fecha de la app es "2026-11-10T10:00:00"

  # ------------------------------------------------------------------ HU-G5-01
  @HU-G5-01 @api @CP-01
  Scenario: Veo mis límites con lo usado y lo disponible del día
    Given que inicié sesión como Diego
    And que ya transferí S/ 300.00 hoy al celular 912345678
    When consulto mis límites
    Then el límite por operación es S/ 500.00
    And mi límite diario vigente es S/ 1000.00
    And lo usado hoy es S/ 300.00
    And lo disponible hoy es S/ 700.00

  # ------------------------------------------------------------------ HU-G5-02 (R-G5-01: rango y múltiplos)
  @HU-G5-02 @api @CP-02
  Scenario Outline: Validación del nuevo límite diario (valores límite de R-G5-01)
    Given que inicié sesión como Ana
    When cambio mi límite diario a S/ <limite>
    Then el resultado es "<resultado>"

    Examples:
      | limite  | resultado       |
      | 50      | LIMITE_INVALIDO |
      | 99.99   | LIMITE_INVALIDO |
      | 100     | INMEDIATA       |
      | 120     | LIMITE_INVALIDO |
      | 150     | INMEDIATA       |
      | 1950    | INMEDIATA       |
      | 2000    | INMEDIATA       |
      | 2050    | LIMITE_INVALIDO |

  # ------------------------------------------------------------------ HU-G5-02 (R-G5-02: reducción vs aumento)
  @HU-G5-02 @api @CP-03
  Scenario: Una reducción del límite es inmediata
    Given que inicié sesión como Diego
    When cambio mi límite diario a S/ 500
    Then el resultado es "INMEDIATA"
    And mi límite diario vigente es S/ 500.00
    And recibo un SMS que contiene "Tu límite diario ahora es S/ 500"

  @HU-G5-02 @api @CP-04
  Scenario: Un aumento del límite queda programado para 24 horas después
    Given que inicié sesión como Diego
    When cambio mi límite diario a S/ 1500
    Then el resultado es "PROGRAMADA"
    And mi límite diario vigente es S/ 1000.00
    And tengo un aumento pendiente de S/ 1500.00
    And recibo un SMS que contiene "estará vigente desde"

  @HU-G5-02 @api @CP-05
  Scenario Outline: El aumento entra en vigencia exactamente a las 24 horas
    Given que inicié sesión como Diego
    And que solicité aumentar mi límite diario a S/ 1500
    When pasan <minutos> minutos
    Then mi límite diario vigente es S/ <vigente>

    Examples:
      | minutos | vigente |
      | 1439    | 1000.00 |
      | 1440    | 1500.00 |

  @HU-G5-02 @api @DEF-01 @fail @CP-06
  Scenario: Una reducción cancela el aumento pendiente
    Given que inicié sesión como Diego
    And que solicité aumentar mi límite diario a S/ 1500
    When cambio mi límite diario a S/ 500
    And pasan 1500 minutos
    Then mi límite diario vigente es S/ 500.00
    And no tengo un aumento pendiente

  @HU-G5-02 @api @CP-07
  Scenario: Reducir el límite por debajo del umbral pausa la alerta de transferencias
    Given que inicié sesión como Ana
    When cambio mi límite diario a S/ 250
    Then la alerta de TRANSFERENCIAS con umbral S/ 300 está PAUSADA

  # ------------------------------------------------------------------ HU-G5-03 (RN-06)
  @HU-G5-03 @api @CP-08
  Scenario Outline: Transferir respetando el límite diario vigente
    Given que inicié sesión como Diego
    And que ya transferí S/ 500.00 hoy al celular 912345678
    When transfiero S/ <monto> al celular 912345678
    Then el resultado es "<resultado>"

    Examples:
      | monto  | resultado              |
      | 499.99 | exitosa                |
      | 500.00 | exitosa                |
      | 500.01 | MONTO_INVALIDO         |

  @HU-G5-03 @api @CP-09
  Scenario: La transferencia que supera el límite diario por un céntimo se rechaza
    Given que inicié sesión como Diego
    And que ya transferí S/ 500.00 hoy al celular 912345678
    And que ya transferí S/ 500.00 hoy al celular 912345678
    When transfiero S/ 0.01 al celular 912345678
    Then el resultado es "LIMITE_DIARIO_EXCEDIDO"

  @HU-G5-03 @api @DEF-02 @fail @CP-10
  Scenario: Las transferencias interbancarias también cuentan para el límite diario
    Given que inicié sesión como Diego
    And que ya transferí S/ 500.00 hoy a otro banco
    And que ya transferí S/ 500.00 hoy a otro banco
    When transfiero S/ 0.01 al celular 912345678
    Then el resultado es "LIMITE_DIARIO_EXCEDIDO"

  # ------------------------------------------------------------------ HU-G5-04 (R-G5-03, R-G5-04)
  @HU-G5-04 @api @CP-11
  Scenario Outline: Validación del umbral de una alerta (valores límite de R-G5-03)
    Given que inicié sesión como Ana
    When creo una alerta de <tipo> con umbral S/ <umbral>
    Then el resultado es "<resultado>"

    Examples:
      | tipo     | umbral | resultado       |
      | RECARGAS | 0      | ALERTA_INVALIDA |
      | RECARGAS | 9.99   | ALERTA_INVALIDA |
      | RECARGAS | 10     | ACTIVA          |
      | RECARGAS | 15     | ALERTA_INVALIDA |
      | RECARGAS | 2000   | ACTIVA          |
      | RECARGAS | 2010   | ALERTA_INVALIDA |
      | AHORROS  | 100    | ALERTA_INVALIDA |

  @HU-G5-04 @api @CP-12
  Scenario Outline: El umbral de TRANSFERENCIAS o TODAS no supera el límite diario vigente
    Given que inicié sesión como Diego
    When creo una alerta de <tipo> con umbral S/ <umbral>
    Then el resultado es "<resultado>"

    Examples:
      | tipo           | umbral | resultado       |
      | TRANSFERENCIAS | 1000   | ACTIVA          |
      | TRANSFERENCIAS | 1010   | ALERTA_INVALIDA |
      | TODAS          | 1010   | ALERTA_INVALIDA |
      | PAGOS          | 1010   | ACTIVA          |

  @HU-G5-04 @api @CP-13
  Scenario: No se permiten dos alertas con el mismo tipo y umbral
    Given que inicié sesión como Ana
    When creo una alerta de TRANSFERENCIAS con umbral S/ 300
    Then el resultado es "ALERTA_DUPLICADA"

  @HU-G5-04 @api @CP-14
  Scenario: No se puede crear una sexta alerta
    Given que inicié sesión como Ana
    And que tengo 5 alertas
    When creo una alerta de PAGOS con umbral S/ 500
    Then el resultado es "LIMITE_ALERTAS"

  # ------------------------------------------------------------------ HU-G5-06
  @HU-G5-06 @api @CP-15
  Scenario: No se puede reanudar una alerta cuyo umbral supera el límite vigente
    Given que inicié sesión como Ana
    And que mi límite diario es S/ 250
    When reanudo la alerta de TRANSFERENCIAS con umbral S/ 300
    Then el resultado es "ALERTA_INVALIDA"

  # ------------------------------------------------------------------ HU-G5-08 (R-G5-05)
  @HU-G5-08 @api @CP-16
  Scenario Outline: La alerta notifica al alcanzar o superar el umbral
    Given que inicié sesión como Ana
    When transfiero S/ <monto> al celular 912345678
    Then recibo <sms> SMS de alerta de consumo

    Examples:
      | monto  | sms |
      | 299.99 | 0   |
      | 300.00 | 1   |
      | 300.01 | 1   |

  @HU-G5-08 @api @DEF-03 @fail @CP-17
  Scenario: Cada alerta notifica como máximo una vez por día
    Given que inicié sesión como Ana
    When transfiero S/ 300.00 al celular 912345678
    And transfiero S/ 10.00 al celular 912345678
    Then recibo 1 SMS de alerta de consumo

  @HU-G5-08 @api @CP-18
  Scenario: Una alerta pausada no notifica
    Given que inicié sesión como Ana
    And que pausé la alerta de TRANSFERENCIAS con umbral S/ 300
    When transfiero S/ 300.00 al celular 912345678
    Then recibo 0 SMS de alerta de consumo

  # ------------------------------------------------------------------ HU-G5-05
  @HU-G5-05 @api @CP-19
  Scenario: Veo mis alertas con su gasto de hoy
    Given que inicié sesión como Ana
    And que ya transferí S/ 120.00 hoy al celular 912345678
    When consulto mis alertas
    Then la alerta de TRANSFERENCIAS con umbral S/ 300 está ACTIVA
    And la alerta de TRANSFERENCIAS con umbral S/ 300 tiene un gasto de hoy de S/ 120.00

  # ------------------------------------------------------------------ HU-G5-07
  @HU-G5-07 @api @CP-20
  Scenario: Una alerta eliminada deja de notificar
    Given que inicié sesión como Ana
    And que eliminé la alerta de TRANSFERENCIAS con umbral S/ 300
    When transfiero S/ 300.00 al celular 912345678
    Then recibo 0 SMS de alerta de consumo

  # ------------------------------------------------------------------ Casos técnicos (autenticación, cuerpo, sin efecto, propiedad de los datos)
  @HU-G5-01 @api @tecnico @CP-21
  Scenario: Sin token no puedo consultar mis límites
    When consulto mis límites sin token
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

  @HU-G5-02 @api @tecnico @CP-22
  Scenario: Con un token inválido no puedo cambiar mi límite
    When cambio mi límite diario a S/ 500 con el token "token-invalido"
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

  @HU-G5-02 @api @tecnico @CP-23
  Scenario Outline: Un cuerpo vacío o con un tipo inválido se rechaza sin cambiar el límite
    Given que inicié sesión como Diego
    When envío el cambio de límite con el cuerpo '<cuerpo>'
    Then la respuesta tiene el código HTTP 422
    And el resultado es "SOLICITUD_INVALIDA"
    And el error indica el campo "limite_diario"
    And mi límite diario vigente es S/ 1000.00

    Examples:
      | cuerpo                   |
      | {}                       |
      | {"limite_diario": "abc"} |
      | {"limite_diario": null}  |

  @HU-G5-02 @api @tecnico @CP-24
  Scenario: Un cambio rechazado por regla de negocio no tiene efecto
    Given que inicié sesión como Diego
    When cambio mi límite diario a S/ 2050
    Then la respuesta tiene el código HTTP 422
    And el resultado es "LIMITE_INVALIDO"
    And mi límite diario vigente es S/ 1000.00
    And no tengo un aumento pendiente

  @api @tecnico @CP-25
  Scenario Outline: La alerta de otro usuario responde como si no existiera
    Given que inicié sesión como Diego
    When intento <accion> la alerta de TRANSFERENCIAS con umbral S/ 300 de Ana
    Then la respuesta tiene el código HTTP 404
    And el resultado es "ALERTA_NO_ENCONTRADA"
    And la alerta de TRANSFERENCIAS con umbral S/ 300 de Ana sigue ACTIVA

    @HU-G5-06
    Examples: Pausar
      | accion |
      | pausar |

    @HU-G5-07
    Examples: Eliminar
      | accion   |
      | eliminar |

  # ------------------------------------------------------------------ Parte 2: casos nuevos de límites
  # ------------------------------------------------------------------ HU-G5-01
  @HU-G5-01 @api @CP-70
  Scenario Outline: Lo disponible hoy se recalcula al bajar el límite y nunca es negativo
    Given que inicié sesión como Diego
    And que ya transferí S/ 500.00 hoy al celular 912345678
    When cambio mi límite diario a S/ <limite>
    Then lo disponible hoy es S/ <disponible>

    Examples:
      | limite | disponible |
      | 600    | 100.00     |
      | 500    | 0.00       |
      | 300    | 0.00       |

  # ------------------------------------------------------------------ HU-G5-02 (R-G5-02)
  @HU-G5-02 @api @CP-71
  Scenario: Pedir el mismo límite vigente no programa un aumento
    Given que inicié sesión como Diego
    When cambio mi límite diario a S/ 1000
    Then el resultado es "INMEDIATA"
    And mi límite diario vigente es S/ 1000.00
    And no tengo un aumento pendiente

  @HU-G5-02 @api @CP-72
  Scenario: Un segundo aumento reemplaza al aumento pendiente
    Given que inicié sesión como Diego
    And que solicité aumentar mi límite diario a S/ 1500
    When cambio mi límite diario a S/ 2000
    Then el resultado es "PROGRAMADA"
    And mi límite diario vigente es S/ 1000.00
    And tengo un aumento pendiente de S/ 2000.00

  @HU-G5-02 @HU-G5-03 @api @CP-73
  Scenario: Mientras el aumento está pendiente, al transferir rige el límite anterior
    Given que inicié sesión como Diego
    And que solicité aumentar mi límite diario a S/ 1500
    And que ya transferí S/ 500.00 hoy al celular 912345678
    And que ya transferí S/ 500.00 hoy al celular 912345678
    When transfiero S/ 0.01 al celular 912345678
    Then el resultado es "LIMITE_DIARIO_EXCEDIDO"

  @HU-G5-02 @HU-G5-04 @R-G5-04 @api @CP-74
  Scenario: Con un aumento pendiente, el umbral se compara con el límite vigente
    Given que inicié sesión como Diego
    And que solicité aumentar mi límite diario a S/ 1500
    When creo una alerta de TRANSFERENCIAS con umbral S/ 1200
    Then el resultado es "ALERTA_INVALIDA"

  # ------------------------------------------------------------------ HU-G5-03
  @HU-G5-03 @api @reloj @CP-75
  Scenario: El límite diario se reinicia al día siguiente
    Given que inicié sesión como Diego
    And que ya transferí S/ 500.00 hoy al celular 912345678
    And que ya transferí S/ 500.00 hoy al celular 912345678
    When pasan 1440 minutos
    And transfiero S/ 500.00 al celular 912345678
    Then el resultado es "exitosa"
    And lo usado hoy es S/ 500.00

  # ------------------------------------------------------------------ HU-G5-06 (editar, pausar, reanudar)
  @HU-G5-06 @api @CP-76
  Scenario Outline: Validación del nuevo umbral al editar una alerta
    Given que inicié sesión como Ana
    When edito el umbral de la alerta de TRANSFERENCIAS con umbral S/ 300 a S/ <umbral>
    Then el resultado es "<resultado>"

    Examples:
      | umbral | resultado       |
      | 400    | ACTIVA          |
      | 405    | ALERTA_INVALIDA |
      | 0      | ALERTA_INVALIDA |
      | 2010   | ALERTA_INVALIDA |

  @HU-G5-06 @R-G5-04 @api @CP-77
  Scenario: El umbral editado no puede superar el límite diario vigente
    Given que inicié sesión como Ana
    And que mi límite diario es S/ 500
    When edito el umbral de la alerta de TRANSFERENCIAS con umbral S/ 300 a S/ 600
    Then el resultado es "ALERTA_INVALIDA"
    And la alerta de TRANSFERENCIAS con umbral S/ 300 está ACTIVA

  @HU-G5-06 @api @CP-78
  Scenario: Editar el umbral a uno que ya existe se rechaza
    Given que inicié sesión como Ana
    And que creé una alerta de TRANSFERENCIAS con umbral S/ 400
    When edito el umbral de la alerta de TRANSFERENCIAS con umbral S/ 400 a S/ 300
    Then la respuesta tiene el código HTTP 409
    And el resultado es "ALERTA_DUPLICADA"

  @HU-G5-06 @api @CP-79
  Scenario: Reanudar una alerta pausada que cabe en el límite
    Given que inicié sesión como Ana
    And que pausé la alerta de TRANSFERENCIAS con umbral S/ 300
    When reanudo la alerta de TRANSFERENCIAS con umbral S/ 300
    Then el resultado es "ACTIVA"

  @HU-G5-06 @api @tecnico @CP-80
  Scenario: Un estado que no es ACTIVA ni PAUSADA se rechaza
    Given que inicié sesión como Ana
    When cambio el estado de la alerta de TRANSFERENCIAS con umbral S/ 300 a BORRADA
    Then la respuesta tiene el código HTTP 422
    And el resultado es "ALERTA_INVALIDA"

  # ------------------------------------------------------------------ HU-G5-07
  @HU-G5-07 @api @CP-81
  Scenario: Eliminar una alerta libera un cupo
    Given que inicié sesión como Ana
    And que tengo 5 alertas
    And que eliminé la alerta de TRANSFERENCIAS con umbral S/ 300
    When creo una alerta de PAGOS con umbral S/ 500
    Then el resultado es "ACTIVA"

  @HU-G5-07 @api @tecnico @contrato @CP-82
  Scenario Outline: Eliminar una alerta con un identificador que no existe
    Given que inicié sesión como Ana
    When elimino la alerta con el identificador <id>
    Then la respuesta tiene el código HTTP <http>
    And el resultado es "<resultado>"

    Examples:
      | id                  | http | resultado            |
      | 99999               | 404  | ALERTA_NO_ENCONTRADA |
      | 9223372036854775808 | 422  | SOLICITUD_INVALIDA   |

  # salió de la cobertura frente a Schemathesis: él probaba las alertas sin token y nosotros no
  @HU-G5-04 @HU-G5-05 @HU-G5-06 @HU-G5-07 @api @tecnico @contrato @CP-85
  Scenario Outline: Sin token no puedo usar mis alertas
    When envío <metodo> <ruta> sin token
    Then la respuesta tiene el código HTTP 401
    And el resultado es "NO_AUTENTICADO"

    Examples:
      | metodo | ruta                   |
      | GET    | /api/limites/alertas   |
      | POST   | /api/limites/alertas   |
      | PUT    | /api/limites/alertas/1 |
      | DELETE | /api/limites/alertas/1 |

  # ------------------------------------------------------------------ HU-G5-08 (R-G5-05)
  @HU-G5-08 @R-G5-05 @api @CP-83
  Scenario: Una transferencia a otro banco cuenta para la alerta por su monto, sin la comisión
    Given que inicié sesión como Ana
    When transfiero S/ 300.00 a otro banco
    Then recibo 1 SMS de alerta de consumo
    And recibo un SMS que contiene "llegó a S/ 300.00"

  @HU-G5-08 @R-G5-05 @api @CP-84
  Scenario: La alerta TODAS suma recargas y transferencias
    Given que inicié sesión como Ana
    And que creé una alerta de TODAS con umbral S/ 200
    And que ya recargué S/ 50 hoy al celular 987111222
    When transfiero S/ 150.00 al celular 912345678
    Then recibo 1 SMS de alerta de consumo
    And recibo un SMS que contiene "tu gasto de hoy en todas"
