"""Migracion de esquema: agrega la columna creado_por_sistema a
parametros_legales, para distinguir de verdad los valores sembrados por
scripts/migrate_parametros_legales.py y scripts/migrate_ipc_variacion_anual.py
(usuario='sistema' por convencion, pero eso era solo texto libre, nunca un
flag real) de los que un usuario carga desde ParametroFormDialog (Sprint
"Parametros: editar/eliminar de usuario"). Backfill: toda fila ya sembrada
con usuario='sistema' queda en creado_por_sistema=1; el resto en 0. Idempotente
-- verifica con PRAGMA table_info antes de alterar, mismo patron que
scripts/migrate_es_smmlv_laboral.py."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega la columna creado_por_sistema si no existe y hace el backfill
    por usuario='sistema'. Retorna True si aplico el ALTER TABLE, False si la
    columna ya existia (backfill no se repite en ese caso -- ya corrio la
    primera vez)."""
    con = sqlite3.connect(db_path)
    try:
        columnas_existentes = {
            fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")
        }
        if "creado_por_sistema" in columnas_existentes:
            return False
        con.execute(
            "ALTER TABLE parametros_legales ADD COLUMN creado_por_sistema "
            "BOOLEAN NOT NULL DEFAULT 0"
        )
        con.execute(
            "UPDATE parametros_legales SET creado_por_sistema = 1 WHERE usuario = 'sistema'"
        )
        con.commit()
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columna creado_por_sistema agregada a parametros_legales.")
    else:
        print("La columna ya existia, no se hizo nada.")
