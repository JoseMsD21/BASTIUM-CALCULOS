import re

from app.core import theme_colors as colores

_HEX = re.compile(r"^#[0-9A-F]{6}$")


def test_todas_las_constantes_de_color_son_hex_de_6_digitos_en_mayusculas():
    valores = [
        v for k, v in vars(colores).items() if k.isupper() and isinstance(v, str)
    ]
    assert len(valores) >= 20
    for valor in valores:
        assert _HEX.match(valor), f"{valor!r} no es un hex #RRGGBB en mayusculas"


def test_primario_y_secundario_coinciden_con_los_colores_ya_usados_en_pdf():
    # app/reports/pdf.py define c_burgundy = "#ae1c21" y c_cream = "#f5f1e9"
    # (Sprint 31 los reutiliza como ancla de marca, en vez de inventar otros).
    assert colores.PRIMARIO == "#AE1C21"
    assert colores.SECUNDARIO == "#F5F1E9"


def test_destructivo_es_distinto_del_primario():
    assert colores.DESTRUCTIVO != colores.PRIMARIO
