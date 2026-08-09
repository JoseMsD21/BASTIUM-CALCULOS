from decimal import Decimal

from app.engine.liquidation.result import LiquidationResult


class ReportTableBuilder:
    """
    Capa de presentación:
    Transforma el rigor matemático del LiquidationResult en una matriz 
    de diccionarios formateados, listos para ser inyectados en PDF, Excel o UI.
    """

    def build_matrix(self, result: LiquidationResult) -> list[dict[str, str]]:
        matrix = []

        for item in result.items:
            concepto = item.concept
            if item.prescrita:
                # Sprint 42: decision del despacho -- la obligacion prescrita se sigue
                # incluyendo en el calculo (no se excluye del total), solo se marca
                # informativamente en el texto para que el abogado la note al leer el
                # reporte. "prescrita" (booleano) tambien queda expuesto aparte para que
                # pdf.py/word.py puedan resaltar la fila sin tener que parsear el texto.
                concepto = f"⚠ {concepto} — Obligación prescrita, no exigible"
            row = {
                "fecha": item.date.strftime("%d/%m/%Y"),
                "concepto": concepto,
                "base_capital": self._format_currency(item.capital_base),
                "tasa": self._format_percent(item.interest_rate),
                "interes": self._format_currency(item.interest_amount),
                "indexacion": self._format_currency(item.indexation_amount),
                "pago": self._format_currency(item.payment_amount),
                # El estado resultante después del evento
                "saldo_capital": self._format_currency(item.balance.debt.principal),
                "saldo_interes": self._format_currency(item.balance.debt.interest),
                "saldo_total": self._format_currency(item.balance.debt.total()),
                "prescrita": item.prescrita,
            }
            matrix.append(row)

        return matrix

    def _format_currency(self, value: Decimal) -> str:
        # Formatea agregando comas de miles y dos decimales fijos
        return f"${value:,.2f}"

    def _format_percent(self, value: Decimal) -> str:
        return f"{value:,.2f}%"