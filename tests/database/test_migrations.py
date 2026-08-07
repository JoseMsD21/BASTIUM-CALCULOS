import sqlite3
from datetime import date
from decimal import Decimal
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.database as database_module
import database.session as session_module
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)


def _crear_bd_con_esquema_desactualizado(db_path: Path) -> None:
    """Crea el esquema completo actual y luego elimina las 5 columnas que los
    Sprints 18/19/20 agregaron al modelo `Obligacion` pero que nunca se
    migraron en una bastium.db real del usuario -- reproduce exactamente el
    bug reportado: sqlite3.OperationalError: no such column:
    obligaciones.costas_tipo_proceso."""
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    for columna in (
        "costas_tipo_proceso",
        "costas_instancia",
        "interes_sobre_capital_indexado",
        "anatocismo_demanda_judicial",
        "anatocismo_fecha_acuerdo",
    ):
        con.execute(f"ALTER TABLE obligaciones DROP COLUMN {columna}")
    con.commit()
    con.close()


def _apuntar_session_module_a(engine, monkeypatch) -> None:
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


def test_aplicar_migraciones_pendientes_agrega_las_columnas_faltantes_de_obligaciones(tmp_path):
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "vieja.db"
    _crear_bd_con_esquema_desactualizado(db_path)

    aplicar_migraciones_pendientes(db_path)

    con = sqlite3.connect(db_path)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    for columna in (
        "costas_tipo_proceso",
        "costas_instancia",
        "interes_sobre_capital_indexado",
        "anatocismo_demanda_judicial",
        "anatocismo_fecha_acuerdo",
    ):
        assert columna in columnas


def test_aplicar_migraciones_pendientes_siembra_parametros_legales(tmp_path, monkeypatch):
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "nueva.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    _apuntar_session_module_a(engine, monkeypatch)

    aplicar_migraciones_pendientes(db_path)

    session = session_module.get_session()
    claves = {fila.clave for fila in session.query(ParametroLegal).all()}
    session.close()
    assert len(claves) == 39


def test_aplicar_migraciones_pendientes_es_idempotente(tmp_path, monkeypatch):
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "idempotente.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    _apuntar_session_module_a(engine, monkeypatch)

    aplicar_migraciones_pendientes(db_path)
    total_filas_primera_vez = session_module.get_session().query(ParametroLegal).count()

    aplicar_migraciones_pendientes(db_path)
    total_filas_segunda_vez = session_module.get_session().query(ParametroLegal).count()

    assert total_filas_segunda_vez == total_filas_primera_vez


def test_aplicar_migraciones_pendientes_agrega_los_indices_de_rendimiento(tmp_path):
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "indices.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    con.execute("DROP INDEX IF EXISTS ix_obligaciones_expediente_id")
    con.commit()
    con.close()

    aplicar_migraciones_pendientes(db_path)

    con = sqlite3.connect(db_path)
    indices = {fila[1] for fila in con.execute("PRAGMA index_list(obligaciones)")}
    con.close()
    assert "ix_obligaciones_expediente_id" in indices


def test_dashboard_no_falla_con_esquema_desactualizado_de_obligaciones(
    tmp_path, monkeypatch, qtbot
):
    """Regresion directa del bug reportado: DashboardView.refrescar() sobre una
    bastium.db con el esquema viejo (sin las 5 columnas) lanzaba
    sqlite3.OperationalError al acceder a expediente.obligaciones."""
    from app.views.dashboard import DashboardView
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "dashboard_vieja.db"
    _crear_bd_con_esquema_desactualizado(db_path)
    aplicar_migraciones_pendientes(db_path)

    engine = create_engine(f"sqlite:///{db_path}")
    _apuntar_session_module_a(engine, monkeypatch)

    session = session_module.get_session()
    expediente = Expediente(
        radicado="X-1",
        demandante="A",
        demandado="B",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Test",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2021, 1, 1),
            valor=Decimal("100.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
