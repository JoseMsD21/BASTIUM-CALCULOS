import sqlite3
from contextlib import contextmanager
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
        "tipo_reajuste_anual",
        "obligacion_padre_id",
    ):
        con.execute(f"ALTER TABLE obligaciones DROP COLUMN {columna}")
    con.commit()
    con.close()


def _apuntar_session_module_a(engine, monkeypatch) -> None:
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


@contextmanager
def _sesion_para(db_path: Path):
    """Sesion SQLAlchemy ad hoc apuntando directamente a db_path -- a
    diferencia de _apuntar_session_module_a(), no toca el engine global de
    database.database ni el SessionLocal de database.session. Sirve para
    verificar, tras el fix del Sprint 52, que migrate_parametros_legales.migrar()
    ya siembra en db_path por si solo (via su propio engine ad hoc) sin que el
    test necesite redirigir el engine global para poder leer el resultado.

    Context manager (en vez de devolver solo la sesion) para garantizar que
    tanto la Session como el Engine SQLite ad hoc se cierren siempre --
    dejarlos a merced del GC produce ResourceWarning: unclosed database y, en
    Windows, PermissionError intermitente al limpiar tmp_path."""
    engine = create_engine(f"sqlite:///{db_path}")
    session = sessionmaker(bind=engine, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()


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
        "tipo_reajuste_anual",
        "obligacion_padre_id",
    ):
        assert columna in columnas


def test_aplicar_migraciones_pendientes_agrega_es_smmlv(tmp_path):
    """Sprint 44, punto 1: una bastium.db creada antes de este sprint no tiene
    la columna es_smmlv -- aplicar_migraciones_pendientes() debe agregarla,
    mismo criterio que las 5 columnas de Sprints 18/19/20 arriba."""
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "sin_es_smmlv.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    con.execute("ALTER TABLE obligaciones DROP COLUMN es_smmlv")
    con.commit()
    con.close()

    aplicar_migraciones_pendientes(db_path)

    con = sqlite3.connect(db_path)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert "es_smmlv" in columnas


def test_migracion_reajuste_anual_agrega_columnas_con_default_ninguno_y_null(tmp_path):
    """Task 1 del Sprint 41: una fila de obligaciones ya existente (creada bajo el
    esquema viejo, sin tipo_reajuste_anual/obligacion_padre_id) debe quedar con
    tipo_reajuste_anual='NINGUNO' (mismo default que el modelo SQLAlchemy,
    TipoReajusteAnual.NINGUNO) y obligacion_padre_id=NULL despues de migrar --
    nunca None/obligatorio en filas legadas."""
    from scripts.migrate_reajuste_anual_familia import migrar

    db_path = tmp_path / "reajuste_anual.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    con.execute("ALTER TABLE obligaciones DROP COLUMN tipo_reajuste_anual")
    con.execute("ALTER TABLE obligaciones DROP COLUMN obligacion_padre_id")
    con.execute(
        "INSERT INTO expedientes (radicado, demandante, demandado, area_derecho, "
        "fecha_corte_default) VALUES ('X-1', 'A', 'B', 'CIVIL_FAMILIA', '2026-01-01')"
    )
    con.execute(
        "INSERT INTO obligaciones (expediente_id, tipo, concepto, categoria, "
        "fecha_origen, valor, tasa_efectiva_anual, pagada, aplica_indexacion_ipc, "
        "interes_sobre_capital_indexado, moneda, anatocismo_demanda_judicial, "
        "sancion_agravada, incluir_seguridad_social, es_smmlv) VALUES "
        "(1, 'PUNTUAL', 'Cuota alimentaria', 'CHILD_SUPPORT', '2026-01-01', "
        "'100000.00', '6.00', 0, 0, 0, 'COP', 0, 0, 0, 0)"
    )
    con.commit()
    con.close()

    aplico = migrar(db_path)
    assert aplico is True

    con = sqlite3.connect(db_path)
    fila = con.execute(
        "SELECT tipo_reajuste_anual, obligacion_padre_id FROM obligaciones"
    ).fetchone()
    con.close()
    assert fila == ("NINGUNO", None)

    # Idempotencia: correrla de nuevo no vuelve a alterar nada ni rompe.
    assert migrar(db_path) is False


def test_aplicar_migraciones_pendientes_siembra_parametros_legales(tmp_path):
    """Sprint 52: ya no hace falta _apuntar_session_module_a -- desde el fix,
    migrate_parametros_legales.migrar(db_path) siembra directamente en
    db_path via su propio engine ad hoc, asi que basta con leer ese mismo
    archivo con una sesion aparte para verificar el resultado."""
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "nueva.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    aplicar_migraciones_pendientes(db_path)

    with _sesion_para(db_path) as session:
        claves = {fila.clave for fila in session.query(ParametroLegal).all()}
    assert len(claves) == 39


def test_aplicar_migraciones_pendientes_es_idempotente(tmp_path):
    """Sprint 52: idem -- ya no hace falta _apuntar_session_module_a."""
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "idempotente.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    aplicar_migraciones_pendientes(db_path)
    with _sesion_para(db_path) as session:
        total_filas_primera_vez = session.query(ParametroLegal).count()

    aplicar_migraciones_pendientes(db_path)
    with _sesion_para(db_path) as session:
        total_filas_segunda_vez = session.query(ParametroLegal).count()

    assert total_filas_segunda_vez == total_filas_primera_vez


