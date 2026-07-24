"""Migracion de esquema (Sprint 16): agrega las columnas incluir_seguridad_social
y nivel_riesgo_arl a la tabla obligaciones. Idempotente -- verifica con PRAGMA
table_info antes de alterar cada columna individualmente, mismo patron exacto
que scripts/migrate_moneda_trm.py (Sprint 12)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "incluir_seguridad_social": "BOOLEAN NOT NULL DEFAULT 0",
    "nivel_riesgo_arl": "VARCHAR(2)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas incluir_seguridad_social/nivel_riesgo_arl si no
    existen. Retorna True si aplico al menos un ALTER TABLE, False si las dos
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
        print("Columnas incluir_seguridad_social/nivel_riesgo_arl agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
