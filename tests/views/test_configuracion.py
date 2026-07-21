from datetime import date
from decimal import Decimal

from app.services.parametro_service import agregar_valor, historial
from app.views.configuracion import ParametroFormDialog, ParametrosView


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


def test_parametro_form_dialog_guarda_un_valor_abierto(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")
    assert filas[0].usuario == "abogado1"


def test_parametro_form_dialog_valor_invalido_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("no-es-un-numero")
    dialogo.campo_usuario.setText("abogado1")
    try:
        dialogo.guardar()
        assert False, "se esperaba ValueError"
    except ValueError:
        pass


def test_parametro_form_dialog_usuario_vacio_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    try:
        dialogo.guardar()
        assert False, "se esperaba ValueError"
    except ValueError:
        pass


def test_parametro_form_dialog_muestra_vigente_hasta_solo_para_tramo_cerrado(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert dialogo.campo_vigente_hasta.isVisible() is False

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
