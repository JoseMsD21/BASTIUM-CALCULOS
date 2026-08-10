"""Migracion de esquema (Sprint 25, hallazgo 4): agrega 4 indices a columnas
de filtrado frecuente de una bastium.db ya existente --
Base.metadata.create_all() (database/database.py) solo crea tablas que
todavia no existen, nunca agrega un indice a una tabla ya creada. Idempotente
via PRAGMA index_list, mismo patron que scripts/migrate_costas_tipo_proceso.py
(que usa PRAGMA table_info para columnas)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_INDICES = [
    ("ix_obligaciones_expediente_id", "obligaciones", "expediente_id"),
    ("ix_audit_logs_expediente_id", "audit_logs", "expediente_id"),
    ("ix_abonos_obligacion_id", "abonos", "obligacion_id"),
    ("ix_parametros_legales_clave", "parametros_legales", "clave"),
]


def _tabla_existe(con: sqlite3.Connection, tabla: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
    ).fetchone()
    return fila is not None


def migrar(db_path: Path = DB_PATH) -> bool:
    """Crea los 4 indices si no existen. Retorna True si creo alguno, False
    si los 4 ya existian. Si una tabla no existe en esta bastium.db (snapshot
    parcial o inusual), se omite esa tabla con un aviso en vez de fallar con
    un traceback crudo -- PRAGMA index_list de una tabla inexistente no
    lanza error (devuelve vacio), asi que sin esta verificacion el CREATE
    INDEX posterior explota a medio loop con sqlite3.OperationalError,
    dejando indices previos ya confirmados (DDL en sqlite3 autocommitea) y
    sin mensaje util sobre cual tabla fallo."""
    con = sqlite3.connect(db_path)
    try:
        aplico = False
        for nombre_indice, tabla, columna in _INDICES:
            if not _tabla_existe(con, tabla):
                print(
                    f"Aviso: la tabla '{tabla}' no existe en {db_path}, "
                    f"se omite el indice {nombre_indice}."
                )
                continue
            indices_existentes = {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            if nombre_indice in indices_existentes:
                continue
            con.execute(f"CREATE INDEX {nombre_indice} ON {tabla}({columna})")
            aplico = True
        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print(
            "Indices de rendimiento agregados (obligaciones, audit_logs, abonos, "
            "parametros_legales)."
        )
    else:
        print("Los 4 indices ya existian, no se hizo nada.")
