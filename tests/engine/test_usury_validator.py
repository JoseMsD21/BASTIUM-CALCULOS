from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import TasaUsurariaError
from app.engine.interest.usury_validator import validar_tasa_usura
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


def test_tasa_por_debajo_del_tope_no_lanza_error():
    validar_tasa_usura(Decimal("20.00"), Decimal("20.00"), "remuneratoria", date(2026, 1, 1))


def test_tasa_exactamente_en_el_tope_no_lanza_error():
    validar_tasa_usura(Decimal("30.00"), Decimal("20.00"), "moratoria", date(2026, 1, 1))


def test_tasa_por_encima_del_tope_lanza_tasa_usuraria_error():
    with pytest.raises(TasaUsurariaError):
        validar_tasa_usura(Decimal("30.01"), Decimal("20.00"), "moratoria", date(2026, 1, 1))


def test_mensaje_de_error_nombra_la_etiqueta_y_el_tope():
    with pytest.raises(TasaUsurariaError, match="moratoria"):
        validar_tasa_usura(Decimal("35.00"), Decimal("20.00"), "moratoria", date(2026, 1, 1))
