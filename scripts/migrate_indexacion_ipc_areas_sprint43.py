"""Migracion de esquema (Sprint 43): agrega las columnas pacto_expreso_indexacion
y protegida_inflacion_uvr a la tabla obligaciones -- soporte de indexacion IPC en
Comercial (XOR con la tasa comercial, solo con pacto expreso en el titulo) y
Tributario (prohibicion de doble cobro si el titulo ya incorpora proteccion
inflacionaria propia, ej. UVR). Ver app/services/area_strategy.py
(ComercialStrategy/TributarioStrategy) y database/models.py::Obligacion. Idempotente
-- verifica con PRAGMA table_info antes de alterar cada columna individualmente,
mismo patron que scripts/migrate_fechas_anuales_fijas.py (Sprint 73)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "pacto_expreso_indexacion": "BOOLEAN NOT NULL DEFAULT 0",
    "protegida_inflacion_uvr": "BOOLEAN NOT NULL DEFAULT 0",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas pacto_expreso_indexacion/protegida_inflacion_uvr si no
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
        print(
            "Columnas pacto_expreso_indexacion/protegida_inflacion_uvr agregadas a obligaciones."
        )
    else:
        print(
            "Las columnas pacto_expreso_indexacion/protegida_inflacion_uvr ya existian, "
            "no se hizo nada."
        )
