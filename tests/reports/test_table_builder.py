import pytest
from datetime import date
from decimal import Decimal
from app.engine.liquidation.models import LiquidationItem, RunningBalance, PendingDebt
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