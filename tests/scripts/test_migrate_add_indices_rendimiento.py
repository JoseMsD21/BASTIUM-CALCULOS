import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_add_indices_rendimiento import migrar


def _crear_tablas(con):
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
    con.execute("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
    con.execute("CREATE TABLE abonos (id INTEGER PRIMARY KEY, obligacion_id INTEGER)")
    con.execute("CREATE TABLE parametros_legales (id INTEGER PRIMARY KEY, clave TEXT)")
    con.commit()


def test_migrar_crea_los_4_indices_en_bd_sin_ellos():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tablas(con)
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        nombres = {
            tabla: {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            for tabla in ("obligaciones", "audit_logs", "abonos", "parametros_legales")
        }
        con.close()
        assert "ix_obligaciones_expediente_id" in nombres["obligaciones"]
        assert "ix_audit_logs_expediente_id" in nombres["audit_logs"]
        assert "ix_abonos_obligacion_id" in nombres["abonos"]
        assert "ix_parametros_legales_clave" in nombres["parametros_legales"]


def test_migrar_es_idempotente():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tablas(con)
        con.close()

        migrar(db_path)
        aplico_segunda_vez = migrar(db_path)
        assert aplico_segunda_vez is False


def test_migrar_omite_tabla_faltante_sin_crashear_y_sigue_con_las_demas():
    # Snapshot parcial/inusual de bastium.db: falta la tabla "abonos". Antes
    # del fix, PRAGMA index_list(abonos) no lanzaba error (tabla inexistente
    # devuelve vacio), asi que el CREATE INDEX posterior explotaba con
    # sqlite3.OperationalError a medio loop, dejando ya confirmados (DDL
    # autocommit) los indices de las tablas anteriores sin ningun mensaje
    # util. El comportamiento correcto es omitir la tabla faltante con un
    # aviso y seguir indexando las demas -- no bloquear el resto de la
    # migracion por una tabla incidental que no existe en este snapshot.
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
        con.execute("CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, expediente_id INTEGER)")
        con.execute("CREATE TABLE parametros_legales (id INTEGER PRIMARY KEY, clave TEXT)")
        con.commit()
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        nombres = {
            tabla: {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            for tabla in ("obligaciones", "audit_logs", "parametros_legales")
        }
        con.close()
        assert "ix_obligaciones_expediente_id" in nombres["obligaciones"]
        assert "ix_audit_logs_expediente_id" in nombres["audit_logs"]
        assert "ix_parametros_legales_clave" in nombres["parametros_legales"]
