from datetime import date
from decimal import Decimal
from typing import Tuple
from app.engine.liquidation.models import PendingDebt, PaymentAllocation

class AllocationEngine:
    """
    Motor de imputación de pagos basado en la prelación legal estricta:
    1. Gastos/Indexación
    2. Intereses
    3. Capital
    Retorna la asignación del pago, el nuevo estado de la deuda y el remanente (si aplica).
    """

    @staticmethod
    def allocate(payment_amount: Decimal, current_debt: PendingDebt, payment_date: date) -> Tuple[PaymentAllocation, PendingDebt, Decimal]:
        remainder = payment_amount
        
        # 1. Imputación a Indexación
        if remainder >= current_debt.indexation:
            to_indexation = current_debt.indexation
            remainder -= to_indexation
            new_indexation = Decimal("0.00")
        else:
            to_indexation = remainder
            new_indexation = current_debt.indexation - remainder
            remainder = Decimal("0.00")

        # 2. Imputación a Intereses
        if remainder >= current_debt.interest:
            to_interest = current_debt.interest
            remainder -= to_interest
            new_interest = Decimal("0.00")
        else:
            to_interest = remainder
            new_interest = current_debt.interest - remainder
            remainder = Decimal("0.00")

        # 3. Imputación a Capital
        if remainder >= current_debt.principal:
            to_principal = current_debt.principal
            remainder -= to_principal
            new_principal = Decimal("0.00")
        else:
            to_principal = remainder
            new_principal = current_debt.principal - remainder
            remainder = Decimal("0.00")

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal
        )

        new_debt = PendingDebt(
            principal=new_principal,
            interest=new_interest,
            indexation=new_indexation
        )

        return allocation, new_debt, remainder