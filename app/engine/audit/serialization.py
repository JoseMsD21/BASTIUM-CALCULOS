import json
from dataclasses import asdict
from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult


def _encode(value):
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError(f"Tipo no serializable en snapshot de auditoría: {type(value)!r}")


def serializar_resultado(resultado: LiquidationResult) -> str:
    """Snapshot JSON exacto de un LiquidationResult, para reconstrucción sin recalcular."""
    items = [asdict(item) for item in resultado.items]
    renta_liquida = asdict(resultado.renta_liquida) if resultado.renta_liquida is not None else None
    return json.dumps(
        {"items": items, "renta_liquida": renta_liquida}, default=_encode, ensure_ascii=False
    )


def deserializar_resultado(json_str: str) -> LiquidationResult:
    """Reconstruye un LiquidationResult exactamente desde un snapshot de serializar_resultado.
    Usa .get() para 'renta_liquida' porque los snapshots guardados antes del Sprint 15 no
    tienen esa clave -- debe seguir reconstruyendo sin KeyError (misma cautela que ya motivo
    el bug de auditoria documentado en el Sprint 23)."""
    data = json.loads(json_str)
    items = [_item_desde_dict(item) for item in data["items"]]
    renta_liquida = _renta_liquida_desde_dict(data.get("renta_liquida"))
    return LiquidationResult(items=items, renta_liquida=renta_liquida)


def _item_desde_dict(data: dict) -> LiquidationItem:
    # rate_source y saldo_a_favor usan .get() con el mismo default del dataclass --
    # a diferencia de los demas campos, ambos se agregaron a LiquidationItem despues
    # de que existieran AuditLog en produccion, asi que snapshots viejos no tienen
    # esas claves (bug real de Sprint 23). El resto de campos son intencionalmente
    # obligatorios: si faltan, la fila esta genuinamente incompleta y debe fallar.
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
        rate_source=data.get("rate_source", "N/A"),
        saldo_a_favor=Decimal(data.get("saldo_a_favor", "0.00")),
    )


def _renta_liquida_desde_dict(data: dict | None) -> RentaLiquidaGravableResult | None:
    if data is None:
        return None
    return RentaLiquidaGravableResult(
        ingresos_netos=Decimal(data["ingresos_netos"]),
        renta_bruta=Decimal(data["renta_bruta"]),
        renta_liquida=Decimal(data["renta_liquida"]),
        hubo_perdida_liquida=data["hubo_perdida_liquida"],
        renta_liquida_gravable=Decimal(data["renta_liquida_gravable"]),
    )
