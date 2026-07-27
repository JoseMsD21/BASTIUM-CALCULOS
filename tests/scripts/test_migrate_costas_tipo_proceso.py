import sqlite3
import tempfile
from pathlib import Path

from scripts.migrate_costas_tipo_proceso import migrar


def test_migrar_agrega_las_dos_columnas_en_bd_sin_ellas():
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
        assert "costas_tipo_proceso" in columnas
        assert "costas_instancia" in columnas


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
