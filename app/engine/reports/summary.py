from decimal import Decimal

from app.engine.liquidation.result import LiquidationResult


class ReportSummaryBuilder:
    """
    Capa de presentación de alto nivel.
    Extrae las métricas globales de la liquidación para el auto interlocutorio.
    """
    def build_summary(self, result: LiquidationResult) -> dict[str, str]:
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

    def build_renta_liquida(self, result: LiquidationResult) -> dict | None:
        """Formatea LiquidationResult.renta_liquida para renderizar en un bloque separado del
        balance de deuda (GUI/PDF/Word) -- None si el resultado no tiene una obligacion
        RENTA_LIQUIDA (la inmensa mayoria de liquidaciones, de cualquier area distinta de
        Tributario)."""
        if result.renta_liquida is None:
            return None
        rl = result.renta_liquida
        return {
            "ingresos_netos": self._format(rl.ingresos_netos),
            "renta_bruta": self._format(rl.renta_bruta),
            "renta_liquida": self._format(rl.renta_liquida),
            "hubo_perdida_liquida": "Sí" if rl.hubo_perdida_liquida else "No",
            "renta_liquida_gravable": self._format(rl.renta_liquida_gravable),
        }

    def _build_zero_summary(self) -> dict[str, str]:
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