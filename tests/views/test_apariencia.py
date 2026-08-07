import re

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


def _color_de_fondo(stylesheet: str, clase: str) -> str:
    """Extrae el background-color del bloque QPushButton[class="<clase>"] { ... }
    (sin pseudo-estado :hover/:pressed/:disabled) del stylesheet completo."""
    patron = rf'QPushButton\[class="{clase}"\]\s*\{{([^}}]*)\}}'
    bloque = re.search(patron, stylesheet)
    assert bloque, f'No se encontro el selector QPushButton[class="{clase}"] en el stylesheet'
    color = re.search(r"background-color:\s*(#[0-9A-Fa-f]{6})", bloque.group(1))
    assert color, f'El selector QPushButton[class="{clase}"] no define background-color'
    return color.group(1).upper()


def test_las_3_clases_de_boton_son_visualmente_distinguibles(qtbot):
    """Sprint 36: primary/secondary/destructive deben producir colores de fondo
    distintos entre si -- de lo contrario la jerarquia visual de botones no
    cumpliria su proposito (que el riesgo/importancia de la accion se distinga
    de un vistazo)."""
    app = QApplication.instance()
    aplicar_tema(app)
    stylesheet = app.styleSheet()

    color_primary = _color_de_fondo(stylesheet, "primary")
    color_secondary = _color_de_fondo(stylesheet, "secondary")
    color_destructive = _color_de_fondo(stylesheet, "destructive")

    colores_por_clase = {color_primary, color_secondary, color_destructive}
    assert len(colores_por_clase) == 3, (
        "Las 3 clases de boton deben tener colores de fondo distintos entre si: "
        f"primary={color_primary} secondary={color_secondary} destructive={color_destructive}"
    )
