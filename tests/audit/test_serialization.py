from datetime import date
from decimal import Decimal

import pytest

from app.engine.audit.serialization import deserializar_resultado, serializar_resultado
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.tax.renta_liquida import RentaLiquidaGravableResult


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


def test_round_trip_preserva_montos_no_cero_y_escalas_variadas():
    debt_1 = PendingDebt(Decimal("450000.5"), Decimal("1234.5"), Decimal("99.999"))
    balance_1 = RunningBalance(date=date(2026, 2, 1), debt=debt_1, event_type="INSTALLMENT")
    item_1 = LiquidationItem(
        date=date(2026, 2, 1),
        concept="Cuota febrero",
        capital_base=Decimal("450000.5"),
        interest_rate=Decimal("1.25"),
        interest_amount=Decimal("1234.5"),
        indexation_amount=Decimal("99.999"),
        payment_amount=Decimal("0.01"),
        balance=balance_1,
        rate_source="Tasa pactada (Art. 1617 C.C.)",
    )

    debt_2 = PendingDebt(Decimal("120000.123"), Decimal("7.7"), Decimal("1000000.00"))
    balance_2 = RunningBalance(date=date(2026, 3, 1), debt=debt_2, event_type="PAYMENT")
    item_2 = LiquidationItem(
        date=date(2026, 3, 1),
        concept="Pago marzo",
        capital_base=Decimal("120000.123"),
        interest_rate=Decimal("0.5"),
        interest_amount=Decimal("7.7"),
        indexation_amount=Decimal("1000000.00"),
        payment_amount=Decimal("50000.99"),
        balance=balance_2,
        rate_source="IBC (Tasa de Usura)",
    )

    resultado = LiquidationResult(items=[item_1, item_2])

    json_str = serializar_resultado(resultado)
    reconstruido = deserializar_resultado(json_str)

    assert reconstruido == resultado
    assert reconstruido.items[0].indexation_amount == Decimal("99.999")
    assert reconstruido.items[0].payment_amount == Decimal("0.01")
    assert reconstruido.items[1].interest_amount == Decimal("7.7")
    assert reconstruido.items[1].indexation_amount == Decimal("1000000.00")


def test_deserializar_con_json_incompleto_lanza_key_error():
    json_incompleto = '{"items": [{"date": "2026-01-01"}]}'

    with pytest.raises(KeyError):
        deserializar_resultado(json_incompleto)


def test_serializar_usa_caracteres_no_ascii_legibles():
    debt = PendingDebt(Decimal("300000.00"), Decimal("3000.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Indexación IPC enero",
        capital_base=Decimal("300000.00"),
        interest_rate=Decimal("1.00"),
        interest_amount=Decimal("3000.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source="N/A",
    )
    resultado = LiquidationResult(items=[item])

    json_str = serializar_resultado(resultado)

    assert "Indexación" in json_str


def _item_de_prueba() -> LiquidationItem:
    debt = PendingDebt(Decimal("1000000.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="IMPUESTO_A_CARGO")
    return LiquidationItem(
        date=date(2026, 1, 1),
        concept="Impuesto de renta 2024",
        capital_base=Decimal("1000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source="N/A",
    )


def test_round_trip_sin_renta_liquida_preserva_none():
    resultado = LiquidationResult(items=[_item_de_prueba()])

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.renta_liquida is None
    assert len(reconstruido.items) == 1


def test_round_trip_con_renta_liquida_preserva_el_resultado_completo():
    renta_liquida = RentaLiquidaGravableResult(
        ingresos_netos=Decimal("100000000.00"),
        renta_bruta=Decimal("60000000.00"),
        renta_liquida=Decimal("40000000.00"),
        hubo_perdida_liquida=False,
        renta_liquida_gravable=Decimal("35000000.00"),
    )
    resultado = LiquidationResult(items=[_item_de_prueba()], renta_liquida=renta_liquida)

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.renta_liquida == renta_liquida


def test_deserializar_snapshot_antiguo_sin_clave_renta_liquida_no_lanza_keyerror():
    # Snapshot como los que ya existen en bastium.db, guardados ANTES de este sprint --
    # no tienen la clave "renta_liquida" en el JSON. deserializar_resultado debe seguir
    # funcionando (regresion equivalente a la ya conocida en Sprint 23 con otras claves).
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00", "rate_source": "N/A",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.renta_liquida is None


def test_deserializar_snapshot_antiguo_sin_clave_rate_source_no_lanza_keyerror():
    # Snapshot como los que ya existen en bastium.db, guardados ANTES de que
    # rate_source se agregara a LiquidationItem (commit posterior al que introdujo
    # el motor de auditoria del Sprint 9). AuditLog.resultado_json es append-only,
    # esas filas nunca se reescriben -- deserializar_resultado debe reconstruir con
    # rate_source="N/A" (mismo default que usa el motor sin rate_provider) en vez de
    # lanzar KeyError. Bug real de Sprint 23.
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.items[0].rate_source == "N/A"


def test_deserializar_snapshot_antiguo_sin_clave_saldo_a_favor_no_lanza_keyerror():
    # Mismo razonamiento que el test de rate_source: cualquier AuditLog guardado
    # ANTES de que saldo_a_favor se agregara a LiquidationItem (Sprint 23) no tiene
    # esa clave en su JSON. deserializar_resultado debe reconstruir con
    # saldo_a_favor=Decimal("0.00") (mismo default del dataclass) en vez de lanzar
    # KeyError.
    import json
    snapshot_antiguo = json.dumps({"items": [
        {
            "date": "2026-01-01", "concept": "Abono a capital", "capital_base": "1000000.00",
            "interest_rate": "0.00", "interest_amount": "0.00", "indexation_amount": "0.00",
            "payment_amount": "0.00", "rate_source": "N/A",
            "balance": {
                "date": "2026-01-01",
                "debt": {"principal": "1000000.00", "interest": "0.00", "indexation": "0.00"},
                "event_type": "IMPUESTO_A_CARGO",
            },
        }
    ]})

    reconstruido = deserializar_resultado(snapshot_antiguo)

    assert reconstruido.items[0].saldo_a_favor == Decimal("0.00")


def test_round_trip_preserva_saldo_a_favor_cuando_esta_presente():
    # Round-trip normal (snapshot nuevo, ya con la clave) -- el valor de saldo_a_favor
    # de un sobrepago real debe sobrevivir intacto, no resetearse a 0.00.
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 10), debt=debt, event_type="PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 10),
        concept="Pago con excedente",
        capital_base=Decimal("0.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=balance,
        saldo_a_favor=Decimal("3000000.00"),
    )
    resultado = LiquidationResult(items=[item])

    reconstruido = deserializar_resultado(serializar_resultado(resultado))

    assert reconstruido.items[0].saldo_a_favor == Decimal("3000000.00")
