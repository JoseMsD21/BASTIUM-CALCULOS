from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from app.engine.liquidation.models import LiquidationItem, PendingDebt
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult

@dataclass(frozen=True)
class LiquidationResult:
    """
    Representa el veredicto y cronología final del proceso de liquidación.
    Expone métodos para extraer métricas listas para interfaces y PDFs.

    `renta_liquida` (Sprint 15): resultado opcional de depurar_renta_liquida_gravable(),
    poblado solo por TributarioStrategy cuando el expediente tiene una obligacion
    "RENTA_LIQUIDA". No participa del balance de deuda (items/PendingDebt) -- es
    informativo, deliberadamente separado (ver design spec, seccion "Renta Liquida
    Gravable no se mezcla con el saldo de deuda").
    """
    items: List[LiquidationItem]
    renta_liquida: Optional[RentaLiquidaGravableResult] = None

    def total_interest_accrued(self) -> Decimal:
        return sum((item.interest_amount for item in self.items), Decimal("0.00"))

    def total_payments_applied(self) -> Decimal:
        return sum((item.payment_amount for item in self.items), Decimal("0.00"))

    def total_saldo_a_favor(self) -> Decimal:
        return sum((item.saldo_a_favor for item in self.items), Decimal("0.00"))

    def final_balance(self) -> PendingDebt:
        if not self.items:
            return PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        return self.items[-1].balance.debt

    def is_empty(self) -> bool:
        return len(self.items) == 0
