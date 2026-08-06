from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from app.core import theme_colors as colores
from app.core.apariencia import aplicar_tema, construir_paleta


def test_construir_paleta_usa_los_colores_de_marca(qtbot):
    paleta = construir_paleta()

    assert paleta.color(QPalette.ColorRole.Window).name().upper() == colores.FONDO
    assert paleta.color(QPalette.ColorRole.Highlight).name().upper() == colores.PRIMARIO
    assert paleta.color(QPalette.ColorRole.ButtonText).name().upper() == colores.PRIMARIO


def test_aplicar_tema_registra_la_fuente_y_carga_el_stylesheet(qtbot):
    app = QApplication.instance()

    familia = aplicar_tema(app)

    assert familia == "Ancizar Sans"
    assert app.font().family() == "Ancizar Sans"
    assert "QPushButton" in app.styleSheet()
