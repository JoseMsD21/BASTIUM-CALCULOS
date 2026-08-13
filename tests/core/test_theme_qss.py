from pathlib import Path

_RESOURCES_DIR = Path(__file__).resolve().parents[2] / "resources"
THEME_QSS = _RESOURCES_DIR / "theme.qss"
THEME_DARK_QSS = _RESOURCES_DIR / "theme_dark.qss"


def test_theme_claro_define_indicador_de_checkbox():
    contenido = THEME_QSS.read_text(encoding="utf-8")
    assert "QCheckBox::indicator {" in contenido
    assert "QCheckBox::indicator:checked {" in contenido
    assert "QCheckBox::indicator:hover {" in contenido
    assert "QCheckBox::indicator:disabled {" in contenido


def test_theme_claro_indicador_checkbox_usa_colores_de_marca():
    contenido = THEME_QSS.read_text(encoding="utf-8")
    bloque_normal = contenido.split("QCheckBox::indicator {", 1)[1].split("}", 1)[0]
    assert "#D8CDBB" in bloque_normal  # borde estandar sin marcar
    bloque_checked = contenido.split("QCheckBox::indicator:checked {", 1)[1].split("}", 1)[0]
    assert "#AE1C21" in bloque_checked  # primario burdeos al marcar


def test_theme_oscuro_define_indicador_de_checkbox():
    contenido = THEME_DARK_QSS.read_text(encoding="utf-8")
    assert "QCheckBox::indicator {" in contenido
    assert "QCheckBox::indicator:checked {" in contenido
    assert "QCheckBox::indicator:hover {" in contenido
    assert "QCheckBox::indicator:disabled {" in contenido


def test_theme_oscuro_indicador_checkbox_usa_colores_de_marca():
    contenido = THEME_DARK_QSS.read_text(encoding="utf-8")
    bloque_normal = contenido.split("QCheckBox::indicator {", 1)[1].split("}", 1)[0]
    assert "#4A4039" in bloque_normal  # borde estandar sin marcar (modo oscuro)
    bloque_checked = contenido.split("QCheckBox::indicator:checked {", 1)[1].split("}", 1)[0]
    assert "#D9484D" in bloque_checked  # primario burdeos claro al marcar
