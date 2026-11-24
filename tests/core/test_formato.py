"""Sprint 129: formato unico de moneda y porcentaje (pantalla + PDF + Word)."""

from decimal import Decimal

from app.core.formato import formatear_moneda, formatear_porcentaje
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder


def test_moneda_con_separador_de_miles_y_dos_decimales():
    assert formatear_moneda(Decimal("1500000")) == "$1,500,000.00"
    assert formatear_moneda(Decimal("427900.5")) == "$427,900.50"
    assert formatear_moneda(0) == "$0.00"


def test_moneda_redondea_half_up_solo_al_mostrar():
    assert formatear_moneda(Decimal("0.125")) == "$0.13"


def test_porcentaje():
    assert formatear_porcentaje(Decimal("6")) == "6.00%"


def test_los_reportes_usan_el_mismo_formato_que_la_pantalla():
    """El PDF y el Word no cambian: siguen mostrando "$1,500,000.00"."""
    valor = Decimal("1500000.5")
    assert formatear_moneda(valor) == "$1,500,000.50"
    assert ReportTableBuilder()._format_currency(valor) == formatear_moneda(valor)
    assert ReportSummaryBuilder()._format(valor) == "$1,500,000.50"
