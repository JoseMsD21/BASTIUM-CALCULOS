from datetime import date
from decimal import Decimal
from app.engine.liquidation.models import PendingDebt
from app.engine.liquidation.allocation import AllocationEngine

def test_full_payment_allocation():
    debt = PendingDebt(Decimal("1000.00"), Decimal("200.00"), Decimal("50.00"))
    payment_amount = Decimal("1250.00")
    
    allocation, new_debt, remainder = AllocationEngine.allocate(payment_amount, debt, date(2026, 7, 12))
    
    assert allocation.to_indexation == Decimal("50.00")
    assert allocation.to_interest == Decimal("200.00")
    assert allocation.to_principal == Decimal("1000.00")
    assert new_debt.total() == Decimal("0.00")
    assert remainder == Decimal("0.00")

def test_partial_payment_interest_only():
    debt = PendingDebt(Decimal("1000.00"), Decimal("200.00"), Decimal("50.00"))
    payment_amount = Decimal("150.00")
    
    allocation, new_debt, remainder = AllocationEngine.allocate(payment_amount, debt, date(2026, 7, 12))
    
    assert allocation.to_indexation == Decimal("50.00")
    assert allocation.to_interest == Decimal("100.00")
    assert allocation.to_principal == Decimal("0.00")
    
    # El capital sigue intacto, los intereses bajaron a 100
    assert new_debt.principal == Decimal("1000.00")
    assert new_debt.interest == Decimal("100.00")
    assert new_debt.indexation == Decimal("0.00")
    assert remainder == Decimal("0.00")

def test_overpayment_generates_remainder():
    debt = PendingDebt(Decimal("500.00"), Decimal("0.00"), Decimal("0.00"))
    payment_amount = Decimal("600.00")
    
    allocation, new_debt, remainder = AllocationEngine.allocate(payment_amount, debt, date(2026, 7, 12))
    
    assert allocation.to_principal == Decimal("500.00")
    assert new_debt.total() == Decimal("0.00")
    assert remainder == Decimal("100.00") # Saldo a favor