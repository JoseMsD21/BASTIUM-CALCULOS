"""Migracion de esquema (Sprint 18, ultraactividad CPC->CGP): agrega la
columna fecha_providencia_costas a la tabla obligaciones. Idempotente --
verifica con PRAGMA table_info antes de alterar (mismo patron que
scripts/migrate_costas_tipo_proceso.py)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna si no existe. Retorna True si aplico el ALTER TABLE,
    False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "fecha_providencia_costas" not in columnas:
            con.execute("ALTER TABLE obligaciones ADD COLUMN fecha_providencia_costas DATE")
            con.commit()
            return True
        return False
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna fecha_providencia_costas agregada a obligaciones.")
    else:
        print("La columna fecha_providencia_costas ya existia, no se hizo nada.")
