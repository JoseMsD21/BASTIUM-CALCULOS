from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import ParametroNoDisponibleError
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


def _insertar(clave, valor, vigente_desde, vigente_hasta=None):
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave=clave, valor=Decimal(valor), vigente_desde=vigente_desde, vigente_hasta=vigente_hasta,
        usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_get_parametro_modo_abierto_toma_la_fila_mas_reciente_antes_de_la_fecha():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    _insertar("USURA_MULTIPLICADOR", "2.0", date(2030, 1, 1))

    assert get_parametro("USURA_MULTIPLICADOR", date(2026, 7, 20)) == Decimal("1.5")
    assert get_parametro("USURA_MULTIPLICADOR", date(2031, 1, 1)) == Decimal("2.0")


def test_get_parametro_modo_abierto_extrapola_hacia_adelante_sin_tope():
    from app.services.parametro_service import get_parametro

    _insertar("CUOTA_LITIS_INDIVIDUAL_PCT", "30", date(2007, 1, 1))
    assert get_parametro("CUOTA_LITIS_INDIVIDUAL_PCT", date(2099, 1, 1)) == Decimal("30")


def test_get_parametro_sin_ninguna_fila_anterior_a_la_fecha_lanza_error():
    from app.services.parametro_service import get_parametro

    _insertar("USURA_MULTIPLICADOR", "1.5", date(1997, 7, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("USURA_MULTIPLICADOR", date(1990, 1, 1))


def test_get_parametro_clave_desconocida_lanza_value_error():
    from app.services.parametro_service import get_parametro

    with pytest.raises(ValueError):
        get_parametro("NO_EXISTE", date(2026, 1, 1))


def test_get_parametro_modo_anual_exacto_requiere_el_mismo_anio():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    _insertar("SMLMV", "1423500.00", date(2025, 1, 1))

    assert get_parametro("SMLMV", date(2026, 7, 20)) == Decimal("1750905.00")
    assert get_parametro("SMLMV", date(2025, 12, 31)) == Decimal("1423500.00")


def test_get_parametro_modo_anual_exacto_no_extrapola():
    from app.services.parametro_service import get_parametro

    _insertar("SMLMV", "1750905.00", date(2026, 1, 1))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("SMLMV", date(2027, 1, 1))


def test_get_parametro_modo_tramo_cerrado_encuentra_el_tramo_correcto():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    _insertar("IBC_CONSUMO_ORDINARIO", "16.82", date(2026, 2, 1), vigente_hasta=date(2026, 2, 28))

    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 1, 15)) == Decimal("16.24")
    assert get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 15)) == Decimal("16.82")


def test_get_parametro_modo_tramo_cerrado_no_extrapola_mas_alla_del_ultimo_tramo():
    from app.services.parametro_service import get_parametro

    _insertar("IBC_CONSUMO_ORDINARIO", "16.24", date(2026, 1, 1), vigente_hasta=date(2026, 1, 31))
    with pytest.raises(ParametroNoDisponibleError):
        get_parametro("IBC_CONSUMO_ORDINARIO", date(2026, 2, 1))
