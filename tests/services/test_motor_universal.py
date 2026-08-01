from datetime import date
from decimal import Decimal

from app.engine.temporal.schedulers.base import Event
from app.services.motor_universal import UniversalLiquidationService


def test_liquidar_reenvia_usar_suma_unica_al_motor_core():
    eventos = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]

    resultado_legado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"), usar_suma_unica=False,
    )
    resultado_suma_unica = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"), usar_suma_unica=True,
    )

    assert resultado_legado.final_balance().interest == Decimal("100.00")
    assert resultado_suma_unica.final_balance().interest == Decimal("150.00")


def test_liquidar_usar_suma_unica_default_es_false():
    eventos = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"),
    ]

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos, pagos=[], fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"),
    )

    assert resultado.final_balance().interest == Decimal("100.00")
