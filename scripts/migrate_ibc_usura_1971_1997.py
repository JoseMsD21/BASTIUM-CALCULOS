"""Migracion de datos (Sprint 81): extiende las claves IBC_CONSUMO_ORDINARIO y
USURA_CONSUMO_ORDINARIO en parametros_legales con los tramos de
_TRAMOS_IBC_USURA (app/engine/indexation/historical_index.py) anteriores a
1997-07-01 -- rango 1971-10-29 a 1997-06-30, transcrito de la certificacion
historica de la Superfinanciera (docs/Archivos de referencia abogado/
_markdown/Historicocertificacionsuperfinancieratasasdeinteres.md).

Decision de mapeo de columnas (ya tomada, ver Sprint 81 en Pendientes.md --
no se reabre aqui): antes de 1997 la fuente trae 3 columnas de interes anual
efectivo distintas ("CORRIENTE" / "BANCARIO CORRIENTE" / "CREDITOS
ORDINARIOS LIBRE ASIGNACION", con celdas "----" cuando esa columna no aplica
a la resolucion de esa fila). Se usa "BANCARIO CORRIENTE" como fuente de
ibc_anual por continuidad conceptual con el Art. 884 C.Co. -- el mismo
criterio que ya usa la linea "Consumo y Ordinario" desde 1997 en adelante
(ver docstring de _TRAMOS_IBC_USURA). La tabla pre-1997 no trae una columna
de usura separada: usura_anual se calcula como ibc_anual * 1.5 (Decimal,
redondeado a 2 decimales con ROUND_HALF_UP), el mismo multiplicador legal
verificado en las 263 filas ya existentes desde 1997 (invariante de la ley,
no una aproximacion nueva de esta migracion).

Por que hace falta un script NUEVO y no basta con editar _TRAMOS_IBC_USURA:
scripts/migrate_parametros_legales.py es idempotente POR CLAVE completa (si
la clave ya tiene alguna fila, salta la clave entera y no vuelve a leer
_TRAMOS_IBC_USURA). En una bastium.db real, esas dos claves ya tienen filas
sembradas desde 1997 (el sprint de parametros legales versionados), asi que
ese script SIEMPRE las salta enteras desde entonces -- nunca vera los ~50
tramos pre-1997 nuevos que este sprint agrego a la lista en Python, sin
importar cuantas veces se reinvoque. Solo editar el dict/lista de Python no
tiene ningun efecto en el comportamiento real de la app para una base de
datos ya migrada (get_ibc_usura_for_date() lee parametros_legales via
get_parametro(), nunca _TRAMOS_IBC_USURA directamente).

Idempotencia de ESTA migracion: como la clave ya tiene filas desde 1997 (no
esta vacia), el chequeo no puede ser "la clave ya tiene alguna fila" (siempre
seria cierto y nunca sembraria nada, el mismo problema que motiva este
script). En su lugar se verifica "ya existe una fila de esta clave con
vigente_desde anterior a 1997-07-01" -- si es asi, el rango pre-1997 ya fue
sembrado (por esta misma migracion en una corrida anterior, o porque
migrate_parametros_legales.migrar() alcanzo a sembrar la clave completa desde
cero en una bastium.db nueva, ej. en tests) y no se hace nada. No existia un
patron de "extender una clave ya parcialmente sembrada" en otro script de
scripts/ (se busco con grep antes de escribir este) -- este es el primero.

Mismo patron que scripts/migrate_ipc_variacion_anual.py: db_path opcional,
ORM via SQLAlchemy, creado_por_sistema=True, AREA_UNIDAD_POR_CLAVE/
serializar_areas de app.services.areas_parametro para areas_derecho/unidad.

ADVERTENCIA -- NO invocar este script suelto (`python
scripts/migrate_ibc_usura_1971_1997.py`) fuera de
database.database.aplicar_migraciones_pendientes() en una bastium.db nueva
(sin filas todavia para estas dos claves): si corre ANTES que
scripts/migrate_parametros_legales.py, sembraria solo los ~50 tramos
pre-1997, dejando la clave "parcialmente sembrada" con un patron de fechas
que scripts/migrate_parametros_legales.py YA NO reconoce como "vacia" (su
chequeo es "la clave tiene alguna fila") -- ese script saltaria la clave
ENTERA en su siguiente corrida y los tramos 1997+ nunca se sembrarian, sin
que ningun otro script lo detecte o corrija despues. Por eso `migrar()`
(abajo) se niega a sembrar si la clave esta completamente vacia -- ver
`_clave_lista_para_extender`. El orden correcto (migrar_parametros_legales
antes que migrar_ibc_usura_1971_1997) ya esta garantizado en
aplicar_migraciones_pendientes(); usar ese entrypoint, no este archivo
directamente."""

import sys
from pathlib import Path

# Garantiza resolucion de 'database.*' y 'app.*' al invocar este archivo
# directamente (python scripts/migrate_ibc_usura_1971_1997.py) desde la raiz
# del proyecto, sin depender de que el caller use 'python -m'. Mismo patron
# que scripts/migrate_parametros_legales.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.engine.indexation.historical_index import _TRAMOS_IBC_USURA
from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE, serializar_areas
from database.database import init_db
from database.models import Base, ParametroLegal
from database.session import get_session

USUARIO_MIGRACION = "sistema"
MOTIVO_MIGRACION = (
    "Dato migrado automaticamente (Sprint 81): extension de IBC_CONSUMO_ORDINARIO/"
    "USURA_CONSUMO_ORDINARIO con los tramos anteriores a 1997-07-01 de la "
    "certificacion historica de la Superfinanciera (columna 'Bancario corriente'; "
    "usura = ibc x 1.5, mismo criterio que las filas ya sembradas desde 1997)."
)

