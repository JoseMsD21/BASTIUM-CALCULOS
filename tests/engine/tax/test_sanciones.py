from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.indexation.historical_index import _UVT_POR_ANIO
from app.engine.tax.sanciones import (
    aplicar_piso_sancion_minima,
    calcular_sancion_error_aritmetico,
    calcular_sancion_extemporaneidad,
    calcular_sancion_inexactitud,
)
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_sanciones_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="EXTEMPORANEIDAD_PCT_MENSUAL", valor=Decimal("5"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="INEXACTITUD_PCT", valor=Decimal("160"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="INEXACTITUD_AGRAVADA_PCT", valor=Decimal("200"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="ERROR_ARITMETICO_PCT", valor=Decimal("30"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="UVT", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_piso_sancion_minima_no_afecta_montos_por_encima_de_10_uvt():
    # UVT 2024 = 47065.00 (ver historical_index.py) -> piso = 470650.00
    assert aplicar_piso_sancion_minima(Decimal("1000000.00"), date(2024, 6, 1)) == Decimal("1000000.00")


def test_piso_sancion_minima_eleva_montos_por_debajo_de_10_uvt():
    assert aplicar_piso_sancion_minima(Decimal("100000.00"), date(2024, 6, 1)) == Decimal("470650.00")


def test_extemporaneidad_5_pct_mensual_por_cada_mes():
    # Impuesto a cargo 10,000,000, 2 meses de atraso: 5% x 2 = 10% = 1,000,000 (por encima del piso).
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("10000000.00"), meses_o_fraccion=2, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("1000000.00")


def test_extemporaneidad_topada_en_100_pct_del_impuesto_a_cargo():
    # 5% x 30 meses = 150%, debe quedar topado en el 100% del impuesto a cargo.
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("10000000.00"), meses_o_fraccion=30, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("10000000.00")


def test_extemporaneidad_por_debajo_del_piso_queda_en_10_uvt():
    resultado = calcular_sancion_extemporaneidad(
        impuesto_a_cargo=Decimal("1000000.00"), meses_o_fraccion=1, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("470650.00")


def test_inexactitud_160_pct_de_la_diferencia_sin_agravante():
    resultado = calcular_sancion_inexactitud(
        diferencia=Decimal("5000000.00"), agravada=False, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("8000000.00")


def test_inexactitud_200_pct_de_la_diferencia_agravada():
    resultado = calcular_sancion_inexactitud(
        diferencia=Decimal("5000000.00"), agravada=True, fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("10000000.00")


def test_error_aritmetico_30_pct_de_la_diferencia():
    resultado = calcular_sancion_error_aritmetico(
        diferencia=Decimal("5000000.00"), fecha_referencia=date(2024, 6, 1)
    )
    assert resultado == Decimal("1500000.00")
