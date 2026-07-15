from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.views.liquidaciones import ResultadoLiquidacionView


def _resultado_de_prueba() -> LiquidationResult:
    debt = PendingDebt(principal=Decimal("427900.00"), interest=Decimal("1200.50"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Corte final de liquidacion",
        capital_base=Decimal("427900.00"),
        interest_rate=Decimal("6.00"),
        interest_amount=Decimal("1200.50"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return LiquidationResult(items=[item])


def test_muestra_una_fila_por_item_de_liquidacion(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba())

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 1).text() == "Corte final de liquidacion"


def test_muestra_los_totales(qtbot):
    view = ResultadoLiquidacionView()
    qtbot.addWidget(view)

    view.mostrar(_resultado_de_prueba())

    assert "1200.50" in view.etiqueta_interes_total.text()
    # NOTA (bug detectado durante implementación): el plan original esperaba "427900.00"
    # aquí, pero PendingDebt.total() = principal + interest + indexation = 429100.50, no
    # solo el principal. El saldo final correcto incluye el interés acumulado, por lo que
    # se corrige la aserción para reflejar el comportamiento real y matemáticamente
    # correcto de final_balance().total(), en vez de forzar la vista a un cálculo erróneo.
    assert "429100.50" in view.etiqueta_saldo_final.text()
