"""Migracion de esquema (Sprint 20): agrega la columna
interes_sobre_capital_indexado a la tabla obligaciones. Idempotente -- verifica
con PRAGMA table_info antes de alterar, para poder correrse mas de una vez
(ej. en otra maquina de desarrollo o en CI) sin fallar. Mismo patron que
scripts/migrate_aplica_indexacion_ipc.py (Sprint 8)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna interes_sobre_capital_indexado si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "interes_sobre_capital_indexado" in columnas:
            return False
        con.execute(
            "ALTER TABLE obligaciones ADD COLUMN interes_sobre_capital_indexado "
            "BOOLEAN NOT NULL DEFAULT 0"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna interes_sobre_capital_indexado agregada a obligaciones.")
    else:
        print("La columna interes_sobre_capital_indexado ya existia, no se hizo nada.")
