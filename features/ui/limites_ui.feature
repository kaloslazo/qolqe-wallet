# language: es
@G5 @ui
Característica: Límites y alertas de consumo desde la interfaz web
  Como cliente de Qolqe
  Quiero controlar mi límite diario y mis alertas desde la página de límites
  Para proteger mi dinero sin depender de nadie

  Antecedentes:
    Dado que los datos de prueba están restaurados
    Y que la fecha de la app es "2026-11-10T10:00:00"

  # ---------------------------------------------------------------- flujo feliz (demo)
  @happy @demo @HU-G5-01 @HU-G5-02 @HU-G5-04 @CP-57
  Escenario: Ana baja su límite diario y crea una alerta de recargas
    Dado que Ana ingresa a Qolqe desde la pantalla de login
    Y que abre "Límites y alertas" desde el menú
    Cuando cambia su límite diario a S/ 500
    Entonces ve el mensaje "Tu límite diario fue actualizado"
    Y su límite diario vigente es "S/ 500.00"
    Cuando crea una alerta de "Recargas" desde S/ 50
    Entonces ve la alerta "Recargas · desde S/ 50.00" en estado "Activa"
    Y el contador de alertas dice "2 de 5"
    Y Ana recibe un SMS que dice "Tu límite diario ahora es S/ 500."

  # ---------------------------------------------------------------- HU-G5-02 · R-G5-02
  @HU-G5-02 @reloj @CP-58
  Escenario: Un aumento del límite entra en vigencia 24 horas después
    Dado que Diego tiene la sesión iniciada
    Y que está en la página de límites
    Cuando cambia su límite diario a S/ 1500
    Entonces ve el aviso "Aumento a S/ 1,500.00 programado desde 11/11/2026 10:00"
    Y su límite diario vigente es "S/ 1,000.00"
    Cuando pasan 24 horas y vuelve a ingresar
    Entonces su límite diario vigente es "S/ 1,500.00"

  # ---------------------------------------------------------------- R-G5-04
  @HU-G5-02 @R-G5-04 @CP-59
  Escenario: Bajar el límite pausa la alerta que queda por encima
    Dado que Ana tiene la sesión iniciada
    Y que está en la página de límites
    Cuando cambia su límite diario a S/ 200
    Entonces ve la alerta "Transferencias · desde S/ 300.00" en estado "Pausada"

  # ---------------------------------------------------------------- HU-G5-03
  @HU-G5-03 @CP-60
  Escenario: Una transferencia que supera el límite diario es rechazada
    Dado que Ana tiene la sesión iniciada
    Y que su límite diario es S/ 100
    Cuando transfiere S/ 150 al celular 912345678
    Entonces ve el error de transferencia "La operación supera tu límite diario de S/ 100.00"

  # ---------------------------------------------------------------- HU-G5-08 (extremo a extremo)
  @HU-G5-08 @e2e @ventanas @CP-61
  Escenario: Ana recibe un SMS al alcanzar el umbral de su alerta
    Dado que Ana tiene la sesión iniciada
    Cuando transfiere S/ 300 al celular 912345678
    Entonces ve el comprobante con el monto "S/ 300.00"
    Y en otra pestaña la bandeja de SMS de Ana muestra "Alerta Qolqe: tu gasto de hoy en transferencias llegó a S/ 300.00"

  # ---------------------------------------------------------------- HU-G5-06 · HU-G5-07
  @HU-G5-06 @HU-G5-07 @dialogos @CP-62
  Escenario: Pausar, reanudar y eliminar una alerta
    Dado que Ana tiene la sesión iniciada
    Y que está en la página de límites
    Cuando pausa la alerta "Transferencias · desde S/ 300.00"
    Entonces ve la alerta "Transferencias · desde S/ 300.00" en estado "Pausada"
    Cuando reanuda la alerta "Transferencias · desde S/ 300.00"
    Entonces ve la alerta "Transferencias · desde S/ 300.00" en estado "Activa"
    Cuando elimina la alerta "Transferencias · desde S/ 300.00" y confirma
    Entonces la lista de alertas dice "No tienes alertas de consumo"

  # ---------------------------------------------------------------- HU-G5-06 (diálogo con formulario)
  @HU-G5-06 @dialogos @CP-63
  Escenario: Editar el umbral de una alerta
    Dado que Ana tiene la sesión iniciada
    Y que está en la página de límites
    Cuando edita la alerta "Transferencias · desde S/ 300.00" con umbral S/ 450
    Entonces ve la alerta "Transferencias · desde S/ 450.00" en estado "Activa"

  # ---------------------------------------------------------------- HU-G5-04 · R-G5-03 / R-G5-04 (datos)
  @HU-G5-04 @datos @CP-64
  Esquema del escenario: Validación del umbral al crear una alerta
    Dado que Ana tiene la sesión iniciada
    Y que está en la página de límites
    Cuando crea una alerta de "<tipo>" desde S/ <umbral>
    Entonces el resultado en pantalla es "<resultado>"

    Ejemplos:
      | tipo               | umbral | resultado                                                        |
      | Recargas           | 5      | El umbral debe estar entre S/ 10 y S/ 2,000                      |
      | Recargas           | 10     | Alerta creada                                                    |
      | Pagos de servicios | 15     | El umbral debe ser múltiplo de S/ 10                             |
      | Pagos de servicios | 2000   | Alerta creada                                                    |
      | Transferencias     | 300    | Ya tienes una alerta con ese tipo y umbral                       |
      | Todos mis gastos   | 2010   | El umbral debe estar entre S/ 10 y S/ 2,000                      |

  # ---------------------------------------------------------------- R-G5-04
  @HU-G5-04 @R-G5-04 @CP-65
  Escenario: El umbral de TODAS no puede superar el límite diario vigente
    Dado que Diego tiene la sesión iniciada
    Y que está en la página de límites
    Cuando crea una alerta de "Todos mis gastos" desde S/ 1100
    Entonces el resultado en pantalla es "El umbral no puede superar tu límite diario vigente de S/ 1000.00"

  # ---------------------------------------------------------------- capacidad de Selenium 4: BiDi
  @bidi @red @CP-66
  Escenario: La interfaz avisa si el servidor falla al guardar el límite
    Dado que Ana tiene la sesión iniciada
    Y que está en la página de límites
    Y que el servidor responderá "Servicio no disponible" al guardar el límite
    Cuando cambia su límite diario a S/ 500
    Entonces ve el mensaje "Servicio no disponible"
    Y su límite diario vigente es "S/ 2,000.00"
