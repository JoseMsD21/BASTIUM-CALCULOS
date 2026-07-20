"""Migracion de esquema (Sprint 8): agrega la columna aplica_indexacion_ipc a
la tabla obligaciones. Idempotente -- verifica con PRAGMA table_info antes de
alterar, para poder correrse mas de una vez (ej. en otra maquina de desarrollo
o en CI) sin fallar. No usa Alembic porque el proyecto todavia no tiene
migraciones formales (ver Pendientes.md, Sprint 8 design doc)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna aplica_indexacion_ipc si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "aplica_indexacion_ipc" in columnas:
            return False
        con.execute(
            "ALTER TABLE obligaciones ADD COLUMN aplica_indexacion_ipc BOOLEAN NOT NULL DEFAULT 0"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna aplica_indexacion_ipc agregada a obligaciones.")
    else:
        print("La columna aplica_indexacion_ipc ya existia, no se hizo nada.")
