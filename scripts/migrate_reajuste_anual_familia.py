"""Migracion de esquema (Sprint 41): agrega las columnas tipo_reajuste_anual y
obligacion_padre_id a la tabla obligaciones -- soporte de cuotas alimentarias
(Civil/Familia) con reajuste anual (SMMLV/IPC) generadas y persistidas como
Obligacion PUNTUAL hijas (ver app/services/reajuste_anual.py). Idempotente --
verifica con PRAGMA table_info antes de alterar cada columna individualmente,
mismo patron que scripts/migrate_anatocismo_comercial.py (Sprint 19)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "tipo_reajuste_anual": "VARCHAR(10) NOT NULL DEFAULT 'NINGUNO'",
    # Sin REFERENCES: ver el comentario junto a Obligacion.obligacion_padre_id
    # en database/models.py -- una FK real bloquearia futuras migraciones que
    # necesiten recrear esta columna, y esta app nunca activa
    # PRAGMA foreign_keys=ON.
    "obligacion_padre_id": "INTEGER",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas tipo_reajuste_anual/obligacion_padre_id si no
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
        print("Columnas tipo_reajuste_anual/obligacion_padre_id agregadas a obligaciones.")
    else:
        print("Las columnas tipo_reajuste_anual/obligacion_padre_id ya existian, no se hizo nada.")
