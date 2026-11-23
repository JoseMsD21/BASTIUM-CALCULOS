"""Migracion de esquema (Sprint 100, wiring del fruto civil): agrega las
columnas fecha_referencia_canon y gasto_conservacion_mensual a la tabla
obligaciones -- datos de una obligacion Civil/Familia de categoria
FRUTO_CIVIL (beneficio dejado de percibir, Art. 964 C.C.). Ver
app/engine/civil/fruto_civil.py y database/models.py::Obligacion.
Idempotente -- verifica con PRAGMA table_info antes de alterar cada columna
individualmente, mismo patron que scripts/migrate_salario_domestico_sprint96.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "fecha_referencia_canon": "DATE",
    "gasto_conservacion_mensual": "NUMERIC(18, 2)",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas del fruto civil si no existen. Retorna True si
    aplico al menos un ALTER TABLE, False si ya existian."""
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
        print("Columnas del fruto civil agregadas a obligaciones.")
    else:
        print("Las columnas del fruto civil ya existian, no se hizo nada.")
