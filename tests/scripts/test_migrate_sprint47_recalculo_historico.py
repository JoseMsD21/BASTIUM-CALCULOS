import sqlite3

import pytest

from scripts.migrate_sprint47_recalculo_historico import migrar


@pytest.fixture
def db_sin_columnas(tmp_path):
    db_path = tmp_path / "test.db"
    con = sqlite3.connect(db_path)
    con.execute(
        "CREATE TABLE expedientes (id INTEGER PRIMARY KEY, radicado TEXT)"
    )
    con.execute("INSERT INTO expedientes (id, radicado) VALUES (1, '2026-00300')")
    con.execute(
        "CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, expediente_id INTEGER)"
    )
    con.execute("INSERT INTO audit_logs (id, expediente_id) VALUES (1, 1)")
    con.commit()
    con.close()
    return db_path


def test_migrar_agrega_las_4_columnas_y_retorna_true(db_sin_columnas):
    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas_expedientes = {fila[1] for fila in con.execute("PRAGMA table_info(expedientes)")}
    columnas_audit_logs = {fila[1] for fila in con.execute("PRAGMA table_info(audit_logs)")}
    con.close()

    assert "estado_procesal" in columnas_expedientes
    assert "obsoleto_requiere_recalculo" in columnas_audit_logs
    assert "liquidacion_anterior_id" in columnas_audit_logs
    assert "motivo_recalculo" in columnas_audit_logs


def test_migrar_preserva_filas_existentes_con_defaults_correctos(db_sin_columnas):
    migrar(db_sin_columnas)

    con = sqlite3.connect(db_sin_columnas)
    fila_expediente = con.execute(
        "SELECT radicado, estado_procesal FROM expedientes WHERE id = 1"
    ).fetchone()
    fila_audit_log = con.execute(
        "SELECT obsoleto_requiere_recalculo, liquidacion_anterior_id, motivo_recalculo "
        "FROM audit_logs WHERE id = 1"
    ).fetchone()
    con.close()

    assert fila_expediente == ("2026-00300", "EN_TRAMITE")
    assert fila_audit_log == (0, None, None)


def test_migrar_es_idempotente_segunda_corrida_retorna_false(db_sin_columnas):
    primera = migrar(db_sin_columnas)
    segunda = migrar(db_sin_columnas)
    assert primera is True
    assert segunda is False


def test_migrar_sobre_bd_parcialmente_migrada_solo_agrega_lo_faltante(db_sin_columnas):
    # Simula una BD donde alguien ya agrego estado_procesal a mano pero no las
    # columnas de audit_logs -- migrar() no debe fallar con "duplicate column".
    con = sqlite3.connect(db_sin_columnas)
    con.execute("ALTER TABLE expedientes ADD COLUMN estado_procesal TEXT DEFAULT 'EN_TRAMITE'")
    con.commit()
    con.close()

    aplicada = migrar(db_sin_columnas)
    assert aplicada is True

    con = sqlite3.connect(db_sin_columnas)
    columnas_audit_logs = {fila[1] for fila in con.execute("PRAGMA table_info(audit_logs)")}
    con.close()
    assert "motivo_recalculo" in columnas_audit_logs
