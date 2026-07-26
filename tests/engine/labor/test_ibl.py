from datetime import date, datetime as _dt, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _ipc_en_memoria(monkeypatch):
    # calcular_ibl usa get_ipc_interpolado_for_date, que lee IPC_INDICE_ACUMULADO
    # via parametro_service en cada llamada -- misma fixture aislada de disco
    # que tests/engine/labor/test_seguridad_social.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    indices = {
        2017: Decimal("100"), 2018: Decimal("105"), 2019: Decimal("110"),
        2020: Decimal("115"), 2021: Decimal("120"), 2022: Decimal("125"),
        2023: Decimal("130"), 2024: Decimal("135"), 2025: Decimal("140"),
        2026: Decimal("145"),
    }
    for anio, valor in indices.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_calcular_ibl_historial_10_anios_con_ipc_variable():
    from app.engine.labor.ibl import calcular_ibl

    historial = [(date(anio, 12, 31), Decimal("1000000.00")) for anio in range(2017, 2027)]

    resultado = calcular_ibl(historial, fecha_calculo=date(2026, 12, 31))

    assert resultado == Decimal("1200351.01")


def test_calcular_ibl_historial_vacio_lanza_error():
    from app.engine.labor.ibl import calcular_ibl

    with pytest.raises(ValueError):
        calcular_ibl([], fecha_calculo=date(2026, 12, 31))
