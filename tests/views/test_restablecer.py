"""Tests de ConfirmarRestablecerDialog (Sprint 66, Task 3): exige escribir
"RESTABLECER" exacto para habilitar el boton de confirmar -- misma filosofia
de "sin papelera, definitivo tras confirmar" que ya usan Eliminar en
Obligaciones/Abonos (Sprint 60)."""

from unittest.mock import patch

from PySide6.QtWidgets import QDialog

from app.views.restablecer import ConfirmarRestablecerDialog, RestablecerView


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
    dialogo = ConfirmarRestablecerDialog()
    qtbot.addWidget(dialogo)
    dialogo.campo_confirmacion.setText("RESTABLECER")
    dialogo.boton_confirmar.click()
    assert dialogo.result() == QDialog.DialogCode.Accepted


def test_restablecer_view_tiene_boton_destructivo(qtbot):
    vista = RestablecerView()
    qtbot.addWidget(vista)
    assert vista.boton_restablecer.property("class") == "destructive"


def test_restablecer_view_no_hace_nada_si_se_cancela_la_confirmacion(qtbot, tmp_path):
    vista = RestablecerView()
    qtbot.addWidget(vista)

    with (
        patch("app.views.restablecer.ConfirmarRestablecerDialog.exec", return_value=0),
        patch("app.views.restablecer.crear_backup_de_base_de_datos") as mock_backup,
        patch("app.views.restablecer.restablecer_datos_fabrica") as mock_restablecer,
    ):
        vista._restablecer()

    mock_backup.assert_not_called()
    mock_restablecer.assert_not_called()


def test_restablecer_view_confirmado_llama_backup_y_restablecer_en_orden(qtbot, tmp_path):
    vista = RestablecerView()
    qtbot.addWidget(vista)
    orden_llamadas = []

    with (
        patch(
            "app.views.restablecer.ConfirmarRestablecerDialog.exec",
            return_value=QDialog.DialogCode.Accepted,
        ),
        patch(
            "app.views.restablecer.crear_backup_de_base_de_datos",
            side_effect=lambda: orden_llamadas.append("backup") or (tmp_path / "x.bak"),
        ) as mock_backup,
        patch(
            "app.views.restablecer.restablecer_datos_fabrica",
            side_effect=lambda: orden_llamadas.append("restablecer"),
        ) as mock_restablecer,
        patch("app.views.restablecer.QMessageBox.information"),
    ):
        vista._restablecer()

    mock_backup.assert_called_once()
    mock_restablecer.assert_called_once()
    assert orden_llamadas == ["backup", "restablecer"]


def test_restablecer_view_no_borra_si_el_backup_falla(qtbot):
    vista = RestablecerView()
    qtbot.addWidget(vista)

    with (
        patch(
            "app.views.restablecer.ConfirmarRestablecerDialog.exec",
            return_value=QDialog.DialogCode.Accepted,
        ),
        patch(
            "app.views.restablecer.crear_backup_de_base_de_datos",
            side_effect=OSError("disco lleno"),
        ),
        patch("app.views.restablecer.restablecer_datos_fabrica") as mock_restablecer,
        patch("app.views.restablecer.QMessageBox.critical") as mock_critical,
    ):
        vista._restablecer()

    mock_restablecer.assert_not_called()
    mock_critical.assert_called_once()
