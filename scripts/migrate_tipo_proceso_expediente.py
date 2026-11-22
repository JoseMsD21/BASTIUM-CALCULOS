"""Migracion de esquema (Sprint 105): agrega la columna tipo_proceso a la
tabla expedientes. Idempotente -- verifica con PRAGMA table_info antes de
alterar, mismo patron que scripts/migrate_tipo_accion_proceso.py. Columna
nullable sin DEFAULT: un expediente anterior a este sprint queda sin tipo de
proceso (catalogo informativo, app/services/catalogo_tipos_proceso.py) y
sigue funcionando exactamente igual."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna tipo_proceso si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(expedientes)")}
        if "tipo_proceso" in columnas:
            return False
        con.execute("ALTER TABLE expedientes ADD COLUMN tipo_proceso VARCHAR(60)")
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna tipo_proceso agregada a expedientes.")
    else:
        print("La columna tipo_proceso ya existia, no se hizo nada.")
