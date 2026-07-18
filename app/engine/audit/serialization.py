import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult


def _encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Tipo no serializable en snapshot de auditoría: {type(value)!r}")


def serializar_resultado(resultado: LiquidationResult) -> str:
    """Snapshot JSON exacto de un LiquidationResult, para reconstrucción sin recalcular."""
    items = [asdict(item) for item in resultado.items]
    return json.dumps({"items": items}, default=_encode, ensure_ascii=False)


def deserializar_resultado(json_str: str) -> LiquidationResult:
    """Reconstruye un LiquidationResult exactamente desde un snapshot de serializar_resultado."""
    data = json.loads(json_str)
    items = [_item_desde_dict(item) for item in data["items"]]
    return LiquidationResult(items)


def _item_desde_dict(data: dict) -> LiquidationItem:
    balance_data = data["balance"]
    debt_data = balance_data["debt"]

    debt = PendingDebt(
        principal=Decimal(debt_data["principal"]),
        interest=Decimal(debt_data["interest"]),
        indexation=Decimal(debt_data["indexation"]),
    )
    balance = RunningBalance(
        date=date.fromisoformat(balance_data["date"]),
        debt=debt,
        event_type=balance_data["event_type"],
    )
    return LiquidationItem(
        date=date.fromisoformat(data["date"]),
        concept=data["concept"],
        capital_base=Decimal(data["capital_base"]),
        interest_rate=Decimal(data["interest_rate"]),
        interest_amount=Decimal(data["interest_amount"]),
        indexation_amount=Decimal(data["indexation_amount"]),
        payment_amount=Decimal(data["payment_amount"]),
        balance=balance,
        rate_source=data["rate_source"],
    )
