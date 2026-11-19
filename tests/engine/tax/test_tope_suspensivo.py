"""Sprint 84 (seguimiento): tope suspensivo del interes moratorio tributario
por demanda ante lo contencioso administrativo. Respuesta del despacho
(16/11/2026): fecha_tope_24m = admision + 24 meses; fecha_reanudacion_interes =
notificacion de la sentencia + 11 dias."""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.tax.tope_suspensivo import (
    FUENTE_TOPE_SUSPENSIVO,
    RateProviderConTopeSuspensivo,
    calcular_fecha_reanudacion_interes,
    calcular_fecha_tope_24m,
)


def test_fecha_tope_24m_suma_24_meses_calendario():
    assert calcular_fecha_tope_24m(date(2022, 3, 5)) == date(2024, 3, 5)


def test_fecha_tope_24m_29_de_febrero_se_topa_al_ultimo_dia_del_mes():
    # 2020-02-29 + 24 meses -> febrero de 2022 no tiene dia 29 -> 2022-02-28.
    assert calcular_fecha_tope_24m(date(2020, 2, 29)) == date(2022, 2, 28)


def test_fecha_reanudacion_suma_11_dias_calendario():
    assert calcular_fecha_reanudacion_interes(date(2024, 3, 10)) == date(2024, 3, 21)
    # Cruza de mes: 2024-02-25 + 11 dias = 2024-03-07 (2024 bisiesto, feb 29 dias).
    assert calcular_fecha_reanudacion_interes(date(2024, 2, 25)) == date(2024, 3, 7)


def _provider_plano() -> MemoryRateProvider:
    provider = MemoryRateProvider()
    provider.add_rate_period(
        start=date(2024, 1, 1),
        end=date(2024, 12, 31),
        rate=Rate(Decimal("0.0001")),
        source="Tasa base",
    )
    return provider


def test_suspende_estrictamente_entre_el_tope_y_la_reanudacion():
    # tope 2024-03-05, reanudacion 2024-03-21: el 5 y el 21 causan interes, del 6
    # al 20 (15 dias) no.
    provider = RateProviderConTopeSuspensivo(
        _provider_plano(),
        fecha_tope_24m=date(2024, 3, 5),
        fecha_reanudacion_interes=date(2024, 3, 21),
    )
    assert provider.get_rate(date(2024, 3, 5)).value == Decimal("0.0001")
    assert provider.get_rate(date(2024, 3, 6)).value == Decimal("0")
    assert provider.get_rate(date(2024, 3, 20)).value == Decimal("0")
    assert provider.get_rate(date(2024, 3, 21)).value == Decimal("0.0001")
    assert provider.get_rate_source(date(2024, 3, 6)) == FUENTE_TOPE_SUSPENSIVO
    assert provider.get_rate_source(date(2024, 3, 21)) == "Tasa base"
    dias_suspendidos = sum(
        1
        for dia in range(1, 32)
        if provider.get_rate(date(2024, 3, dia)).value == Decimal("0")
    )
    assert dias_suspendidos == 15


def test_sin_reanudacion_conocida_suspende_desde_el_tope_en_adelante():
    provider = RateProviderConTopeSuspensivo(
        _provider_plano(), fecha_tope_24m=date(2024, 3, 5), fecha_reanudacion_interes=None
    )
    assert provider.get_rate(date(2024, 3, 5)).value == Decimal("0.0001")
    assert provider.get_rate(date(2024, 12, 31)).value == Decimal("0")


def test_reanudacion_anterior_o_igual_al_tope_no_suspende_nada():
    # Sentencia notificada antes de cumplirse los 24 meses: el tope nunca se alcanza.
    provider = RateProviderConTopeSuspensivo(
        _provider_plano(),
        fecha_tope_24m=date(2024, 3, 5),
        fecha_reanudacion_interes=date(2024, 3, 1),
    )
    assert all(
        provider.get_rate(date(2024, 3, dia)).value == Decimal("0.0001") for dia in range(1, 32)
    )


def test_dias_fuera_del_provider_base_siguen_lanzando_value_error():
    provider = RateProviderConTopeSuspensivo(
        _provider_plano(),
        fecha_tope_24m=date(2024, 3, 5),
        fecha_reanudacion_interes=date(2024, 3, 21),
    )
    with pytest.raises(ValueError):
        provider.get_rate(date(2025, 1, 1))
