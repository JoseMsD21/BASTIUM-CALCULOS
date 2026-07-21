from datetime import date
from decimal import Decimal

from app.services.parametro_service import agregar_valor
from app.views.configuracion import ParametrosView


def test_parametros_view_lista_todas_las_claves_del_catalogo(qtbot):
    from app.services.parametro_service import CATALOGO_PARAMETROS

    vista = ParametrosView()
    qtbot.addWidget(vista)
    assert vista.tabla.rowCount() == len(CATALOGO_PARAMETROS)


def test_parametros_view_muestra_sin_dato_cuando_no_hay_valor_cargado(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "(sin dato)"


def test_parametros_view_muestra_el_valor_vigente_cuando_hay_dato(qtbot):
    agregar_valor("USURA_MULTIPLICADOR", Decimal("1.5"), date(1900, 1, 1), "test")
    vista = ParametrosView()
    qtbot.addWidget(vista)
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"
