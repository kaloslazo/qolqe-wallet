"""El mismo happy path de limites_ui.feature, escrito con el patrón Screenplay en vez de pasos + Page Object.

Sirve para comparar estilos: corre con  pytest tests/e2e -m screenplay
"""
import pytest

from tests.e2e.screenplay import Actor, NavegarLaWeb
from tests.e2e.screenplay.tareas import (CambiarLimiteDiario, CrearAlerta, EstadoDeAlerta, IniciarSesion, IrA,
                                         LimiteDiarioVigente)


@pytest.mark.screenplay
def test_ana_baja_su_limite_y_crea_una_alerta(driver, app):
    app.reiniciar()
    app.fijar_reloj("2026-11-10T10:00:00")
    ana = Actor.llamado("Ana").que_puede(NavegarLaWeb(driver))

    ana.intenta(
        IniciarSesion.como("Ana"),
        IrA("Límites y alertas"),
        CambiarLimiteDiario.a(500),
        CrearAlerta.de("Recargas").desde(50),
    )

    assert ana.ve(LimiteDiarioVigente("S/ 500.00")) == "S/ 500.00"
    assert ana.ve(EstadoDeAlerta("Recargas · desde S/ 50.00", "Activa")) == "Activa"
