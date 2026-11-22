"""Migracion de esquema (Sprint 106): agrega a la tabla expedientes los datos
del titulo ejecutivo, capturados una sola vez por caso -- tipo_titulo,
numero_identificador_titulo, fecha_expedicion_otorgamiento,
fecha_exigibilidad, es_primera_copia_ejecutiva, fecha_ejecutoria y
termino_prescripcion_anos. fecha_limite_prescripcion NO se guarda: se calcula
(ver app/services/titulo_ejecutivo.py). Todas quedan NULL en los expedientes
existentes ("no capturado"). Idempotente -- verifica con PRAGMA table_info
antes de alterar cada columna, mismo patron que
scripts/migrate_tope_suspensivo_tributario_sprint84.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_COLUMNAS = {
    "tipo_titulo": "VARCHAR(10)",
    "numero_identificador_titulo": "VARCHAR(100)",
    "fecha_expedicion_otorgamiento": "DATE",
    "fecha_exigibilidad": "DATE",
    "es_primera_copia_ejecutiva": "BOOLEAN",
    "fecha_ejecutoria": "DATE",
    "termino_prescripcion_anos": "INTEGER",
}


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las columnas si no existen. Retorna True si aplico al menos un
    ALTER TABLE, False si todas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {fila[1] for fila in con.execute("PRAGMA table_info(expedientes)")}
        aplico_alguna = False
        for nombre, definicion in _COLUMNAS.items():
            if nombre in columnas_existentes:
                continue
            con.execute(f"ALTER TABLE expedientes ADD COLUMN {nombre} {definicion}")
            aplico_alguna = True
        con.commit()
        return aplico_alguna
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas del titulo ejecutivo agregadas a expedientes.")
    else:
        print("Las columnas del titulo ejecutivo ya existian en expedientes.")
