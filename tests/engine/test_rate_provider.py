import pytest
from datetime import date
from decimal import Decimal
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider

def test_memory_rate_provider_resolves_historical_rates():
    provider = MemoryRateProvider()
    # Tasa del 1% para enero, 2% para febrero
    provider.add_rate_period(date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0")))
    provider.add_rate_period(date(2026, 2, 1), date(2026, 2, 28), Rate.from_percent(Decimal("2.0")))
    
    # Consultas exactas
    tasa_enero = provider.get_rate(date(2026, 1, 15))
    tasa_febrero = provider.get_rate(date(2026, 2, 10))
    
    assert tasa_enero.percent() == Decimal("1.00")
    assert tasa_febrero.percent() == Decimal("2.00")

def test_rate_provider_raises_error_if_date_not_found():
    provider = MemoryRateProvider()
    provider.add_rate_period(date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0")))
    
    with pytest.raises(ValueError, match="No se encontró una tasa configurada para la fecha"):
        provider.get_rate(date(2025, 12, 31))