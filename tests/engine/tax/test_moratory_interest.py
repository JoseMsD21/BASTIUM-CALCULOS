from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest

import database.session as session_module
from app.engine.indexation.historical_index import _TRAMOS_IBC_USURA
from app.engine.tax.moratory_interest import (
    FUENTE_MORATORIO_TRIBUTARIO,
    calcular_interes_moratorio_tributario,
    construir_rate_provider_moratorio_tributario,
)
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _parametro_et635_en_memoria():
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="ET635_PUNTOS_DESCUENTO", valor=Decimal("2"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    # IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO (Tarea 13):
    # construir_rate_provider_moratorio_tributario llama a
    # get_tramos_ibc_usura_between, que ahora reconstruye tramos desde
    # parametros_legales en vez de leer _TRAMOS_IBC_USURA en memoria. Se
    # siembran aqui desde la misma tabla congelada que consume
    # scripts/migrate_parametros_legales.py (mismo criterio que la fixture
    # equivalente de tests/services/test_area_strategy.py).
    for tramo in _TRAMOS_IBC_USURA:
        session.add(ParametroLegal(
            clave="IBC_CONSUMO_ORDINARIO", valor=tramo.ibc_anual, vigente_desde=tramo.inicio,
            vigente_hasta=tramo.fin, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
        session.add(ParametroLegal(
            clave="USURA_CONSUMO_ORDINARIO", valor=tramo.usura_anual, vigente_desde=tramo.inicio,
            vigente_hasta=tramo.fin, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


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


def test_capital_cero_o_negativo_retorna_cero_sin_consultar_tramos():
    assert calcular_interes_moratorio_tributario(
        capital=Decimal("0.00"), fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    ) == Decimal("0.00")


def test_fecha_corte_igual_a_exigibilidad_da_cero_dias_de_mora():
    assert calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 6, 15), fecha_corte=date(2026, 6, 15)
    ) == Decimal("0.00")


def test_un_dia_de_mora_coincide_con_el_ejemplo_del_pdf_usura_28_79_ea():
    # PDF pag. 39: usura 28.79% EA -> interes moratorio tributario 26.79% EA
    total = calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 6, 1), fecha_corte=date(2026, 6, 2)
    )
    assert total == Decimal("650.52")


def test_mora_que_cruza_dos_meses_suma_interes_de_cada_tramo():
    total = calcular_interes_moratorio_tributario(
        capital=Decimal("1000000.00"), fecha_exigibilidad=date(2026, 4, 29), fecha_corte=date(2026, 5, 2)
    )
    # abril 30 (606.27) + mayo 1 (637.08) + mayo 2 (637.08)
    assert total == Decimal("1880.43")
