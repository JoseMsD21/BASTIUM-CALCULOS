from datetime import date
from decimal import Decimal

import pytest

from app.engine.currency.trm_provider import ManualTRMProvider, TRMProvider


def test_manual_trm_provider_retorna_el_valor_sembrado():
    provider = ManualTRMProvider(Decimal("4150.2500"))
    assert provider.get_trm(date(2025, 1, 1)) == Decimal("4150.2500")


def test_manual_trm_provider_retorna_el_mismo_valor_para_cualquier_fecha():
    provider = ManualTRMProvider(Decimal("4000.0000"))
    assert provider.get_trm(date(2020, 1, 1)) == Decimal("4000.0000")
    assert provider.get_trm(date(2026, 12, 31)) == Decimal("4000.0000")


def test_trm_provider_es_abstracto_no_se_puede_instanciar():
    with pytest.raises(TypeError):
        TRMProvider()
