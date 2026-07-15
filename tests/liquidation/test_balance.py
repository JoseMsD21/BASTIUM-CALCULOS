from decimal import Decimal
import pytest
from app.engine.liquidation.models import PendingDebt
from app.engine.liquidation.balance import BalanceEngine

def test_add_principal_creates_new_state():
    initial_debt = PendingDebt(Decimal("1000.00"), Decimal("0.00"), Decimal("0.00"))
    new_debt = BalanceEngine.add_principal(initial_debt, Decimal("500.00"))
    
    assert new_debt.principal == Decimal("1500.00")
    assert initial_debt.principal == Decimal("1000.00") # Garantiza inmutabilidad

def test_accrue_interest():
    initial_debt = PendingDebt(Decimal("1000.00"), Decimal("50.00"), Decimal("0.00"))
    new_debt = BalanceEngine.add_interest(initial_debt, Decimal("12.50"))
    
    assert new_debt.interest == Decimal("62.50")
    assert new_debt.total() == Decimal("1062.50")

def test_accrue_indexation():
    initial_debt = PendingDebt(Decimal("1000.00"), Decimal("0.00"), Decimal("0.00"))
    new_debt = BalanceEngine.add_indexation(initial_debt, Decimal("35.00"))
    
    assert new_debt.indexation == Decimal("35.00")