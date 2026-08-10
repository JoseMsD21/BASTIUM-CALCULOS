import re

from PySide6.QtGui import QPalette
from PySide6.QtWidgets import QApplication

from app.core import theme_colors as colores
from app.core import theme_colors_dark as colores_oscuro
from app.core.apariencia import (
    MODO_CLARO,
    MODO_OSCURO,
    aplicar_tema,
    cargar_modo_tema,
    construir_paleta,
    guardar_modo_tema,
)


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


def test_construir_paleta_modo_claro_es_el_default(qtbot):
    """El modo "claro" (Sprint 31, sin cambios visuales) sigue siendo el default
    al no pasar `modo` explicitamente -- Sprint 50 no debe alterar el
    comportamiento existente."""
    assert construir_paleta() == construir_paleta(MODO_CLARO)


def test_construir_paleta_modo_oscuro_usa_los_colores_oscuros(qtbot):
    paleta = construir_paleta(MODO_OSCURO)

    assert paleta.color(QPalette.ColorRole.Window).name().upper() == colores_oscuro.FONDO
    assert paleta.color(QPalette.ColorRole.Highlight).name().upper() == colores_oscuro.PRIMARIO
    assert paleta.color(QPalette.ColorRole.ButtonText).name().upper() == colores_oscuro.PRIMARIO


def test_aplicar_tema_modo_oscuro_carga_el_stylesheet_oscuro(qtbot):
    app = QApplication.instance()

    aplicar_tema(app, MODO_OSCURO)

    assert "QPushButton" in app.styleSheet()
    assert colores_oscuro.FONDO.lower() in app.styleSheet().lower()

    # Vuelve al modo claro para no filtrar estado hacia otros tests de este modulo.
    aplicar_tema(app, MODO_CLARO)


def test_guardar_y_cargar_modo_tema_persiste_via_qsettings(qtbot):
    """tests/conftest.py::_qsettings_aislado redirige QSettings a un directorio
    temporal por test (mismo patron reutilizado de MainWindow._crear_settings(),
    Sprint 37), asi que guardar_modo_tema()/cargar_modo_tema() aqui no tocan la
    configuracion real del usuario."""
    guardar_modo_tema(MODO_OSCURO)

    assert cargar_modo_tema() == MODO_OSCURO


def test_cargar_modo_tema_cae_a_claro_en_el_primer_arranque(qtbot):
    # Sin QSettings previo (tmp_path vacio por test) debe caer a "claro".
    assert cargar_modo_tema() == MODO_CLARO


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
