"""Migracion de esquema (Sprint 44, punto 1): agrega la columna es_smmlv a la
tabla obligaciones. Idempotente -- verifica con PRAGMA table_info antes de
alterar, mismo patron exacto que scripts/migrate_seguridad_social_laboral.py
(Sprint 16).

No hace falta una migracion separada para la tabla nueva `descuentos_laborales`
(Sprint 44, punto 3): `Base.metadata.create_all()` (database.init_db()) ya crea
cualquier tabla que todavia no exista, tanto en una bastium.db nueva como en
una existente -- solo las columnas nuevas AGREGADAS A UNA TABLA YA EXISTENTE
(como es_smmlv aqui) necesitan un ALTER TABLE explicito."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna es_smmlv si no existe. Retorna True si aplico el
    ALTER TABLE, False si la columna ya existia."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {fila[1] for fila in con.execute("PRAGMA table_info(obligaciones)")}
        if "es_smmlv" in columnas_existentes:
            return False
        con.execute("ALTER TABLE obligaciones ADD COLUMN es_smmlv BOOLEAN NOT NULL DEFAULT 0")
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna es_smmlv agregada a obligaciones.")
    else:
        print("La columna ya existia, no se hizo nada.")
