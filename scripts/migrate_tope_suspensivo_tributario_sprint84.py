"""Migracion de esquema (Sprint 84, seguimiento): agrega las columnas
fecha_admision_demanda y fecha_notificacion_sentencia a la tabla
obligaciones -- tope suspensivo del interes moratorio tributario por demanda
ante lo contencioso administrativo (ver app/engine/tax/tope_suspensivo.py).
fecha_tope_24m y fecha_reanudacion_interes NO se guardan: se calculan siempre
a partir de estas dos. Idempotente -- verifica con PRAGMA table_info antes de
alterar cada columna, mismo patron que
scripts/migrate_dismissal_indemnity_sprint92.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "fecha_admision_demanda": "DATE",
    "fecha_notificacion_sentencia": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas si no existen. Retorna True si aplico al menos un
    ALTER TABLE, False si ambas ya existian."""
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
        print("Columnas fecha_admision_demanda/fecha_notificacion_sentencia agregadas.")
    else:
        print("Las columnas fecha_admision_demanda/fecha_notificacion_sentencia ya existian.")
