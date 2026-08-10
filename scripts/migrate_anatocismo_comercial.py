"""Migracion de esquema (Sprint 19): agrega las columnas
anatocismo_demanda_judicial y anatocismo_fecha_acuerdo a la tabla
obligaciones. Idempotente -- verifica con PRAGMA table_info antes de alterar
cada columna individualmente, mismo patron que
scripts/migrate_aplica_indexacion_ipc.py (Sprint 8) y
scripts/migrate_moneda_trm.py (Sprint 12)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "anatocismo_demanda_judicial": "BOOLEAN NOT NULL DEFAULT 0",
    "anatocismo_fecha_acuerdo": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas anatocismo_demanda_judicial/anatocismo_fecha_acuerdo
    si no existen. Retorna True si aplico al menos un ALTER TABLE, False si
    las dos columnas ya existian."""
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
        print(
            "Columnas anatocismo_demanda_judicial/anatocismo_fecha_acuerdo agregadas a "
            "obligaciones."
        )
    else:
        print("Las columnas ya existian, no se hizo nada.")
