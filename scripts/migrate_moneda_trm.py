"""Migracion de esquema (Sprint 12): agrega las columnas moneda, trm_aplicable
y trm_fecha_referencia a la tabla obligaciones. Idempotente -- verifica con
PRAGMA table_info antes de alterar cada columna individualmente, para poder
correrse mas de una vez (ej. en otra maquina de desarrollo, en CI, o si una
corrida anterior quedo a medias) sin fallar. No usa Alembic porque el proyecto
todavia no tiene migraciones formales (mismo patron que
scripts/migrate_aplica_indexacion_ipc.py, Sprint 8)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "moneda": "VARCHAR(3) NOT NULL DEFAULT 'COP'",
    "trm_aplicable": "NUMERIC(9, 4)",
    "trm_fecha_referencia": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas moneda/trm_aplicable/trm_fecha_referencia si no
    existen. Retorna True si aplico al menos un ALTER TABLE, False si las tres
    columnas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        aplico_alguna = False
        for nombre, definicion in _COLUMNAS.items():
            if nombre in columnas_existentes:
                continue
            con.execute(f"ALTER TABLE obligaciones ADD COLUMN {nombre} {definicion}")
            aplico_alguna = True
        con.commit()
        return aplico_alguna
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas moneda/trm_aplicable/trm_fecha_referencia agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
