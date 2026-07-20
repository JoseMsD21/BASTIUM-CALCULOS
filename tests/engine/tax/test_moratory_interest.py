from datetime import date
from decimal import Decimal

import pytest

from app.engine.tax.moratory_interest import (
    FUENTE_MORATORIO_TRIBUTARIO,
    construir_rate_provider_moratorio_tributario,
)


def test_sin_mora_si_fecha_corte_no_supera_la_exigibilidad():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 6, 15), fecha_corte=date(2026, 6, 15)
    )
    with pytest.raises(ValueError):
        provider.get_rate(date(2026, 6, 16))


def test_un_solo_tramo_agrega_un_periodo_con_tasa_usura_menos_dos_puntos():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    )
    rate = provider.get_rate(date(2026, 6, 2))
    # usura junio 2026 = 28.79% EA -> tributario = 26.79% EA (mismo ejemplo del PDF pag. 39)
    assert rate.decimal() == Decimal("0.000650518313")
    assert provider.get_rate_source(date(2026, 6, 2)) == FUENTE_MORATORIO_TRIBUTARIO


def test_rango_que_cruza_dos_meses_agrega_dos_periodos_con_tasas_distintas():
    provider = construir_rate_provider_moratorio_tributario(
        fecha_exigibilidad=date(2026, 4, 29), fecha_corte=date(2026, 5, 2)
    )
    # abril 2026: usura 26.76% -> tributario 24.76%
    assert provider.get_rate(date(2026, 4, 30)).decimal() == Decimal("0.000606270573")
    # mayo 2026: usura 28.17% -> tributario 26.17%
    assert provider.get_rate(date(2026, 5, 1)).decimal() == Decimal("0.000637079611")
    assert provider.get_rate(date(2026, 5, 2)).decimal() == Decimal("0.000637079611")


def test_rango_fuera_de_datos_disponibles_propaga_value_error():
    with pytest.raises(ValueError):
        construir_rate_provider_moratorio_tributario(
            fecha_exigibilidad=date(2026, 8, 1), fecha_corte=date(2026, 8, 5)
        )
