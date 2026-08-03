from datetime import date, timedelta
from datetime import datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.indexation.historical_index import _TRAMOS_IBC_USURA, get_ibc_usura_for_date
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_ibc_usura_en_memoria(monkeypatch):
    # Tarea 13: MoratoryIndemnityCalculator.calcular (via get_ibc_usura_for_date)
    # ahora lee IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO de parametros_legales
    # en vez de la tabla en memoria _TRAMOS_IBC_USURA. Sin esta fixture, los tests
    # de este archivo dependerian silenciosamente del bastium.db real en disco
    # (gitignored, estado no garantizado en un checkout limpio o en CI) en vez de
    # una base aislada -- mismo criterio que las fixtures equivalentes de
    # tests/engine/test_historical_index.py y tests/services/test_area_strategy.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
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


def test_pagado_a_tiempo_no_genera_indemnizacion():
    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=date(2020, 1, 10),
        fecha_pago_o_corte=date(2020, 1, 5),  # antes de terminar el contrato
    )
    assert resultado.total == Decimal("0.00")
    assert resultado.dias_retardo == 0
    assert resultado.dias_fase1 == 0
    assert resultado.dias_fase2 == 0


def test_pago_exactamente_dia_720_solo_fase1():
    fecha_terminacion = date(2018, 1, 1)
    fecha_pago = fecha_terminacion + timedelta(days=720)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_retardo == 720
    assert resultado.dias_fase1 == 720
    assert resultado.monto_fase1 == Decimal("72000000.00")  # (3M/30) * 720
    assert resultado.dias_fase2 == 0
    assert resultado.monto_fase2 == Decimal("0.00")
    assert resultado.total == Decimal("72000000.00")


def test_pago_dia_721_entra_un_dia_en_fase2():
    fecha_terminacion = date(2018, 1, 1)
    fecha_pago = fecha_terminacion + timedelta(days=721)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_fase1 == 720
    assert resultado.monto_fase1 == Decimal("72000000.00")
    assert resultado.dias_fase2 == 1

    dia_calculo = fecha_terminacion + timedelta(days=721)
    _, usura = get_ibc_usura_for_date(dia_calculo)
    tasa_diaria = EffectiveRateConverter.annual_to_daily(usura)
    esperado_fase2 = DailyInterest.calculate(Decimal("5000000.00"), tasa_diaria, 1)

    assert resultado.monto_fase2 == esperado_fase2
    assert resultado.total == resultado.monto_fase1 + esperado_fase2


def test_fase2_cruza_tramos_de_usura_distintos():
    # fecha_terminacion elegida para que el dia 721 caiga en 2018-01-31 y el
    # dia 722 en 2018-02-01 -- dos tramos de usura distintos en
    # historical_index (verificado: 31.04% vs 31.52% EA).
    fecha_terminacion = date(2016, 2, 10)
    fecha_pago = fecha_terminacion + timedelta(days=722)

    resultado = MoratoryIndemnityCalculator.calcular(
        salario_mensual=Decimal("3000000.00"),
        monto_adeudado=Decimal("5000000.00"),
        fecha_terminacion=fecha_terminacion,
        fecha_pago_o_corte=fecha_pago,
    )

    assert resultado.dias_fase2 == 2

    dia1 = fecha_terminacion + timedelta(days=721)
    dia2 = fecha_terminacion + timedelta(days=722)
    assert dia1 == date(2018, 1, 31)
    assert dia2 == date(2018, 2, 1)

    _, usura_dia1 = get_ibc_usura_for_date(dia1)
    _, usura_dia2 = get_ibc_usura_for_date(dia2)
    assert usura_dia1 != usura_dia2  # confirma que el tramo realmente cambia

    esperado_dia1 = DailyInterest.calculate(
        Decimal("5000000.00"), EffectiveRateConverter.annual_to_daily(usura_dia1), 1
    )
    esperado_dia2 = DailyInterest.calculate(
        Decimal("5000000.00"), EffectiveRateConverter.annual_to_daily(usura_dia2), 1
    )
    assert resultado.monto_fase2 == esperado_dia1 + esperado_dia2
    assert resultado.total == resultado.monto_fase1 + resultado.monto_fase2
