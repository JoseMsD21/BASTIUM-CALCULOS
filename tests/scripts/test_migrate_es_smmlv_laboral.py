import sqlite3

import pytest

from scripts.migrate_es_smmlv_laboral import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Liquidacion de contrato')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert "es_smmlv" in columnas


def test_migrar_preserva_las_filas_existentes_con_default_false(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    fila = con.execute("SELECT concepto, es_smmlv FROM obligaciones WHERE id = 1").fetchone()
    con.close()
    assert fila == ("Liquidacion de contrato", 0)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
