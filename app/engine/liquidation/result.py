from dataclasses import dataclass
from decimal import Decimal
from typing import List
from app.engine.liquidation.models import LiquidationItem, PendingDebt

@dataclass(frozen=True)
class LiquidationResult:
    """
    Representa el veredicto y cronología final del proceso de liquidación.
    Expone métodos para extraer métricas listas para interfaces y PDFs.
    """
    items: List[LiquidationItem]

    def total_interest_accrued(self) -> Decimal:
        return sum((item.interest_amount for item in self.items), Decimal("0.00"))

    def total_payments_applied(self) -> Decimal:
        return sum((item.payment_amount for item in self.items), Decimal("0.00"))

    def final_balance(self) -> PendingDebt:
        if not self.items:
            return PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        return self.items[-1].balance.debt

    def is_empty(self) -> bool:
        return len(self.items) == 0