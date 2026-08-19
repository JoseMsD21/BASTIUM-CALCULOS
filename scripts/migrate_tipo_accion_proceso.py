"""Migracion de esquema (Sprint 61): agrega la columna tipo_accion_proceso a
la tabla obligaciones. Idempotente -- verifica con PRAGMA table_info antes de
alterar, mismo patron que scripts/migrate_aplica_indexacion_ipc.py. Columna
nullable sin DEFAULT: una obligacion sin este campo simplemente no se alerta
de prescripcion/caducidad no-ejecutiva (comportamiento identico al de hoy),
no es un caso de error -- ver docs/superpowers/specs/
2026-08-14-sprint61-wiring-parametros-prescripcion-design.md."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna tipo_accion_proceso si no existe.
    Retorna True si aplico el ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "tipo_accion_proceso" in columnas:
            return False
        con.execute("ALTER TABLE obligaciones ADD COLUMN tipo_accion_proceso TEXT")
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna tipo_accion_proceso agregada a obligaciones.")
    else:
        print("La columna tipo_accion_proceso ya existia, no se hizo nada.")
