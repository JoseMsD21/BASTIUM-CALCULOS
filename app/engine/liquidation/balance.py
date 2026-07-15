from decimal import Decimal
from app.engine.liquidation.models import PendingDebt

class BalanceEngine:
    """
    Motor puro para la transición del estado de la deuda.
    Garantiza que toda modificación produzca una nueva instancia inmutable,
    preservando la integridad del historial auditivo.
    """
    
    @staticmethod
    def add_principal(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return PendingDebt(
            principal=debt.principal + amount,
            interest=debt.interest,
            indexation=debt.indexation
        )

    @staticmethod
    def add_interest(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return PendingDebt(
            principal=debt.principal,
            interest=debt.interest + amount,
            indexation=debt.indexation
        )

    @staticmethod
    def add_indexation(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return PendingDebt(
            principal=debt.principal,
            interest=debt.interest,
            indexation=debt.indexation + amount
        )