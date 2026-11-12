# language: es
@ui @screenplay
Característica: Dos usuarios a la vez, con el patrón Screenplay
  Como cliente de Qolqe
  Quiero que lo que hace otro usuario se vea en mi cuenta
  Para confiar en que el dinero llega

  # cada actor tiene su propio navegador y su propia sesión: los pasos dicen quién hace qué

  Antecedentes:
    Dado que los datos de prueba están restaurados
    Y que la fecha de la app es "2026-11-10T10:00:00"

  @HU-N-07 @HU-N-04 @CP-145 @CA-N-07-3 @CA-N-04-1
  Escenario: Ana le transfiere a Bruno y Bruno lo ve en su cuenta
    Dado que Ana y Bruno ingresan a Qolqe, cada uno en su navegador
    Cuando Ana le transfiere S/ 50 a Bruno
    Entonces Ana ve en su comprobante "S/ 50.00"
    Y Ana ve su saldo en "S/ 1,450.00"
    Y Bruno ve su saldo en "S/ 850.00"
    Y Bruno ve un movimiento reciente de "S/ 50.00"
