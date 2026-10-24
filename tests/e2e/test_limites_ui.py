"""Pasos de features/ui/*.feature (límites y defectos conocidos). Cada paso delega en un Page Object: aquí no hay selectores."""
from pytest_bdd import given, parsers, scenarios, then, when

from tests.e2e.pages.limites_page import LimitesPage
from tests.e2e.pages.login_page import LoginPage, Menu
from tests.e2e.pages.transferir_page import TransferirPage
from tests.e2e.soporte import bidi
from tests.e2e.soporte.api import USUARIOS

scenarios("../../features/ui")


# ---------------------------------------------------------------- Dado
@given("que los datos de prueba están restaurados")
def datos_restaurados(app):
    app.reiniciar()


@given(parsers.parse('que la fecha de la app es "{fecha}"'))
def fecha_de_la_app(app, fecha):
    app.fijar_reloj(fecha)


@given(parsers.parse("que {usuario} ingresa a Qolqe desde la pantalla de login"))
def login_por_ui(driver, usuario):
    LoginPage(driver).abrir().ingresar(*USUARIOS[usuario])


@given(parsers.parse('que abre "{opcion}" desde el menú'))
def abre_desde_menu(driver, opcion):
    Menu(driver).ir_a(opcion)
    LimitesPage(driver).esperar_carga()


@given(parsers.parse("que {usuario} tiene la sesión iniciada"))
def sesion_por_api(driver, app, contexto, usuario):
    contexto["usuario"] = usuario
    contexto["sesion"] = app.login(usuario)
    LoginPage(driver).iniciar_sesion_por_api(contexto["sesion"])


@given("que está en la página de límites")
def en_limites(driver):
    LimitesPage(driver).abrir()


@given(parsers.parse("que su límite diario es S/ {monto:d}"))
def limite_por_api(app, contexto, monto):
    app.cambiar_limite(contexto["sesion"]["access_token"], monto)


@given(parsers.parse('que el servidor responderá "{detalle}" al guardar el límite'))
def servidor_falla(driver, detalle):
    bidi.responder_error(driver, "**/api/limites", "PUT", detalle)


# ---------------------------------------------------------------- Cuando
@when(parsers.parse("cambia su límite diario a S/ {monto:d}"))
def cambia_limite(driver, monto):
    LimitesPage(driver).cambiar_limite(monto)


@when(parsers.parse('crea una alerta de "{tipo}" desde S/ {umbral:d}'))
def crea_alerta(driver, tipo, umbral):
    LimitesPage(driver).crear_alerta(tipo, umbral)


@when("pasan 24 horas y vuelve a ingresar")
def pasan_24_horas(driver, app, contexto):
    # el token dura 30 minutos: tras adelantar el reloj la sesión anterior ya venció
    app.avanzar_reloj(24 * 60)
    LoginPage(driver).iniciar_sesion_por_api(app.login(contexto["usuario"]))
    LimitesPage(driver).abrir()


@when(parsers.parse("transfiere S/ {monto:d} al celular {celular}"))
def transfiere(driver, monto, celular):
    TransferirPage(driver).abrir().transferir(monto, celular)


@when(parsers.parse("transfiere S/ {monto:d} a otro banco a la cuenta {cci}"))
def transfiere_a_otro_banco(driver, monto, cci):
    TransferirPage(driver).abrir().transferir_a_otro_banco(monto, cci)


@when("abre la página de límites")
def abre_limites(driver):
    LimitesPage(driver).abrir()


@when(parsers.parse('pausa la alerta "{titulo}"'))
def pausa(driver, titulo):
    LimitesPage(driver).pausar(titulo)


@when(parsers.parse('reanuda la alerta "{titulo}"'))
def reanuda(driver, titulo):
    LimitesPage(driver).reanudar(titulo)


@when(parsers.parse('elimina la alerta "{titulo}" y confirma'))
def elimina(driver, titulo):
    LimitesPage(driver).eliminar_y_confirmar(titulo)


@when(parsers.parse('edita la alerta "{titulo}" con umbral S/ {umbral:d}'))
def edita(driver, titulo, umbral):
    LimitesPage(driver).editar_umbral(titulo, umbral)


