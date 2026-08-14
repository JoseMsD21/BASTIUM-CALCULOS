import os
from pathlib import Path

from sqlalchemy import create_engine


def _resolve_db_path() -> Path:
    """Ruta del archivo bastium.db. Por defecto vive en la raiz del repo;
    la variable de entorno BASTIUM_DB_PATH permite apuntar a otra ubicacion
    (ej. una base de pruebas manual o una ruta compartida) sin editar
    codigo fuente (Sprint 28, hallazgo 3)."""
    ruta_personalizada = os.environ.get("BASTIUM_DB_PATH")
    if ruta_personalizada:
        return Path(ruta_personalizada)
    return Path(__file__).resolve().parent.parent / "bastium.db"


DB_PATH = _resolve_db_path()
engine = create_engine(f"sqlite:///{DB_PATH}")


def init_db() -> None:
    from database.models import Base

    Base.metadata.create_all(engine)


def aplicar_migraciones_pendientes(db_path: Path | None = None) -> None:
    """Aplica, en orden y de forma idempotente, todas las migraciones de
    esquema/indices/datos que el proyecto acumulo sprint a sprint en
    scripts/migrate_*.py (Sprints 8, 12, 15, 16, 18, 19, 20, 25) mas la
    siembra de parametros_legales.

    `Base.metadata.create_all()` (init_db(), arriba) solo crea tablas que
    todavia no existen -- nunca agrega una columna o un indice a una tabla
    que ya existia con un esquema mas viejo. Sin esta funcion, cualquier
    bastium.db creada antes de que un sprint agregara una columna nueva se
    queda desactualizada para siempre a menos que alguien recuerde correr a
    mano el script de ese sprint -- eso fue exactamente lo que le paso a la
    bastium.db real de este proyecto (le faltaban 5 columnas de los Sprints
    18/19/20 y las 39 filas de parametros_legales del sprint de parametros
    versionados, y `DashboardView` -- la primera pantalla que carga TODAS
    las obligaciones de TODOS los expedientes al arrancar -- fue quien
    primero disparo el error).

    Se llama automaticamente en cada arranque de la app (`main.py`, despues
    de `init_db()`) para que ni un checkout existente desactualizado ni un
    clon nuevo del repositorio necesiten un paso manual: cada script
    individual ya verifica con PRAGMA table_info/index_list antes de
    alterar, asi que correrlos de mas es gratis (una consulta PRAGMA, no un
    ALTER TABLE) tanto en una bastium.db ya al dia como en una recien
    creada."""
    from scripts.migrate_add_indices_rendimiento import migrar as migrar_indices
    from scripts.migrate_anatocismo_comercial import migrar as migrar_anatocismo
    from scripts.migrate_aplica_indexacion_ipc import migrar as migrar_indexacion_ipc
    from scripts.migrate_costas_tipo_proceso import migrar as migrar_costas
    from scripts.migrate_creado_por_sistema import migrar as migrar_creado_por_sistema
    from scripts.migrate_es_smmlv_laboral import migrar as migrar_es_smmlv
    from scripts.migrate_interes_sobre_capital_indexado import (
        migrar as migrar_interes_capital_indexado,
    )
    from scripts.migrate_ipc_variacion_anual import migrar as migrar_ipc_variacion_anual
    from scripts.migrate_moneda_trm import migrar as migrar_moneda_trm
    from scripts.migrate_parametros_area_unidad import migrar as migrar_parametros_area_unidad
    from scripts.migrate_parametros_legales import migrar as migrar_parametros_legales
    from scripts.migrate_reajuste_anual_familia import migrar as migrar_reajuste_anual_familia
    from scripts.migrate_seguridad_social_laboral import migrar as migrar_seguridad_social
    from scripts.migrate_sprint47_recalculo_historico import (
        migrar as migrar_recalculo_historico_sprint47,
    )
    from scripts.migrate_tributario import migrar as migrar_tributario

    ruta = db_path if db_path is not None else _resolve_db_path()

    migrar_indexacion_ipc(ruta)
    migrar_moneda_trm(ruta)
    migrar_seguridad_social(ruta)
    migrar_tributario(ruta)
    migrar_anatocismo(ruta)
    migrar_costas(ruta)
    migrar_interes_capital_indexado(ruta)
    migrar_reajuste_anual_familia(ruta)
    migrar_indices(ruta)
    migrar_es_smmlv(ruta)
    # Se llama ANTES de migrar_parametros_legales/migrar_ipc_variacion_anual
    # (bug real encontrado en produccion, 2026-08-12): ambos scripts hacen
    # `session.query(ParametroLegal)` via el ORM, y el modelo ParametroLegal
    # (database/models.py) ya declara areas_derecho/unidad como columnas
    # mapeadas desde el Sprint 57 -- SQLAlchemy siempre selecciona TODAS las
    # columnas del modelo actual, sin importar que migracion "logica" este
    # corriendo. En una bastium.db real anterior al Sprint 57 (con las 683
    # filas de parametros_legales ya sembradas pero sin estas 2 columnas
    # fisicas todavia), correr migrar_parametros_legales primero lanzaba
    # sqlite3.OperationalError: no such column: parametros_legales.areas_derecho
    # apenas Python arrancaba, porque el ALTER TABLE que agrega esas columnas
    # no habia corrido todavia. Se mantiene ademas la llamada de mas abajo,
    # despues de migrar_parametros_legales, para completar areas_derecho/
    # unidad en las filas que ese script sí llegue a sembrar de nuevo (bastium.db
    # completamente nueva) -- migrar_parametros_area_unidad es idempotente,
    # llamarla dos veces es gratis (Sprint 57/58).
    # migrar_creado_por_sistema debe correr antes que las dos migraciones de
    # siembra por la misma clase de bug descrita arriba: ambos scripts hacen
    # `session.add(ParametroLegal(..., creado_por_sistema=True))` via el ORM,
    # que igual que session.query() siempre incluye TODAS las columnas
    # mapeadas del modelo actual -- en una bastium.db que todavia no tiene la
    # columna fisica creado_por_sistema, sembrar antes de esta migracion
    # lanzaria sqlite3.OperationalError: no such column: parametros_legales.creado_por_sistema.
    migrar_creado_por_sistema(ruta)
    migrar_parametros_area_unidad(ruta)
    migrar_parametros_legales(ruta)
    # Debe correr DESPUES de migrar_parametros_legales tambien: en una bastium.db
    # nueva, las filas que ese script acaba de sembrar todavia no tienen
    # areas_derecho/unidad -- si esta migracion corriera antes, quedarian sin
    # completar hasta el siguiente arranque (Sprint 57).
    migrar_parametros_area_unidad(ruta)
    # Orden narrativo (Sprint 58 despues de Sprint 57) -- no hay dependencia
    # real de datos: migrar_ipc_variacion_anual siembra sus propias filas ya
    # con areas_derecho/unidad completos (lee AREA_UNIDAD_POR_CLAVE
    # directamente), asi que correria igual de bien antes o despues de
    # migrar_parametros_area_unidad.
    migrar_ipc_variacion_anual(ruta)
    # Sprint 47: agrega expedientes.estado_procesal y las 3 columnas de
    # recalculo historico en audit_logs -- sin dependencia de orden con las
    # migraciones de arriba (columnas nuevas en tablas ya existentes, no
    # siembra de datos via ORM).
    migrar_recalculo_historico_sprint47(ruta)
