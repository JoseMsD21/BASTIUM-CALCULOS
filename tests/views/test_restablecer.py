"""Tests de ConfirmarRestablecerDialog (Sprint 66, Task 3): exige escribir
"RESTABLECER" exacto para habilitar el boton de confirmar -- misma filosofia
de "sin papelera, definitivo tras confirmar" que ya usan Eliminar en
Obligaciones/Abonos (Sprint 60)."""

from app.views.restablecer import ConfirmarRestablecerDialog


def test_confirmar_restablecer_dialog_boton_deshabilitado_por_defecto(qtbot):
    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)
    assert dialogo.boton_confirmar.isEnabled() is False


def test_confirmar_restablecer_dialog_boton_se_habilita_con_el_texto_exacto(qtbot):
    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)

    dialogo.campo_confirmacion.setText("restablecer")
    assert dialogo.boton_confirmar.isEnabled() is False

    dialogo.campo_confirmacion.setText("RESTABLECER")
    assert dialogo.boton_confirmar.isEnabled() is True


def test_confirmar_restablecer_dialog_confirmar_acepta_el_dialogo(qtbot):
    from PySide6.QtWidgets import QDialog

    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)
    dialogo.campo_confirmacion.setText("RESTABLECER")
    dialogo.boton_confirmar.click()
    assert dialogo.result() == QDialog.DialogCode.Accepted
