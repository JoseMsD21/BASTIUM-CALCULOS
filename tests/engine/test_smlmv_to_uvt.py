from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("828116.00"), vigente_desde=date(2019, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_hecho_pre_2020_usa_smlmv_del_anio_del_hecho():
    # SMLMV 2019 = 828116.00 (ver historical_index.py, verificado contra el PDF pag. 55-57).
    resultado = resolver_base_sancion(date(2019, 6, 1), Decimal("2"))
    assert resultado == Decimal("1656232.00")


def test_hecho_dia_anterior_al_corte_2020_usa_smlmv_2019():
    resultado = resolver_base_sancion(date(2019, 12, 31), Decimal("1"))
    assert resultado == Decimal("828116.00")


def test_hecho_exactamente_2020_01_01_ya_requiere_uvt_y_lanza_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2020, 1, 1), Decimal("1"))


def test_hecho_posterior_a_2020_lanza_uvt_no_disponible_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2021, 1, 1), Decimal("1"))
