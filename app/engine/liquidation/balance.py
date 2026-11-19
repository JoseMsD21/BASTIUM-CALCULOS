from dataclasses import replace
from decimal import Decimal

from app.engine.liquidation.models import PendingDebt


class BalanceEngine:
    """
    Motor puro para la transición del estado de la deuda.
    Garantiza que toda modificación produzca una nueva instancia inmutable,
    preservando la integridad del historial auditivo.

    Usa `dataclasses.replace` para que cada transicion conserve los componentes
    que no toca -- en particular `costas` (Sprint 79), que ninguna transicion de
    capital/interes/indexacion debe perder.
    """

    @staticmethod
    def add_principal(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return replace(debt, principal=debt.principal + amount)

    @staticmethod
    def add_interest(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return replace(debt, interest=debt.interest + amount)

    @staticmethod
    def add_indexation(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        return replace(debt, indexation=debt.indexation + amount)

    @staticmethod
    def add_costas(debt: PendingDebt, amount: Decimal) -> PendingDebt:
        """Sprint 79: costas procesales -- componente aparte que nunca genera interes."""
        return replace(debt, costas=debt.costas + amount)

    @staticmethod
    def capitalize_interest(debt: PendingDebt) -> PendingDebt:
        """Anatocismo: capitaliza solo los intereses; las costas siguen aparte."""
        return replace(
            debt, principal=debt.principal + debt.interest, interest=Decimal("0.00")
        )
