# language: es
@G5 @ui @defecto
Característica: Defectos conocidos del G5 vistos desde la interfaz web
  Los mismos defectos que la Parte 1 encontró por API (docs/defectos.md), ahora como los vería un cliente.
  Estos escenarios describen el comportamiento CORRECTO: fallan mientras el defecto exista.

  Antecedentes:
    Dado que los datos de prueba están restaurados
    Y que la fecha de la app es "2026-11-10T10:00:00"

  @DEF-01 @HU-G5-02
  Escenario: Una reducción del límite cancela el aumento programado
    Dado que Diego tiene la sesión iniciada
    Y que está en la página de límites
    Cuando cambia su límite diario a S/ 1500
    Entonces ve el aviso "Aumento a S/ 1,500.00 programado desde 11/11/2026 10:00"
    Cuando cambia su límite diario a S/ 500
    Entonces su límite diario vigente es "S/ 500.00"
    Y ya no ve un aumento programado

  @DEF-02 @HU-G5-03
  Escenario: Las transferencias a otro banco cuentan para el límite diario
    Dado que Diego tiene la sesión iniciada
    Cuando transfiere S/ 500 a otro banco a la cuenta 00219300123456789012
    Y transfiere S/ 500 a otro banco a la cuenta 00219300123456789012
    Y abre la página de límites
    Entonces lo usado hoy es "S/ 1,000.00"

  @DEF-03 @HU-G5-08
  Escenario: Una alerta avisa como máximo una vez por día
    Dado que Ana tiene la sesión iniciada
    Cuando transfiere S/ 300 al celular 912345678
    Y transfiere S/ 10 al celular 912345678
    Entonces Ana recibió 1 SMS de alerta de consumo