_LIMITE_1997 = date(1997, 7, 1)

_TRAMOS_PRE_1997 = [tramo for tramo in _TRAMOS_IBC_USURA if tramo.fin < _LIMITE_1997]


def _clave_ya_extendida(session, clave: str) -> bool:
    """True si ya existe una fila de `clave` con vigente_desde anterior a
    1997-07-01 -- es decir, si el rango pre-1997 ya fue sembrado (por esta
    misma migracion antes, o porque la clave se sembro entera desde cero).
    No se puede usar "la clave ya tiene alguna fila" como chequeo de
    idempotencia: esa clave YA tiene filas desde 1997 en cualquier bastium.db
    real, y ese chequeo nunca sembraria nada (ver docstring del modulo)."""
    return (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == clave, ParametroLegal.vigente_desde < _LIMITE_1997)
        .first()
        is not None
    )


def _clave_completamente_vacia(session, clave: str) -> bool:
    """True si `clave` no tiene NINGUNA fila todavia (ni siquiera las 1997+).
    Distingue el escenario real (clave con filas 1997+ sembradas por
    scripts/migrate_parametros_legales.py en un sprint anterior, a la que
    este script le agrega las pre-1997 que le faltan) del escenario del
    footgun documentado en el docstring del modulo (este script invocado
    suelto sobre una bastium.db nueva, ANTES de
    scripts/migrate_parametros_legales.py)."""
    return session.query(ParametroLegal).filter(ParametroLegal.clave == clave).first() is None


def _clave_lista_para_extender(session, clave: str) -> bool:
    """True solo si `clave` ya tiene filas (1997+, sembradas por otro script)
    Y todavia no tiene el rango pre-1997 -- el unico caso en el que este
    script debe sembrar. Si la clave esta completamente vacia, se abstiene
    (guarda contra el footgun de invocacion manual fuera de orden -- ver
    docstring del modulo) y deja que scripts/migrate_parametros_legales.py
    (via aplicar_migraciones_pendientes(), que ya respeta el orden correcto)
    siembre la clave completa, tramos pre-1997 incluidos."""
    if _clave_completamente_vacia(session, clave):
        return False
    return not _clave_ya_extendida(session, clave)


def migrar(db_path: Path | None = None) -> int:
    """Siembra los tramos pre-1997 de IBC_CONSUMO_ORDINARIO/
    USURA_CONSUMO_ORDINARIO. Retorna cuantas filas se insertaron (0 si el
    rango pre-1997 ya estaba sembrado en ambas claves, O si alguna de las dos
    claves esta completamente vacia todavia -- guarda contra invocar este
    script suelto, fuera de orden, sobre una bastium.db nueva; ver ADVERTENCIA
    en el docstring del modulo y `_clave_lista_para_extender`).

    Mismo patron db_path opcional que scripts/migrate_parametros_legales.py:
    sin db_path opera sobre el engine global (database.database.engine),
    atado por la fixture de tests _db_en_memoria_por_defecto; con db_path usa
    un engine SQLAlchemy ad hoc apuntando exactamente a esa ruta -- nunca al
    engine global -- para que la siembra quede aislada en la base destino."""
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
    sembradas = 0
    try:
        if _clave_lista_para_extender(session, "IBC_CONSUMO_ORDINARIO"):
            areas, unidad = AREA_UNIDAD_POR_CLAVE["IBC_CONSUMO_ORDINARIO"]
            areas_json = serializar_areas(areas)
            for tramo in _TRAMOS_PRE_1997:
                session.add(
                    ParametroLegal(
                        clave="IBC_CONSUMO_ORDINARIO",
                        valor=tramo.ibc_anual,
                        vigente_desde=tramo.inicio,
                        vigente_hasta=tramo.fin,
                        usuario=USUARIO_MIGRACION,
                        motivo=MOTIVO_MIGRACION,
                        creado_en=datetime.now(),
                        areas_derecho=areas_json,
                        unidad=unidad,
                        creado_por_sistema=True,
                    )
                )
            sembradas += len(_TRAMOS_PRE_1997)

        if _clave_lista_para_extender(session, "USURA_CONSUMO_ORDINARIO"):
            areas, unidad = AREA_UNIDAD_POR_CLAVE["USURA_CONSUMO_ORDINARIO"]
            areas_json = serializar_areas(areas)
            for tramo in _TRAMOS_PRE_1997:
                session.add(
                    ParametroLegal(
                        clave="USURA_CONSUMO_ORDINARIO",
                        valor=tramo.usura_anual,
                        vigente_desde=tramo.inicio,
                        vigente_hasta=tramo.fin,
                        usuario=USUARIO_MIGRACION,
                        motivo=MOTIVO_MIGRACION,
                        creado_en=datetime.now(),
                        areas_derecho=areas_json,
                        unidad=unidad,
                        creado_por_sistema=True,
                    )
                )
            sembradas += len(_TRAMOS_PRE_1997)

        session.commit()
        return sembradas
    finally:
        session.close()


if __name__ == "__main__":
    n = migrar()
    if n:
        print(
            f"Se sembraron {n} filas pre-1997 de IBC/USURA_CONSUMO_ORDINARIO "
            "en parametros_legales."
        )
    else:
        print(
            "El rango pre-1997 de IBC/USURA_CONSUMO_ORDINARIO ya estaba sembrado, no se hizo nada."
        )