# ---------------------------------------------------------------- Entonces
@then(parsers.parse('ve el mensaje "{texto}"'))
def ve_mensaje(driver, texto):
    real = LimitesPage(driver).mensaje(texto)
    assert real == texto, f"Se esperaba {texto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('su límite diario vigente es "{monto}"'))
def limite_vigente(driver, monto):
    pagina = LimitesPage(driver)
    real = pagina.esperar_texto(pagina.LIMITE_DIARIO, monto)
    assert real == monto, f"Se esperaba {monto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('ve el aviso "{texto}"'))
def ve_aviso(driver, texto):
    pagina = LimitesPage(driver)
    real = pagina.esperar_texto(pagina.PENDIENTE, texto)
    assert real == texto, f"Se esperaba {texto!r} y la pantalla muestra {real!r}"


@then("ya no ve un aumento programado")
def sin_aumento_programado(driver):
    assert LimitesPage(driver).sin_aviso_pendiente(), f"El aumento debía cancelarse y sigue visible: {LimitesPage(driver).aviso_pendiente()!r}"


@then(parsers.parse('lo usado hoy es "{monto}"'))
def usado_hoy(driver, monto):
    pagina = LimitesPage(driver)
    real = pagina.esperar_texto(pagina.USADO, monto)
    assert real == monto, f"Se esperaba {monto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('ve la alerta "{titulo}" en estado "{estado}"'))
def alerta_en_estado(driver, titulo, estado):
    real = LimitesPage(driver).estado_alerta(titulo, estado)
    assert real == estado, f"Se esperaba {estado!r} y la pantalla muestra {real!r}"


@then(parsers.parse('el contador de alertas dice "{texto}"'))
def contador(driver, texto):
    real = LimitesPage(driver).contador(texto)
    assert real == texto, f"Se esperaba {texto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('la lista de alertas dice "{texto}"'))
def lista_dice(driver, texto):
    real = LimitesPage(driver).texto_lista(texto)
    assert real == texto, f"Se esperaba {texto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('el resultado en pantalla es "{resultado}"'))
def resultado_en_pantalla(driver, resultado):
    real = LimitesPage(driver).resultado_alerta()
    assert real == resultado, f"Se esperaba {resultado!r} y la pantalla muestra {real!r}"


@then(parsers.parse('{usuario} recibe un SMS que dice "{mensaje}"'))
def recibe_sms(app, usuario, mensaje):
    recibidos = [n["mensaje"] for n in app.notificaciones(USUARIOS[usuario][0])]
    assert mensaje in recibidos, f"No llegó el SMS {mensaje!r}; llegaron: {recibidos}"


@then(parsers.parse("{usuario} recibió {cantidad:d} SMS de alerta de consumo"))
def sms_de_alerta(app, usuario, cantidad):
    alertas = [n["mensaje"] for n in app.notificaciones(USUARIOS[usuario][0]) if n["mensaje"].startswith("Alerta Qolqe")]
    assert len(alertas) == cantidad, f"Se esperaba {cantidad} SMS de alerta y llegaron {len(alertas)}: {alertas}"


@then(parsers.parse('ve el error de transferencia "{texto}"'))
def error_transferencia(driver, texto):
    real = TransferirPage(driver).error()
    assert real == texto, f"Se esperaba {texto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('ve el comprobante con el monto "{monto}"'))
def comprobante(driver, monto):
    real = TransferirPage(driver).monto_comprobante()
    assert real == monto, f"Se esperaba {monto!r} y la pantalla muestra {real!r}"


@then(parsers.parse('en otra pestaña la bandeja de SMS de {usuario} muestra "{texto}"'))
def bandeja_en_otra_pestana(driver, usuario, texto):
    """Selenium 4 · ventanas: abre una pestaña nueva, lee la bandeja de SMS simulados y vuelve."""
    original = driver.current_window_handle
    driver.switch_to.new_window("tab")
    driver.get(f"{LimitesPage.url_base}/api/pruebas/notificaciones?celular={USUARIOS[usuario][0]}")
    contenido = driver.find_element("tag name", "body").text
    driver.close()
    driver.switch_to.window(original)
    assert texto in contenido, f"La bandeja no contiene {texto!r}: {contenido}"