def test_aplicar_migraciones_pendientes_siembra_parametros_legales_en_db_path(tmp_path):
    """Regresion Sprint 52 (hallazgo 3): antes del fix, migrar_parametros_legales()
    ignoraba por completo el db_path que aplicar_migraciones_pendientes() le
    pasa a las otras 10 migraciones, y sembraba siempre contra el engine
    global de database.database. Este test NO parchea ese engine global de
    ninguna forma (a diferencia de _apuntar_session_module_a, usado en otros
    tests de este archivo) y verifica el resultado con sqlite3 crudo sobre
    db_path, para que sea imposible que pase "por accidente" contra otra
    base: si el bug reaparece, parametros_legales en db_path queda vacia."""
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "aislada.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    aplicar_migraciones_pendientes(db_path)

    con = sqlite3.connect(db_path)
    (total_claves,) = con.execute(
        "SELECT COUNT(DISTINCT clave) FROM parametros_legales"
    ).fetchone()
    con.close()
    assert total_claves == 39


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


def test_migrar_parametros_area_unidad_agrega_columnas_y_completa_filas_legadas(tmp_path):
    """Sprint 57: una bastium.db creada antes de este sprint no tiene las
    columnas areas_derecho/unidad -- el script debe agregarlas (nullable, sin
    DEFAULT unico posible porque el valor varia por clave) y completarlas para
    cualquier fila ya sembrada, segun AREA_UNIDAD_POR_CLAVE."""
    from app.services.areas_parametro import deserializar_areas
    from database.models import AreaDerecho
    from scripts.migrate_parametros_area_unidad import migrar

    db_path = tmp_path / "sin_area_unidad.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    con.execute("ALTER TABLE parametros_legales DROP COLUMN areas_derecho")
    con.execute("ALTER TABLE parametros_legales DROP COLUMN unidad")
    con.execute(
        "INSERT INTO parametros_legales (clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES ('SMLMV', '1750905.00', '2026-01-01', 'test', '2026-01-01 00:00:00')"
    )
    con.execute(
        "INSERT INTO parametros_legales (clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES ('USURA_MULTIPLICADOR', '1.5', '1990-01-01', 'test', '2026-01-01 00:00:00')"
    )
    con.commit()
    con.close()

    aplico = migrar(db_path)
    assert aplico is True

    con = sqlite3.connect(db_path)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")}
    assert "areas_derecho" in columnas
    assert "unidad" in columnas

    fila_smlmv = con.execute(
        "SELECT areas_derecho, unidad FROM parametros_legales WHERE clave = 'SMLMV'"
    ).fetchone()
    fila_usura = con.execute(
        "SELECT areas_derecho, unidad FROM parametros_legales WHERE clave = 'USURA_MULTIPLICADOR'"
    ).fetchone()
    con.close()

    assert deserializar_areas(fila_smlmv[0]) == [
        AreaDerecho.CIVIL_FAMILIA,
        AreaDerecho.LABORAL,
        AreaDerecho.SANCIONATORIO,
        AreaDerecho.COMERCIAL,
        AreaDerecho.HONORARIOS,
    ]
    assert fila_smlmv[1] == "COP"
    assert deserializar_areas(fila_usura[0]) == [AreaDerecho.COMERCIAL]
    assert fila_usura[1] == "veces"

    # Idempotencia: correrla de nuevo no rompe ni vuelve a reportar cambios.
    assert migrar(db_path) is False


def test_migrar_parametros_area_unidad_no_toca_filas_ya_migradas(tmp_path):
    """No debe sobrescribir una fila que ya tiene areas_derecho/unidad
    asignados (aunque el valor guardado sea distinto del que la tabla
    propondria hoy) -- solo completa filas todavia sin migrar."""
    from scripts.migrate_parametros_area_unidad import migrar

    db_path = tmp_path / "parcial.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    con = sqlite3.connect(db_path)
    con.execute(
        "INSERT INTO parametros_legales "
        "(clave, valor, vigente_desde, usuario, creado_en, areas_derecho, unidad) "
        "VALUES ('SMLMV', '1750905.00', '2026-01-01', 'test', '2026-01-01 00:00:00', "
        "'[\"TRIBUTARIO\"]', 'personalizado')"
    )
    con.commit()
    con.close()

    migrar(db_path)

    con = sqlite3.connect(db_path)
    fila = con.execute(
        "SELECT areas_derecho, unidad FROM parametros_legales WHERE clave = 'SMLMV'"
    ).fetchone()
    con.close()
    assert fila == ('["TRIBUTARIO"]', "personalizado")


def test_aplicar_migraciones_pendientes_completa_area_unidad_de_las_683_filas(tmp_path):
    """Test de integracion (Task 4, Step 6): sobre una bastium.db nueva
    completa, aplicar_migraciones_pendientes() debe sembrar las 683 filas
    (migrar_parametros_legales) Y completar areas_derecho/unidad de todas
    ellas en la misma pasada -- exige que la migracion nueva corra despues de
    la siembra, no antes."""
    from database.database import aplicar_migraciones_pendientes

    db_path = tmp_path / "nueva_area_unidad.db"
    engine = create_engine(f"sqlite:///{db_path}")
    Base.metadata.create_all(engine)
    engine.dispose()

    aplicar_migraciones_pendientes(db_path)

    con = sqlite3.connect(db_path)
    total_filas = con.execute("SELECT COUNT(*) FROM parametros_legales").fetchone()[0]
    total_sin_migrar = con.execute(
        "SELECT COUNT(*) FROM parametros_legales WHERE areas_derecho IS NULL "
        "OR areas_derecho = '' OR unidad IS NULL OR unidad = ''"
    ).fetchone()[0]
    con.close()

    assert total_filas == 683
    assert total_sin_migrar == 0


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
