from datetime import date
from decimal import Decimal

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QApplication, QDialog

from app.core.apariencia import MODO_CLARO, MODO_OSCURO, cargar_modo_tema, guardar_modo_tema
from app.services.parametro_service import agregar_valor, historial
from app.views.configuracion import (
    HistorialParametroDialog,
    ParametroFormDialog,
    ParametrosView,
)


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
        raise AssertionError("se esperaba ValueError")
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
        raise AssertionError("se esperaba ValueError")
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


def test_parametro_form_dialog_label_vigente_hasta_no_queda_huerfana(qtbot):
    """Sprint 39 (barrido de app/views/): la etiqueta "Vigente hasta" generada
    por QFormLayout.addRow(str, campo_vigente_hasta) debe ocultarse junto con
    el campo cuando el parametro no es de tramo cerrado -- si solo se oculta
    el QDateEdit queda una fila huerfana."""
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    etiqueta_vigente_hasta = dialogo._layout_formulario.labelForField(dialogo.campo_vigente_hasta)
    assert etiqueta_vigente_hasta is not None

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert etiqueta_vigente_hasta.isVisible() is False

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert etiqueta_vigente_hasta.isVisible() is True


def test_parametro_form_dialog_valor_no_finito_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("inf")
    dialogo.campo_usuario.setText("abogado1")
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_historial_parametro_dialog_lista_todas_las_filas_de_una_clave(qtbot):
    agregar_valor("SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1")
    agregar_valor("SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1")

    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)
    assert dialogo.tabla.rowCount() == 2
    assert dialogo.tabla.item(0, 0).text() == "1750905.00"


def test_parametros_view_abrir_dialogo_agregar_refresca_la_tabla(qtbot, monkeypatch):
    from PySide6.QtWidgets import QDialog

    vista = ParametrosView()
    qtbot.addWidget(vista)
    monkeypatch.setattr(ParametroFormDialog, "guardar", lambda self: agregar_valor(
        "USURA_MULTIPLICADOR", Decimal("1.5"), date(1900, 1, 1), "abogado1",
    ))

    def _exec_simulado(self):
        # Simula el flujo real (click en "Guardar" -> _guardar_y_cerrar ->
        # guardar() -> accept()) sin abrir el bucle de eventos modal.
        self.guardar()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ParametroFormDialog, "exec", _exec_simulado)

    vista._abrir_dialogo_agregar()

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"


def test_parametro_form_dialog_vigente_hasta_anterior_a_desde_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.campo_vigente_desde.setDate(QDate(2026, 2, 1))
    dialogo.campo_vigente_hasta.setDate(QDate(2026, 1, 1))
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_parametro_form_dialog_boton_guardar_tiene_icono_y_clase_primaria(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    assert not dialogo.boton_guardar.icon().isNull()
    assert dialogo.boton_guardar.property("class") == "primary"


def test_parametros_view_boton_agregar_tiene_clase_primaria(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.boton_agregar.property("class") == "primary"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")


def test_escape_cierra_el_dialogo_sin_guardar(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_Escape)

    assert dialogo.result() == QDialog.DialogCode.Rejected
    assert historial("USURA_MULTIPLICADOR") == []


def test_parametros_view_casilla_modo_oscuro_arranca_desmarcada_por_defecto(qtbot):
    # Sin QSettings previo (tmp_path vacio por test) el modo por defecto es "claro".
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is False


def test_parametros_view_casilla_modo_oscuro_refleja_el_modo_persistido(qtbot):
    guardar_modo_tema(MODO_OSCURO)

    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.casilla_modo_oscuro.isChecked() is True


def test_marcar_casilla_modo_oscuro_aplica_el_tema_en_caliente(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert "#1E1A18" in QApplication.instance().styleSheet()
    # Vuelve al modo claro para no filtrar estado hacia otros tests.
    vista.casilla_modo_oscuro.setChecked(False)


def test_marcar_casilla_modo_oscuro_persiste_la_eleccion(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    vista.casilla_modo_oscuro.setChecked(True)

    assert cargar_modo_tema() == MODO_OSCURO

    vista.casilla_modo_oscuro.setChecked(False)

    assert cargar_modo_tema() == MODO_CLARO


def test_enter_guarda_y_cierra_el_dialogo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_Return)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")
