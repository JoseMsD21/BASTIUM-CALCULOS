"""Migracion de esquema (Sprint 15): agrega las columnas propias del area
Tributario a la tabla obligaciones (base_sancion_tributaria,
meses_extemporaneidad, sancion_agravada, y los 5 campos de Renta Liquida
Gravable). Idempotente -- mismo patron que scripts/migrate_moneda_trm.py
(Sprint 12): verifica con PRAGMA table_info antes de alterar cada columna."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "base_sancion_tributaria": "NUMERIC(18, 2)",
    "meses_extemporaneidad": "INTEGER",
    "sancion_agravada": "BOOLEAN NOT NULL DEFAULT 0",
    "ingresos_brutos": "NUMERIC(18, 2)",
    "devoluciones_rebajas_descuentos": "NUMERIC(18, 2)",
    "costos": "NUMERIC(18, 2)",
    "deducciones": "NUMERIC(18, 2)",
    "rentas_exentas": "NUMERIC(18, 2)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas tributarias si no existen. Retorna True si aplico al menos
    un ALTER TABLE, False si las ocho columnas ya existian."""
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
        print("Columnas tributarias agregadas a obligaciones.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
