from decimal import Decimal

from app.engine.interest.rate_conversion import EffectiveRateConverter


def test_seis_por_ciento_anual_produce_la_tasa_diaria_civil_conocida():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("6"))
    assert rate.decimal() == Decimal("0.000159653587")


def test_cero_por_ciento_anual_produce_tasa_diaria_cero():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("0"))
    assert rate.decimal() == Decimal("0.000000000000")
