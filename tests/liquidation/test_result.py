from datetime import date
from decimal import Decimal
from app.engine.liquidation.models import LiquidationItem, RunningBalance, PendingDebt
from app.engine.liquidation.result import LiquidationResult

def test_liquidation_result_aggregation():
    debt1 = PendingDebt(Decimal("1000"), Decimal("100"), Decimal("0"))
    debt2 = PendingDebt(Decimal("1000"), Decimal("200"), Decimal("0"))
    
    item1 = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Cuota",
        capital_base=Decimal("1000"),
        interest_rate=Decimal("0.10"),
        interest_amount=Decimal("100"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("0"),
        balance=RunningBalance(date(2026, 1, 1), debt1, "NEW_INSTALLMENT")
    )
    
    item2 = LiquidationItem(
        date=date(2026, 2, 1),
        concept="Interés",
        capital_base=Decimal("1000"),
        interest_rate=Decimal("0.10"),
        interest_amount=Decimal("100"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("0"),
        balance=RunningBalance(date(2026, 2, 1), debt2, "INTEREST_ACCRUAL")
    )
    
    result = LiquidationResult([item1, item2])
    
    assert result.total_interest_accrued() == Decimal("200")
    assert result.final_balance().total() == Decimal("1200")