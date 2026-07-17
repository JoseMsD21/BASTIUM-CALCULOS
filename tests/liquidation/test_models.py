import pytest
from datetime import date
from decimal import Decimal
from dataclasses import FrozenInstanceError

from app.engine.liquidation.models import (
    Installment, PaymentAllocation, PendingDebt,
    RunningBalance, LiquidationItem
)

def test_installment_creation():
    inst = Installment(
        due_date=date(2022, 1, 1),
        principal=Decimal("300000.00"),
        concept="Cuota enero",
        remaining=Decimal("300000.00")
    )
    assert inst.principal == Decimal("300000.00")
    assert inst.state == "PENDING"

def test_payment_allocation_math():
    allocation = PaymentAllocation(
        payment_date=date(2022, 1, 15),
        total_payment=Decimal("500000.00"),
        to_interest=Decimal("120000.00"),
        to_indexation=Decimal("80000.00"),
        to_principal=Decimal("300000.00")
    )
    # Validamos que la suma de las partes equivalga al pago total
    assert allocation.total_payment == (
        allocation.to_interest + allocation.to_indexation + allocation.to_principal
    )

def test_pending_debt_total():
    debt = PendingDebt(
        principal=Decimal("1000000.00"),
        interest=Decimal("150000.00"),
        indexation=Decimal("50000.00")
    )
    assert debt.total() == Decimal("1200000.00")

def test_immutability_enforcement():
    debt = PendingDebt(Decimal("100.00"), Decimal("0.00"), Decimal("0.00"))
    rb = RunningBalance(
        date=date(2022, 1, 1),
        debt=debt,
        event_type="NEW_INSTALLMENT"
    )
    # El sistema DEBE fallar si intentamos alterar la historia
    with pytest.raises(FrozenInstanceError):
        rb.event_type = "MODIFIED"

def test_liquidation_item_rate_source_por_defecto_es_na():
    debt = PendingDebt(Decimal("300000.00"), Decimal("3000.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2022, 1, 1), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2022, 1, 1),
        concept="Cuota enero",
        capital_base=Decimal("300000.00"),
        interest_rate=Decimal("1.00"),
        interest_amount=Decimal("3000.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    assert item.rate_source == "N/A"


def test_liquidation_item_acepta_rate_source_explicito():
    debt = PendingDebt(Decimal("300000.00"), Decimal("3000.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2022, 1, 1), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2022, 1, 1),
        concept="Cuota enero",
        capital_base=Decimal("300000.00"),
        interest_rate=Decimal("1.00"),
        interest_amount=Decimal("3000.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source="Tasa pactada en la obligación (Art. 1617 C.C.)",
    )
    assert item.rate_source == "Tasa pactada en la obligación (Art. 1617 C.C.)"