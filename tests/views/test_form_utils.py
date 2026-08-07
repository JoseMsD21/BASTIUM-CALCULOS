from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit

from app.views.form_utils import set_row_visible


def test_set_row_visible_oculta_tambien_la_etiqueta_generada_por_addrow(qtbot):
    """QFormLayout.addRow(str, widget) genera un QLabel que widget.setVisible()
    solo, NO oculta -- ese es exactamente el bug de labels huerfanas del
    Sprint 39. set_row_visible() debe ocultar la fila completa."""
    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    campo = QLineEdit()
    layout.addRow("Campo de prueba", campo)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, campo, False)

    etiqueta = layout.labelForField(campo)
    assert etiqueta is not None
    assert campo.isVisible() is False
    assert etiqueta.isVisible() is False


def test_set_row_visible_muestra_tambien_la_etiqueta(qtbot):
    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    campo = QLineEdit()
    layout.addRow("Campo de prueba", campo)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, campo, False)
    set_row_visible(layout, campo, True)

    etiqueta = layout.labelForField(campo)
    assert campo.isVisible() is True
    assert etiqueta.isVisible() is True


def test_set_row_visible_no_falla_si_el_widget_no_tiene_etiqueta(qtbot):
    """addRow(widget) de un solo argumento (ej. un QCheckBox que ocupa toda la
    fila) no genera QLabel -- labelForField() devuelve None. set_row_visible
    debe seguir funcionando sin reventar."""
    from PySide6.QtWidgets import QCheckBox

    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    check = QCheckBox("Solo")
    layout.addRow(check)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, check, False)

    assert check.isVisible() is False
