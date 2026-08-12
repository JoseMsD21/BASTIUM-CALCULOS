"""Migracion de esquema + datos (Sprint 57): agrega las columnas
areas_derecho/unidad a parametros_legales y completa las filas existentes
(683 al momento de este sprint) segun la tabla clave -> (areas, unidad) de
`app.services.areas_parametro.AREA_UNIDAD_POR_CLAVE` (copiada tal cual de la
spec 2026-08-11-parametros-ux-dialogos-crud-design.md, seccion Sprint 57 --
NO se repite aqui, ver ese modulo).

Idempotente -- verifica con PRAGMA table_info antes de alterar el esquema, y
solo completa filas donde areas_derecho/unidad todavia esten sin asignar
(NULL o '').

A diferencia de otras migraciones de este proyecto que agregan una columna
con un unico valor por defecto (ej. es_smmlv BOOLEAN NOT NULL DEFAULT 0), aqui
el valor correcto varia por clave -- no hay un DEFAULT unico valido para el
ALTER TABLE. Las columnas se agregan sin NOT NULL/DEFAULT (nullable a nivel
SQLite, mismo criterio que database/models.py::ParametroLegal) y esta misma
migracion completa cada fila con un UPDATE dirigido por clave. Debe correr
DESPUES de scripts/migrate_parametros_legales.py en
aplicar_migraciones_pendientes() (database/database.py): en una bastium.db
nueva, las 683 filas recien sembradas por ese script todavia no tienen
areas_derecho/unidad -- si esta migracion corriera antes, esa siembra
quedaria sin completar hasta el siguiente arranque de la app (idempotente,
pero no en la misma pasada)."""

import sqlite3
from pathlib import Path

from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, serializar_areas

DB_PATH = Path(__file__).resolve().parent.parent / "bastium.db"


def migrar(db_path: Path = DB_PATH) -> bool:
    """Agrega areas_derecho/unidad a parametros_legales si faltan, y completa
    con AREA_UNIDAD_POR_CLAVE cualquier fila que todavia no las tenga
    asignadas. Retorna True si aplico algun cambio (ALTER TABLE y/o UPDATE),
    False si no hizo falta nada."""
    con = sqlite3.connect(db_path)
    try:
        columnas = {fila[1] for fila in con.execute("PRAGMA table_info(parametros_legales)")}
        aplico = False
        if "areas_derecho" not in columnas:
            con.execute("ALTER TABLE parametros_legales ADD COLUMN areas_derecho VARCHAR(200)")
            aplico = True
        if "unidad" not in columnas:
            con.execute("ALTER TABLE parametros_legales ADD COLUMN unidad VARCHAR(30)")
            aplico = True

        for clave, (areas, unidad) in AREA_UNIDAD_POR_CLAVE.items():
            areas_json = serializar_areas(areas)
            cursor = con.execute(
                "UPDATE parametros_legales SET areas_derecho = ?, unidad = ? "
                "WHERE clave = ? "
                "AND (areas_derecho IS NULL OR areas_derecho = '' "
                "OR unidad IS NULL OR unidad = '')",
                (areas_json, unidad, clave),
            )
            if cursor.rowcount:
                aplico = True

        con.commit()
        return aplico
    finally:
        con.close()


if __name__ == "__main__":
    if migrar():
        print("Columnas areas_derecho/unidad agregadas/completadas en parametros_legales.")
    else:
        print("parametros_legales ya tenia areas_derecho/unidad completos, no se hizo nada.")
