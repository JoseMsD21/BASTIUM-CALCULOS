import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_add_indices_recalculo_historico import migrar


def _crear_tabla_audit_logs(con):
    con.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, fecha_ejecucion TEXT, "
        "obsoleto_requiere_recalculo BOOLEAN, liquidacion_anterior_id INTEGER)"
    )
    con.commit()


def test_migrar_crea_los_3_indices_en_bd_sin_ellos():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tabla_audit_logs(con)
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        nombres = {fila[1] for fila in con.execute("PRAGMA index_list(audit_logs)")}
        con.close()
        assert "ix_audit_logs_fecha_ejecucion" in nombres
        assert "ix_audit_logs_obsoleto_requiere_recalculo" in nombres
        assert "ix_audit_logs_liquidacion_anterior_id" in nombres


def test_migrar_es_idempotente():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        _crear_tabla_audit_logs(con)
        con.close()

        migrar(db_path)
        aplico_segunda_vez = migrar(db_path)
        assert aplico_segunda_vez is False


def test_migrar_omite_tabla_faltante_sin_crashear():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE otra_tabla (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()

        aplico = migrar(db_path)
        assert aplico is False
