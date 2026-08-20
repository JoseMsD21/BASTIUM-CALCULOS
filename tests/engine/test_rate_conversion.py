from decimal import Decimal

from app.engine.interest.rate_conversion import EffectiveRateConverter


def test_seis_por_ciento_anual_produce_la_tasa_diaria_civil_conocida():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("6"))
    assert rate.decimal() == Decimal("0.000159653587")


def test_cero_por_ciento_anual_produce_tasa_diaria_cero():
    rate = EffectiveRateConverter.annual_to_daily(Decimal("0"))
    assert rate.decimal() == Decimal("0.000000000000")


def test_seis_por_ciento_anual_produce_la_tasa_mensual_de_la_plantilla_i7():
    # i7.INTERESES-CIVILES-6-ANUAL.md (Sprint 83): tasa_mensual =
    # [(1+6%)^(1/12)-1]*12/12, mostrada como "0,49%" en la plantilla del
    # despacho (redondeada a 2 decimales de porcentaje).
    rate = EffectiveRateConverter.annual_to_monthly(Decimal("6"))
    assert rate.decimal() == Decimal("0.004867550565")
    assert round(rate.percent(), 2) == Decimal("0.49")


def test_cero_por_ciento_anual_produce_tasa_mensual_cero():
    rate = EffectiveRateConverter.annual_to_monthly(Decimal("0"))
    assert rate.decimal() == Decimal("0.000000000000")


def test_tasa_mensual_compuesta_doce_veces_reproduce_la_tasa_efectiva_anual_original():
    for annual_percent in (Decimal("6"), Decimal("20"), Decimal("28.79")):
        monthly_rate = EffectiveRateConverter.annual_to_monthly(annual_percent)
        annual_fraction = annual_percent / Decimal("100")
        reconstructed = (Decimal("1") + monthly_rate.decimal()) ** 12 - Decimal("1")
        assert abs(reconstructed - annual_fraction) < Decimal("0.0000001")
