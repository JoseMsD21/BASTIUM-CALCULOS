from dataclasses import dataclass, field
from decimal import Decimal

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

    `alertas` (Sprint 43): mensajes de advertencia NO bloqueantes generados durante
    liquidar() -- la liquidacion se completa igual y el saldo no cambia por su
    presencia, pero el abogado debe revisarlos (ej. "Doble Actualización Prohibida"
    en Laboral cuando IPC y la indemnizacion moratoria coinciden sobre el mismo
    rubro/periodo, o "Improcedente por acumulación" en Honorarios). Reutiliza el
    mismo criterio de "feedback no bloqueante" del Sprint 36 (`app/views/toast.py`)
    -- la vista (`expediente_detalle.py`) los muestra con `mostrar_toast(tipo="warning")`
    en vez de un `QMessageBox` modal. Default lista vacia: ninguna liquidacion previa
    a este sprint construye `LiquidationResult` con este argumento, asi que el default
    preserva el comportamiento exacto de siempre."""
    items: list[LiquidationItem]
    renta_liquida: RentaLiquidaGravableResult | None = None
    alertas: list[str] = field(default_factory=list)

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
