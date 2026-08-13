import sqlite3
from datetime import datetime

import pytest

from scripts.migrate_creado_por_sistema import migrar


@pytest.fixture
def db_sin_columna(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute(
        """CREATE TABLE parametros_legales (
            id INTEGER PRIMARY KEY,
            clave TEXT,
            valor TEXT,
            vigente_desde TEXT,
            usuario TEXT,
            creado_en TEXT
        )"""
    )
    con.execute(
        "INSERT INTO parametros_legales (id, clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES (1, 'SMLMV', '1000000', '2026-01-01', 'sistema', ?)",
        (datetime.now().isoformat(),),
    )
    con.execute(
        "INSERT INTO parametros_legales (id, clave, valor, vigente_desde, usuario, creado_en) "
        "VALUES (2, 'USURA_MULTIPLICADOR', '1.5', '2026-01-01', 'abogado1', ?)",
        (datetime.now().isoformat(),),
    )
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_la_columna_y_retorna_true(db_sin_columna):
    aplicada = migrar(db_sin_columna)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columna)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")}
    con.close()
    assert "creado_por_sistema" in columnas


def test_migrar_marca_como_sistema_solo_las_filas_con_usuario_sistema(db_sin_columna):
    migrar(db_sin_columna)

    con = sqlite3.connect(db_sin_columna)
    filas = dict(con.execute("SELECT id, creado_por_sistema FROM parametros_legales").fetchall())
    con.close()
    assert filas == {1: 1, 2: 0}


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columna):
    primera = migrar(db_sin_columna)
    segunda = migrar(db_sin_columna)
    assert primera is True
    assert segunda is False
