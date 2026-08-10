from datetime import date
from decimal import Decimal

import pytest

from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider, RateProvider


def test_memory_rate_provider_resolves_historical_rates():
    provider = MemoryRateProvider()
    # Tasa del 1% para enero, 2% para febrero
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )
    provider.add_rate_period(
        date(2026, 2, 1), date(2026, 2, 28), Rate.from_percent(Decimal("2.0"))
    )

    # Consultas exactas
    tasa_enero = provider.get_rate(date(2026, 1, 15))
    tasa_febrero = provider.get_rate(date(2026, 2, 10))

    assert tasa_enero.percent() == Decimal("1.00")
    assert tasa_febrero.percent() == Decimal("2.00")


def test_rate_provider_raises_error_if_date_not_found():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )

    with pytest.raises(ValueError, match="No se encontró una tasa configurada para la fecha"):
        provider.get_rate(date(2025, 12, 31))


def test_memory_rate_provider_resolves_rate_source():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1),
        date(2026, 1, 31),
        Rate.from_percent(Decimal("1.0")),
        source="Tasa pactada",
    )
    assert provider.get_rate_source(date(2026, 1, 15)) == "Tasa pactada"


def test_memory_rate_provider_rate_source_por_defecto_es_na():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )
    assert provider.get_rate_source(date(2026, 1, 15)) == "N/A"


def test_memory_rate_provider_get_rate_source_lanza_error_si_no_hay_tramo():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )
    with pytest.raises(ValueError, match="No se encontró una tasa configurada para la fecha"):
        provider.get_rate_source(date(2025, 12, 31))


def test_rate_provider_base_get_rate_source_por_defecto_es_na():
    class _ProviderDeControl(RateProvider):
        def get_rate(self, target_date):
            return Rate.from_percent(Decimal("1.0"))

    provider = _ProviderDeControl()
    assert provider.get_rate_source(date(2026, 1, 1)) == "N/A"


def test_memory_rate_provider_con_hueco_entre_periodos_lanza_error_en_el_hueco():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )
    provider.add_rate_period(
        date(2026, 3, 1), date(2026, 3, 31), Rate.from_percent(Decimal("3.0"))
    )

    with pytest.raises(ValueError, match="No se encontró una tasa configurada para la fecha"):
        provider.get_rate(date(2026, 2, 15))


def test_memory_rate_provider_resuelve_correctamente_en_las_fronteras_exactas():
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2026, 1, 1), date(2026, 1, 31), Rate.from_percent(Decimal("1.0"))
    )
    provider.add_rate_period(
        date(2026, 2, 1), date(2026, 2, 28), Rate.from_percent(Decimal("2.0"))
    )

    assert provider.get_rate(date(2026, 1, 1)).percent() == Decimal("1.00")
    assert provider.get_rate(date(2026, 1, 31)).percent() == Decimal("1.00")
    assert provider.get_rate(date(2026, 2, 1)).percent() == Decimal("2.00")


def test_memory_rate_provider_muchos_periodos_agregados_en_orden_no_ordenado():
    provider = MemoryRateProvider()
    # Se agregan fuera de orden a propósito -- add_rate_period debe reordenar.
    for anio in range(2020, 2010, -1):
        provider.add_rate_period(
            date(anio, 1, 1), date(anio, 12, 31), Rate.from_percent(Decimal(anio - 2000))
        )

    assert provider.get_rate(date(2015, 6, 1)).percent() == Decimal("15.00")
    assert provider.get_rate(date(2020, 12, 31)).percent() == Decimal("20.00")
