from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as database_module
import database.session as session_module
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return engine


def test_migrar_siembra_las_17_claves_del_catalogo():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    claves = {fila.clave for fila in session.query(ParametroLegal).all()}
    session.close()
    assert claves == {
        "USURA_MULTIPLICADOR", "CUOTA_LITIS_INDIVIDUAL_PCT", "HONORARIOS_TOTAL_PCT",
        "ET635_PUNTOS_DESCUENTO", "CIVIL_ANNUAL_RATE",
        "PRESCRIPCION_EJECUTIVA_MESES", "PRESCRIPCION_ORDINARIA_MESES",
        "PRESCRIPCION_HONORARIOS_MESES", "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
        "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
        "CADUCIDAD_IMPUGNACION_INEFICACIA_SOCIETARIA_MESES",
        "SMLMV", "IPC_INDICE_ACUMULADO", "IBC_CONSUMO_ORDINARIO", "USURA_CONSUMO_ORDINARIO",
        "UVT",
    }


def test_migrar_smlmv_2026_coincide_con_el_valor_conocido():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(
        ParametroLegal.clave == "SMLMV", ParametroLegal.vigente_desde == date(2026, 1, 1)
    ).one()
    session.close()
    assert fila.valor == Decimal("1750905.00")


def test_migrar_ibc_usura_primer_tramo_1997_coincide_con_inicio_y_fin():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(
        ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO", ParametroLegal.vigente_desde == date(1997, 7, 1)
    ).one()
    session.close()
    assert fila.valor == Decimal("36.50")
    assert fila.vigente_hasta == date(1997, 8, 31)


def test_migrar_usura_multiplicador_coincide_con_la_constante_actual():
    from scripts.migrate_parametros_legales import migrar

    migrar()
    session = session_module.get_session()
    fila = session.query(ParametroLegal).filter(ParametroLegal.clave == "USURA_MULTIPLICADOR").one()
    session.close()
    assert fila.valor == Decimal("1.5")


def test_migrar_es_idempotente():
    from scripts.migrate_parametros_legales import migrar

    primera = migrar()
    segunda = migrar()
    assert primera == 17
    assert segunda == 0
