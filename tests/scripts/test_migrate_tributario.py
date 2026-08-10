import sqlite3

import pytest

from scripts.migrate_tributario import migrar

_COLUMNAS_NUEVAS = {
    "base_sancion_tributaria",
    "meses_extemporaneidad",
    "sancion_agravada",
    "ingresos_brutos",
    "devoluciones_rebajas_descuentos",
    "costos",
    "deducciones",
    "rentas_exentas",
}


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute("CREATE TABLE obligaciones (id INTEGER PRIMARY KEY, concepto TEXT)")
    con.execute("INSERT INTO obligaciones (id, concepto) VALUES (1, 'Impuesto de renta 2024')")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_ocho_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert _COLUMNAS_NUEVAS <= columnas


def test_migrar_preserva_las_filas_existentes_con_sancion_agravada_falso_por_defecto(
    db_sin_columnas,
):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila = con.execute(
        "SELECT concepto, sancion_agravada FROM obligaciones WHERE id = 1"
    ).fetchone()
    con.close()
    assert fila == ("Impuesto de renta 2024", 0)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_es_idempotente_si_ya_existe_solo_una_de_las_ocho_columnas(db_sin_columnas):
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE obligaciones ADD COLUMN base_sancion_tributaria NUMERIC(18, 2)")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
    con.close()
    assert _COLUMNAS_NUEVAS <= columnas
