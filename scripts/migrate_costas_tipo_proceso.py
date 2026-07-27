"""Migracion de esquema (Sprint 18): agrega las columnas costas_tipo_proceso y
costas_instancia a la tabla obligaciones. Idempotente -- verifica con
PRAGMA table_info antes de alterar."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las dos columnas si no existen. Retorna True si aplico algun
    ALTER TABLE, False si ambas columnas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        aplico = False
        if "costas_tipo_proceso" not in columnas:
            con.execute("ALTER TABLE obligaciones ADD COLUMN costas_tipo_proceso VARCHAR(60)")
            aplico = True
        if "costas_instancia" not in columnas:
            con.execute("ALTER TABLE obligaciones ADD COLUMN costas_instancia VARCHAR(10)")
            aplico = True
        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas costas_tipo_proceso/costas_instancia agregadas a obligaciones.")
    else:
        print("Las columnas costas_tipo_proceso/costas_instancia ya existian, no se hizo nada.")
