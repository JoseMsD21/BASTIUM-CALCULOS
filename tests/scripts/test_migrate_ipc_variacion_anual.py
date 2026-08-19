from datetime import date
from decimal import Decimal

import database.session as session_module
from app.engine.indexation.historical_index import _IPC_VARIACION_ANUAL
from database.models import ParametroLegal


def test_migrar_siembra_una_fila_por_anio_con_el_valor_crudo_correcto():
    from scripts.migrate_ipc_variacion_anual import migrar

    migrar()
    session = session_module.get_session()
    filas = {
        fila.vigente_desde.year: fila.valor
        for fila in session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IPC_VARIACION_ANUAL")
        .all()
    }
    session.close()

    assert len(filas) == len(_IPC_VARIACION_ANUAL)
    for anio, variacion_esperada in _IPC_VARIACION_ANUAL.items():
        assert filas[anio] == variacion_esperada


def test_migrar_valor_2025_coincide_con_historical_index():
    from scripts.migrate_ipc_variacion_anual import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(
            ParametroLegal.clave == "IPC_VARIACION_ANUAL",
            ParametroLegal.vigente_desde == date(2025, 1, 1),
        )
        .one()
    )
    session.close()
    assert fila.valor == Decimal("5.10")


def test_migrar_es_idempotente():
    from scripts.migrate_ipc_variacion_anual import migrar

    primera = migrar()
    segunda = migrar()

    assert primera == len(_IPC_VARIACION_ANUAL)
    assert segunda == 0


def test_migrar_areas_y_unidad_coinciden_con_ipc_indice_acumulado():
    """IPC_VARIACION_ANUAL comparte areas/unidad con IPC_INDICE_ACUMULADO --
    es su dato crudo (ver CLAVE_CRUDA_DE en parametro_service.py)."""
    from app.services.areas_parametro import deserializar_areas
    from scripts.migrate_ipc_variacion_anual import migrar

    migrar()
    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal).filter(ParametroLegal.clave == "IPC_VARIACION_ANUAL").first()
    )
    session.close()

    assert fila is not None
    assert fila.unidad == "%"
    from database.models import AreaDerecho

    # Sprint 43: IPC_INDICE_ACUMULADO/IPC_VARIACION_ANUAL ahora alimentan las 6
    # areas (indexacion IPC en Comercial/Laboral/Sancionatorio/Honorarios, ademas de
    # Civil/Familia y Tributario que ya la usaban) -- ver
    # app/services/areas_parametro.py, AREA_UNIDAD_POR_CLAVE.
    assert deserializar_areas(fila.areas_derecho) == [
        AreaDerecho.CIVIL_FAMILIA,
        AreaDerecho.COMERCIAL,
        AreaDerecho.LABORAL,
        AreaDerecho.SANCIONATORIO,
        AreaDerecho.HONORARIOS,
        AreaDerecho.TRIBUTARIO,
    ]
