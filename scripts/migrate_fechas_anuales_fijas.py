"""Migracion de esquema (Sprint 73): agrega las columnas tipo_recurrencia y
fechas_anuales_fijas a la tabla obligaciones -- soporte de obligaciones
RECURRENTE con cadencia de fechas anuales fijas (ej. gastos de vestuario en
junio/diciembre/cumpleanos del beneficiario) en vez de una cuota mensual (ver
app/services/recurrencia_fechas_fijas.py). Idempotente -- verifica con PRAGMA
table_info antes de alterar cada columna individualmente, mismo patron que
scripts/migrate_reajuste_anual_familia.py (Sprint 41)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "tipo_recurrencia": "VARCHAR(30) NOT NULL DEFAULT 'MENSUAL'",
    "fechas_anuales_fijas": "VARCHAR(300)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas tipo_recurrencia/fechas_anuales_fijas si no
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
        print("Columnas tipo_recurrencia/fechas_anuales_fijas agregadas a obligaciones.")
    else:
        print("Las columnas tipo_recurrencia/fechas_anuales_fijas ya existian, no se hizo nada.")
