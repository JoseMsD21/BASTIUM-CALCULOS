"""Migracion de esquema (Sprint 92): agrega las columnas
tipo_contrato_laboral, despido_injustificado y fecha_fin_pactada a la tabla
obligaciones -- soporte de la indemnizacion por despido injustificado (Art.
64 CST) en el area Laboral. Ver app/engine/labor/dismissal_indemnity.py
(DismissalIndemnityCalculator) y database/models.py::Obligacion. Idempotente
-- verifica con PRAGMA table_info antes de alterar cada columna
individualmente, mismo patron que
scripts/migrate_indexacion_ipc_areas_sprint43.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "tipo_contrato_laboral": "VARCHAR(11) NOT NULL DEFAULT 'INDEFINIDO'",
    "despido_injustificado": "BOOLEAN NOT NULL DEFAULT 0",
    "fecha_fin_pactada": "DATE",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas tipo_contrato_laboral/despido_injustificado/
    fecha_fin_pactada si no existen. Retorna True si aplico al menos un
    ALTER TABLE, False si las 3 columnas ya existian."""
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
            "Columnas tipo_contrato_laboral/despido_injustificado/fecha_fin_pactada "
            "agregadas a obligaciones."
        )
    else:
        print(
            "Las columnas tipo_contrato_laboral/despido_injustificado/fecha_fin_pactada "
            "ya existian, no se hizo nada."
        )
