import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_fecha_providencia_costas import migrar


def test_migrar_agrega_la_columna_en_bd_sin_ella():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()

        aplico = migrar(db_path)
        assert aplico is True

        con = sqlite3.connect(db_path)
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        con.close()
        assert "fecha_providencia_costas" in columnas


def test_migrar_es_idempotente():
    with tempfile.TemporaryDirectory() as tmp:
        db_path = Path(tmp) / "test.db"
        con = sqlite3.connect(db_path)
        con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY)")
        con.commit()
        con.close()

        migrar(db_path)
        aplico_segunda_vez = migrar(db_path)
        assert aplico_segunda_vez is False
