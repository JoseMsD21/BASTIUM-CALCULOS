"""Migracion de esquema (Sprint 96): agrega las columnas salario_diario y
dias_laborados_semana a la tabla obligaciones -- soporte de la captura de un
salario pactado por dia (trabajo domestico por dias/jornada parcial) en el
area Laboral. Ver app/engine/labor/salario_domestico.py y
database/models.py::Obligacion. Idempotente -- verifica con PRAGMA
table_info antes de alterar cada columna individualmente, mismo patron que
scripts/migrate_dismissal_indemnity_sprint92.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "salario_diario": "NUMERIC(18, 2)",
    "dias_laborados_semana": "INTEGER",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas salario_diario/dias_laborados_semana si no
    existen. Retorna True si aplico al menos un ALTER TABLE, False si las 2
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
        print("Columnas salario_diario/dias_laborados_semana agregadas a obligaciones.")
    else:
        print("Las columnas salario_diario/dias_laborados_semana ya existian, no se hizo nada.")
