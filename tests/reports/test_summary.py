import pytest
from datetime import date
from decimal import Decimal
from app.engine.liquidation.models import LiquidationItem, RunningBalance, PendingDebt
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder

def test_summary_builder_aggregates_totals_correctly():
    debt = PendingDebt(Decimal("1000000"), Decimal("250000"), Decimal("0"))
    rb = RunningBalance(date(2026, 4, 15), debt, "PAYMENT")
    
    item = LiquidationItem(
        date=date(2026, 4, 15),
        concept="Abono",
        capital_base=Decimal("1000000"),
        interest_rate=Decimal("1.5"),
        interest_amount=Decimal("10000"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("500000"),
        balance=rb
    )
    
    result = LiquidationResult([item])
    builder = ReportSummaryBuilder()
    summary = builder.build_summary(result)
    
    assert summary["total_abonos"] == "$500,000.00"
    assert summary["saldo_final_capital"] == "$1,000,000.00"
    assert summary["saldo_final_intereses"] == "$250,000.00"
    assert summary["gran_total_adeudado"] == "$1,250,000.00"