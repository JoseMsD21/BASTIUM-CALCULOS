from datetime import date
from decimal import Decimal

from app.engine.audit.serialization import deserializar_resultado, serializar_resultado
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult


def _item(rate_source: str = "N/A") -> LiquidationItem:
    debt = PendingDebt(Decimal("300000.00"), Decimal("3000.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="INSTALLMENT")
    return LiquidationItem(
        date=date(2026, 1, 1),
        concept="Cuota enero",
        capital_base=Decimal("300000.00"),
        interest_rate=Decimal("1.00"),
        interest_amount=Decimal("3000.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source=rate_source,
    )


def test_round_trip_preserva_items_exactamente():
    resultado = LiquidationResult(items=[_item("Tasa pactada (Art. 1617 C.C.)"), _item()])

    json_str = serializar_resultado(resultado)
    reconstruido = deserializar_resultado(json_str)

    assert reconstruido == resultado


def test_round_trip_preserva_precision_decimal_y_tipos():
    resultado = LiquidationResult(items=[_item()])

    json_str = serializar_resultado(resultado)
    reconstruido = deserializar_resultado(json_str)

    item = reconstruido.items[0]
    assert item.capital_base == Decimal("300000.00")
    assert isinstance(item.capital_base, Decimal)
    assert item.date == date(2026, 1, 1)
    assert isinstance(item.date, date)
    assert isinstance(item.balance.debt, PendingDebt)


def test_serializar_produce_un_string_json():
    resultado = LiquidationResult(items=[_item()])
    json_str = serializar_resultado(resultado)
    assert isinstance(json_str, str)
    assert "Cuota enero" in json_str
