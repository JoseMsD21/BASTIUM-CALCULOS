from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.table_builder import ReportTableBuilder


def test_table_builder_formats_currency_and_dates_correctly():
    # Simulamos el final de una liquidación
    debt = PendingDebt(Decimal("1500000.50"), Decimal("125000.00"), Decimal("0.00"))
    rb = RunningBalance(date(2026, 4, 15), debt, "PAYMENT")
    
    item = LiquidationItem(
        date=date(2026, 4, 15),
        concept="Abono a capital",
        capital_base=Decimal("1500000.50"),
        interest_rate=Decimal("1.5"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("500000.00"),
        balance=rb
    )
    
    result = LiquidationResult([item])
    builder = ReportTableBuilder()
    
    # Transformamos el objeto duro en datos listos para renderizar
    table_data = builder.build_matrix(result)
    
    assert len(table_data) == 1
    row = table_data[0]
    
    # Validamos que los formatos sean humanamente legibles para el juzgado
    assert row["fecha"] == "15/04/2026"
    assert row["concepto"] == "Abono a capital"
    assert row["base_capital"] == "$1,500,000.50"
    assert row["tasa"] == "1.50%"
    assert row["interes"] == "$0.00"
    assert row["pago"] == "$500,000.00"
    assert row["saldo_capital"] == "$1,500,000.50"
    assert row["saldo_interes"] == "$125,000.00"
    assert row["saldo_total"] == "$1,625,000.50"
    assert row["prescrita"] is False
    assert row["saldo_a_favor"] == "$0.00"


def test_table_builder_marca_fila_prescrita_en_el_concepto_y_expone_bandera():
    # Sprint 42: decision del despacho -- la obligacion prescrita se sigue
    # incluyendo en el calculo, solo se marca informativamente en el reporte.
    debt = PendingDebt(Decimal("1000000.00"), Decimal("0.00"), Decimal("0.00"))
    rb = RunningBalance(date(2015, 1, 1), debt, "INSTALLMENT")

    item = LiquidationItem(
        date=date(2015, 1, 1),
        concept="Capital antiguo",
        capital_base=Decimal("1000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=rb,
        prescrita=True,
    )

    result = LiquidationResult([item])
    row = ReportTableBuilder().build_matrix(result)[0]

    assert row["prescrita"] is True
    assert "Capital antiguo" in row["concepto"]
    assert "prescrita" in row["concepto"].lower()
    assert "no exigible" in row["concepto"].lower()


def test_table_builder_fila_no_prescrita_no_modifica_el_texto_del_concepto():
    debt = PendingDebt(Decimal("1000000.00"), Decimal("0.00"), Decimal("0.00"))
    rb = RunningBalance(date(2026, 1, 1), debt, "INSTALLMENT")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Capital vigente",
        capital_base=Decimal("1000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=rb,
    )

    row = ReportTableBuilder().build_matrix(LiquidationResult([item]))[0]

    assert row["prescrita"] is False
    assert row["concepto"] == "Capital vigente"


def test_table_builder_expone_saldo_a_favor_formateado_igual_que_pago():
    # Sprint 46: mismo patron que "prescrita" (Sprint 42) -- la clave siempre
    # esta presente en la fila, formateada en "$0.00" cuando no aplica, y
    # los consumidores (pdf.py/word.py) deciden si la muestran.
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    rb = RunningBalance(date(2026, 1, 10), debt, "PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 10),
        concept="Pago",
        capital_base=Decimal("7000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=rb,
        saldo_a_favor=Decimal("3000000.00"),
    )

    row = ReportTableBuilder().build_matrix(LiquidationResult([item]))[0]

    assert row["saldo_a_favor"] == "$3,000,000.00"