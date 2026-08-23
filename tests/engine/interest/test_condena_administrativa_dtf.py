"""Sprint 82 (respuesta del despacho, 22/08/2026): interes de mora en
condenas o conciliaciones contra el Estado (Art. 195 num. 4 Ley 1437/2011,
CPACA) -- regimen dual DTF (primeros 304 dias) / 1,5x IBC (de ahi en
adelante). Funcion aislada, sin conectar a ninguna AreaStrategy -- ver
docstring de app/engine/interest/condena_administrativa_dtf.py."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.engine.indexation.historical_dtf import get_dtf_for_date
from app.engine.indexation.historical_index import get_ibc_usura_for_date
from app.engine.interest.condena_administrativa_dtf import (
    LIMITE_GRACIA_DIAS,
    calcular_interes_dtf_condena_administrativa,
)
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria():
    from scripts.migrate_parametros_legales import migrar

    migrar()


def test_un_dia_dentro_del_tramo_dtf():
    capital = Decimal("10000000.00")
    fecha_ejecutoria = date(1985, 12, 20)
    fecha_corte = date(1985, 12, 21)  # 1 dia transcurrido

    resultado = calcular_interes_dtf_condena_administrativa(
        capital, fecha_ejecutoria, fecha_corte
    )

    dtf_anual = get_dtf_for_date(fecha_ejecutoria)
    tasa_diaria = EffectiveRateConverter.annual_to_daily(dtf_anual)
    esperado = DailyInterest.calculate(capital, tasa_diaria, days=1)
    assert resultado == esperado
    assert resultado == Decimal("8552.51")  # valor de referencia (DTF=36.62% EA -> diaria)


def test_fecha_corte_igual_a_ejecutoria_no_causa_interes():
    resultado = calcular_interes_dtf_condena_administrativa(
        Decimal("10000000.00"), date(2020, 1, 1), date(2020, 1, 1)
    )
    assert resultado == Decimal("0.00")


def test_periodo_completo_dentro_del_tramo_dtf_coincide_con_la_composicion():
    capital = Decimal("5000000.00")
    fecha_ejecutoria = date(2020, 1, 1)
    fecha_corte = fecha_ejecutoria + timedelta(days=30)  # bien dentro de los 304 dias

    resultado = calcular_interes_dtf_condena_administrativa(
        capital, fecha_ejecutoria, fecha_corte
    )

    esperado = Decimal("0.00")
    dia = fecha_ejecutoria
    while dia < fecha_corte:
        tasa_diaria = EffectiveRateConverter.annual_to_daily(get_dtf_for_date(dia))
        esperado += DailyInterest.calculate(capital, tasa_diaria, days=1)
        dia += timedelta(days=1)

    assert resultado == esperado


def test_periodo_cruza_al_tramo_comercial_1_5x_ibc():
    capital = Decimal("5000000.00")
    fecha_ejecutoria = date(2020, 1, 1)
    # 306 dias transcurridos: 1-304 tramo DTF, 305-306 tramo comercial.
    fecha_corte = fecha_ejecutoria + timedelta(days=306)

    resultado = calcular_interes_dtf_condena_administrativa(
        capital, fecha_ejecutoria, fecha_corte
    )

    esperado = Decimal("0.00")
    dia = fecha_ejecutoria
    dias_transcurridos = 0
    while dia < fecha_corte:
        dias_transcurridos += 1
        if dias_transcurridos <= LIMITE_GRACIA_DIAS:
            tasa_anual = get_dtf_for_date(dia)
        else:
            ibc_anual, _usura = get_ibc_usura_for_date(dia)
            tasa_anual = Decimal("1.5") * ibc_anual
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tasa_anual)
        esperado += DailyInterest.calculate(capital, tasa_diaria, days=1)
        dia += timedelta(days=1)

    assert resultado == esperado
    # El tramo comercial (1.5x IBC) debe dar mas interes por dia que si todo el
    # periodo hubiera seguido en DTF -- confirma que el cambio de tramo si aplica.
    solo_dtf = calcular_interes_dtf_condena_administrativa(
        capital, fecha_ejecutoria, fecha_ejecutoria + timedelta(days=304)
    )
    interes_ultimos_2_dias = resultado - solo_dtf
    ibc_anual, _usura = get_ibc_usura_for_date(fecha_ejecutoria + timedelta(days=305))
    tasa_dtf_esos_dias = EffectiveRateConverter.annual_to_daily(
        get_dtf_for_date(fecha_ejecutoria + timedelta(days=305))
    )
    tasa_comercial_esos_dias = EffectiveRateConverter.annual_to_daily(
        Decimal("1.5") * ibc_anual
    )
    assert tasa_comercial_esos_dias.decimal() != tasa_dtf_esos_dias.decimal()
    assert interes_ultimos_2_dias > Decimal("0.00")


def test_fecha_corte_anterior_a_ejecutoria_lanza_error():
    with pytest.raises(ValueError):
        calcular_interes_dtf_condena_administrativa(
            Decimal("1000000.00"), date(2020, 6, 1), date(2020, 1, 1)
        )


def test_limite_gracia_es_304_dias():
    assert LIMITE_GRACIA_DIAS == 304
