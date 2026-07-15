from typing import Dict
from decimal import Decimal
from app.engine.liquidation.result import LiquidationResult

class ReportSummaryBuilder:
    """
    Capa de presentación de alto nivel.
    Extrae las métricas globales de la liquidación para el auto interlocutorio.
    """
    def build_summary(self, result: LiquidationResult) -> Dict[str, str]:
        if result.is_empty():
            return self._build_zero_summary()

        final_debt = result.final_balance()
        total_payments = result.total_payments_applied()
        total_interest_generated = result.total_interest_accrued()

        return {
            "total_abonos": self._format(total_payments),
            "total_intereses_generados": self._format(total_interest_generated),
            "saldo_final_capital": self._format(final_debt.principal),
            "saldo_final_intereses": self._format(final_debt.interest),
            "saldo_final_indexacion": self._format(final_debt.indexation),
            "gran_total_adeudado": self._format(final_debt.total())
        }

    def _build_zero_summary(self) -> Dict[str, str]:
        zero = self._format(Decimal("0.00"))
        return {
            "total_abonos": zero,
            "total_intereses_generados": zero,
            "saldo_final_capital": zero,
            "saldo_final_intereses": zero,
            "saldo_final_indexacion": zero,
            "gran_total_adeudado": zero
        }

    def _format(self, value: Decimal) -> str:
        return f"${value:,.2f}"