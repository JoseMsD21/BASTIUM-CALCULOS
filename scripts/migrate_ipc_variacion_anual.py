"""Migracion de datos (Sprint 58): siembra la clave IPC_VARIACION_ANUAL en
parametros_legales -- la tabla CRUDA de variacion porcentual anual del IPC tal
como esta transcrita del PDF del abogado (`_IPC_VARIACION_ANUAL`,
app/engine/indexation/historical_index.py), de la que ya se deriva
IPC_INDICE_ACUMULADO (formula `indice = indice_anterior * (1 +
variacion_anual / 100)`, ver `_construir_indice_ipc_acumulado` en ese mismo
modulo) pero que hasta este sprint nunca se sembraba en la base de datos --
solo el resultado ya calculado. El usuario pidio ver el dato crudo junto al
calculado en HistorialParametroDialog (ver
app/services/parametro_service.py::CLAVE_CRUDA_DE).

Hermano de scripts/migrate_parametros_legales.py (mismo patron: db_path
opcional, ORM, idempotente por clave) en vez de sumarse a
scripts/migrate_parametros_area_unidad.py -- ese script ya tiene una
responsabilidad propia bien acotada (completar areas_derecho/unidad de filas
EXISTENTES via UPDATE) y esta migracion en cambio INSERTA filas nuevas para
una clave que no existia, mismo tipo de operacion que migrate_parametros_legales.py.

IPC_VARIACION_ANUAL nunca participa de ningun calculo de liquidacion -- solo
IPC_INDICE_ACUMULADO se consulta desde get_ipc_for_date()/get_parametro(). Es
puramente informativa para la GUI.

Idempotente: si la clave ya tiene filas, no la vuelve a sembrar."""

import sys
from pathlib import Path

# Garantiza resolucion de 'database.*' y 'app.*' al invocar este archivo
# directamente (python scripts/migrate_ipc_variacion_anual.py) desde la raiz
# del proyecto, sin depender de que el caller use 'python -m'. Mismo patron
# que scripts/migrate_parametros_legales.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.engine.indexation.historical_index import _IPC_VARIACION_ANUAL
from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, serializar_areas
from database.database import init_db
from database.models import Base, ParametroLegal
from database.session import get_session

USUARIO_MIGRACION = "sistema"
MOTIVO_MIGRACION = (
    "Dato crudo migrado automaticamente (Sprint 58): variacion % anual del IPC tal "
    "como esta en el PDF, fuente de la que se deriva IPC_INDICE_ACUMULADO."
)
CLAVE = "IPC_VARIACION_ANUAL"


def migrar(db_path: Path | None = None) -> int:
    """Siembra IPC_VARIACION_ANUAL. Retorna cuantas filas se insertaron (0 si
    la clave ya estaba sembrada).

    Mismo patron db_path opcional que scripts/migrate_parametros_legales.py:
    sin db_path opera sobre el engine global (database.database.engine),
    atado por la fixture de tests _db_en_memoria_por_defecto; con db_path usa
    un engine SQLAlchemy ad hoc apuntando exactamente a esa ruta -- nunca al
    engine global -- para que la siembra quede aislada en la base destino
    (ver docstring de migrar() en migrate_parametros_legales.py para el
    detalle completo de por que ambas ramas son necesarias)."""
    engine_ad_hoc = None
    try:
        if db_path is None:
            init_db()
            session = get_session()
        else:
            engine_ad_hoc = create_engine(f"sqlite:///{db_path}")
            Base.metadata.create_all(engine_ad_hoc)
            session = sessionmaker(bind=engine_ad_hoc, autoflush=False, expire_on_commit=False)()
        return _sembrar(session)
    finally:
        if engine_ad_hoc is not None:
            engine_ad_hoc.dispose()


def _sembrar(session) -> int:
    try:
        ya_sembrada = (
            session.query(ParametroLegal).filter(ParametroLegal.clave == CLAVE).first()
            is not None
        )
        if ya_sembrada:
            return 0

        areas, unidad = AREA_UNIDAD_POR_CLAVE[CLAVE]
        areas_json = serializar_areas(areas)
        for anio, variacion in _IPC_VARIACION_ANUAL.items():
            session.add(
                ParametroLegal(
                    clave=CLAVE,
                    valor=variacion,
                    vigente_desde=date(anio, 1, 1),
                    usuario=USUARIO_MIGRACION,
                    motivo=MOTIVO_MIGRACION,
                    creado_en=datetime.now(),
                    areas_derecho=areas_json,
                    unidad=unidad,
                )
            )
        session.commit()
        return len(_IPC_VARIACION_ANUAL)
    finally:
        session.close()


if __name__ == "__main__":
    n = migrar()
    if n:
        print(f"Se sembraron {n} filas de IPC_VARIACION_ANUAL en parametros_legales.")
    else:
        print("IPC_VARIACION_ANUAL ya estaba sembrada, no se hizo nada.")
