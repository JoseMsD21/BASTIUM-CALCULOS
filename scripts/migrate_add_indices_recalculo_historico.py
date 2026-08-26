"""Migracion de esquema (Sprint 112, hallazgo 4): agrega indices a las
columnas que app/services/recalculo_historico.py
(identificar_liquidaciones_pre_sprint30) usa para filtrar/ordenar, ninguna
con index=True desde que el Sprint 47 las agrego. Esa funcion esta diseñada
para poder re-ejecutarse (idempotente) -- sin indice, cada corrida hace un
full table scan de audit_logs, una tabla que crece una fila por cada
liquidacion que el abogado corre. fecha_ejecucion es la columna principal
(filtro de rango `< cierre` + ORDER BY); obsoleto_requiere_recalculo y
liquidacion_anterior_id son las otras 2 condiciones del mismo WHERE, mas
baratas de indexar de una vez que de omitir. Mismo patron idempotente
(PRAGMA index_list) que scripts/migrate_add_indices_rendimiento.py
(Sprint 25)."""

import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"

_INDICES = [
    ("ix_audit_logs_fecha_ejecucion", "audit_logs", "fecha_ejecucion"),
    ("ix_audit_logs_obsoleto_requiere_recalculo", "audit_logs", "obsoleto_requiere_recalculo"),
    ("ix_audit_logs_liquidacion_anterior_id", "audit_logs", "liquidacion_anterior_id"),
]


def _tabla_existe(con: sqlite3.Connection, tabla: str) -> bool:
    fila = con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
    ).fetchone()
    return fila is not None


def migrar(db_path: Path = DB_PATH) -> bool:
    """Crea los 2 indices si no existen. Retorna True si creo alguno, False
    si ya existian. Si la tabla no existe (snapshot parcial o inusual), se
    omite con un aviso en vez de fallar -- mismo criterio que
    migrate_add_indices_rendimiento.py."""
    con = sqlite3.connect(db_path)
    try:
        aplico = False
        for nombre_indice, tabla, columna in _INDICES:
            if not _tabla_existe(con, tabla):
                print(
                    f"Aviso: la tabla '{tabla}' no existe en {db_path}, "
                    f"se omite el indice {nombre_indice}."
                )
                continue
            indices_existentes = {fila[1] for fila in con.execute(f"PRAGMA index_list({tabla})")}
            if nombre_indice in indices_existentes:
                continue
            con.execute(f"CREATE INDEX {nombre_indice} ON {tabla}({columna})")
            aplico = True
        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print(
            "Indices de recalculo historico agregados (audit_logs.fecha_ejecucion, "
            "audit_logs.obsoleto_requiere_recalculo, audit_logs.liquidacion_anterior_id)."
        )
    else:
        print("Los 3 indices ya existian, no se hizo nada.")
