from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
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


def test_liquidation_result_total_saldo_a_favor():
    debt = PendingDebt(Decimal("0"), Decimal("0"), Decimal("0"))
    item_sin_excedente = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Pago exacto",
        capital_base=Decimal("0"),
        interest_rate=Decimal("0"),
        interest_amount=Decimal("0"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("500000"),
        balance=RunningBalance(date(2026, 1, 1), debt, "PAYMENT"),
    )
    item_con_excedente = LiquidationItem(
        date=date(2026, 2, 1),
        concept="Pago con excedente",
        capital_base=Decimal("0"),
        interest_rate=Decimal("0"),
        interest_amount=Decimal("0"),
        indexation_amount=Decimal("0"),
        payment_amount=Decimal("7000000"),
        balance=RunningBalance(date(2026, 2, 1), debt, "PAYMENT"),
        saldo_a_favor=Decimal("3000000"),
    )

    result = LiquidationResult([item_sin_excedente, item_con_excedente])

    assert result.total_saldo_a_favor() == Decimal("3000000")