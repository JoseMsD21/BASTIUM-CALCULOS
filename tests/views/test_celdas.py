"""Sprint 127: cifras alineadas a la derecha y nombre legible del area."""

from PySide6.QtCore import Qt

from app.views.celdas import ALINEACION_NUMERO, celda_numero, etiqueta_area


def test_celda_numero_conserva_el_texto_y_se_alinea_a_la_derecha(qtbot):
    celda = celda_numero("427900.00")

    assert celda.text() == "427900.00"
    assert celda.textAlignment() == ALINEACION_NUMERO
    assert ALINEACION_NUMERO & Qt.AlignmentFlag.AlignRight


def test_celda_numero_acepta_decimal_y_enteros(qtbot):
    from decimal import Decimal

    assert celda_numero(Decimal("1.50")).text() == "1.50"
    assert celda_numero(3).text() == "3"


def test_etiqueta_area_traduce_el_codigo_y_respeta_lo_desconocido():
    assert etiqueta_area("CIVIL_FAMILIA") == "Civil / Familia"
    assert etiqueta_area("HONORARIOS") == "Honorarios / Litigio"
    assert etiqueta_area("OTRA_COSA") == "OTRA_COSA"
