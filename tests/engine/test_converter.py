from datetime import date
from decimal import Decimal

import pytest

from app.engine.currency.converter import convertir_a_pesos
from app.engine.currency.trm_provider import ManualTRMProvider


def test_moneda_cop_retorna_el_valor_sin_conversion_ni_provider():
    resultado = convertir_a_pesos(
        valor=Decimal("1000000.00"), moneda="COP", provider=None, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_moneda_none_se_trata_igual_que_cop():
    resultado = convertir_a_pesos(
        valor=Decimal("1000000.00"), moneda=None, provider=None, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_moneda_usd_convierte_multiplicando_por_la_trm():
    provider = ManualTRMProvider(Decimal("4150.2500"))
    resultado = convertir_a_pesos(
        valor=Decimal("10000.00"), moneda="USD", provider=provider, fecha_referencia=date(2025, 1, 1)
    )
    assert resultado == Decimal("41502500.00")


def test_moneda_usd_sin_provider_lanza_value_error():
    with pytest.raises(ValueError, match="requiere una TRM aplicable"):
        convertir_a_pesos(
            valor=Decimal("10000.00"), moneda="USD", provider=None, fecha_referencia=date(2025, 1, 1)
        )
