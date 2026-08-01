from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.interest.usury_validator import calcular_tope_usura
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="USURA_MULTIPLICADOR", valor=Decimal("1.5"), vigente_desde=date(1997, 7, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_calcula_el_tope_como_multiplicador_por_ibc():
    assert calcular_tope_usura(Decimal("20.00"), date(2026, 1, 1)) == Decimal("30.000")


def test_no_lanza_nada_ni_para_tasas_por_encima_del_tope():
    # calcular_tope_usura solo calcula el tope -- no rechaza ni recorta ninguna tasa.
    # Sancionar el exceso (Ley 45/1990 art. 72) es responsabilidad de quien la llama,
    # ver ComercialStrategy._calcular_sancion_usura (Preguntas-Para-Abogado.md Sprint 2).
    calcular_tope_usura(Decimal("20.00"), date(2026, 1, 1))
