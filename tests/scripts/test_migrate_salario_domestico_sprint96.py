import sqlite3

import pytest

from scripts.migrate_salario_domestico_sprint96 import migrar


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Liquidacion de contrato')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_dos_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"salario_diario", "dias_laborados_semana"} <= columnas


def test_migrar_preserva_las_filas_existentes_con_nulos(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute(
        "SELECT concepto, salario_diario, dias_laborados_semana "
        "FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Liquidacion de contrato", None, None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_dos_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN salario_diario NUMERIC(18, 2)")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert {"salario_diario", "dias_laborados_semana"} <= columnas
