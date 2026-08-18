"""Migracion de esquema (Sprint 47): agrega las columnas necesarias para el
recalculo historico de liquidaciones afectadas por las correcciones del
Sprint 30 (fecha_interrupcion_efectiva fecha-a-fecha real, conteo inclusivo
de dias de prestaciones sociales sobre base comercial 360). Idempotente --
verifica con PRAGMA table_info antes de alterar, mismo patron exacto que
scripts/migrate_es_smmlv_laboral.py (Sprint 44).

Columnas agregadas:
- expedientes.estado_procesal (TEXT, default 'EN_TRAMITE'): ver docstring de
  EstadoProcesal en database/models.py -- no existia ningun campo de estado
  procesal antes de este sprint, default conservador EN_TRAMITE para no
  omitir por silencio el recalculo obligatorio que exige el despacho. Debe
  revisarse manualmente expediente por expediente antes de correr
  scripts/recalcular_historicas_sprint30.py en produccion, sobre todo para
  marcar los que ya estan en cosa juzgada.
- audit_logs.obsoleto_requiere_recalculo (BOOLEAN, default 0)
- audit_logs.liquidacion_anterior_id (INTEGER, nullable, sin FK -- mismo
  motivo que obligacion_padre_id/liquidacion_anterior_id en
  database/models.py: SQLite no permite DROP COLUMN sobre una columna con FK)
- audit_logs.motivo_recalculo (TEXT, nullable)

No hace falta migracion para ninguna tabla nueva -- este sprint no crea
tablas, solo columnas sobre expedientes/audit_logs (ambas ya existentes)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega las 4 columnas si no existen. Retorna True si aplico algun
    ALTER TABLE, False si todas las columnas ya existian."""
    con = sqlite3.connect(db_path)
    try:
        aplico_algo = False

        columnas_expedientes = {
            fila[1] for fila in con.execute("PRAGMA table_info(expedientes)")
        }
        if "estado_procesal" not in columnas_expedientes:
            con.execute(
                "ALTER TABLE expedientes ADD COLUMN estado_procesal "
                "TEXT NOT NULL DEFAULT 'EN_TRAMITE'"
            )
            aplico_algo = True

        columnas_audit_logs = {
            fila[1] for fila in con.execute("PRAGMA table_info(audit_logs)")
        }
        if "obsoleto_requiere_recalculo" not in columnas_audit_logs:
            con.execute(
                "ALTER TABLE audit_logs ADD COLUMN obsoleto_requiere_recalculo "
                "BOOLEAN NOT NULL DEFAULT 0"
            )
            aplico_algo = True
        if "liquidacion_anterior_id" not in columnas_audit_logs:
            con.execute(
                "ALTER TABLE audit_logs ADD COLUMN liquidacion_anterior_id INTEGER"
            )
            aplico_algo = True
        if "motivo_recalculo" not in columnas_audit_logs:
            con.execute("ALTER TABLE audit_logs ADD COLUMN motivo_recalculo TEXT")
            aplico_algo = True

        con.commit()
        return aplico_algo
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas del Sprint 47 (recalculo historico) agregadas.")
    else:
        print("Las columnas ya existian, no se hizo nada.")
