from datetime import date
from decimal import Decimal
from app.engine.temporal.schedulers.base import Event
from app.engine.liquidation.engine import LiquidationCore
from app.engine.financial.rate import Rate

def test_engine_processes_chronological_events():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
        Event(date=date(2026, 1, 15), payload={"amount": Decimal("50.00")}, event_type="INTEREST"),
        Event(date=date(2026, 1, 31), payload={"amount": Decimal("500.00")}, event_type="PAYMENT"),
    ]
    
    # 1. Instanciamos el motor con una tasa de control (0%) para probar puramente la imputación
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)
    
    # 2. Definimos la fecha de corte exacta del último evento
    cutoff = date(2026, 1, 31)
    
    # 3. Procesamos inyectando el límite temporal
    result = engine.process(events, cutoff_date=cutoff)
    
    # Validaciones estables
    assert len(result.items) == 3
    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("550.00")
    assert final_debt.interest == Decimal("0.00")
    assert result.total_payments_applied() == Decimal("500.00")


from app.engine.interest.provider import MemoryRateProvider


def test_engine_popula_rate_source_desde_el_rate_provider():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
    ]
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2025, 12, 31), date(2026, 1, 31), Rate.from_percent(Decimal("1.0")), source="Tasa de prueba"
    )
    engine = LiquidationCore(rate_provider=provider)

    result = engine.process(events, cutoff_date=date(2026, 1, 1))

    assert all(item.rate_source == "Tasa de prueba" for item in result.items)


def test_engine_rate_source_es_na_sin_rate_provider():
    events = [
        Event(date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"),
    ]
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("0.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 1))

    assert all(item.rate_source == "N/A" for item in result.items)