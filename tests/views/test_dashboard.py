from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from app.views.dashboard import DashboardView
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )


def _crear_expediente(session, radicado: str, area: AreaDerecho) -> Expediente:
    expediente = Expediente(
        radicado=radicado,
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    return expediente


def _sembrar_parametro_prescripcion_ejecutiva(session, meses: int = 60) -> None:
    session.add(
        ParametroLegal(
            clave="PRESCRIPCION_EJECUTIVA_MESES",
            valor=Decimal(meses),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.commit()


def _crear_obligacion(
    session, expediente_id: int, fecha_origen: date, pagada: bool = False
) -> Obligacion:
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=fecha_origen,
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        pagada=pagada,
    )
    session.add(obligacion)
    session.commit()
    return obligacion


def test_dashboard_sin_expedientes_muestra_conteo_en_cero(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 0"
    assert view.tabla_por_area.rowCount() == len(AREAS_DERECHO)
    for fila in range(view.tabla_por_area.rowCount()):
        assert view.tabla_por_area.item(fila, 1).text() == "0"


def test_dashboard_muestra_el_total_y_el_conteo_por_area(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _crear_expediente(session, "2026-001", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-002", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-003", AreaDerecho.COMERCIAL)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.etiqueta_total_expedientes.text() == "Total de expedientes: 3"

    fila_civil = next(
        fila
        for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO)
        if codigo == "CIVIL_FAMILIA"
    )
    fila_comercial = next(
        fila for fila, (codigo, _et, _hab) in enumerate(AREAS_DERECHO) if codigo == "COMERCIAL"
    )
    assert view.tabla_por_area.item(fila_civil, 1).text() == "2"
    assert view.tabla_por_area.item(fila_comercial, 1).text() == "1"


def test_dashboard_boton_ver_expedientes_invoca_callback(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    llamadas = []

    view = DashboardView(on_ver_expedientes=lambda: llamadas.append(1))
    qtbot.addWidget(view)

    view.boton_ver_expedientes.click()

    assert llamadas == [1]


def test_dashboard_boton_ver_expedientes_tiene_clase_primary(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.boton_ver_expedientes.property("class") == "primary"


def test_dashboard_muestra_alerta_de_obligacion_proxima_a_prescribir(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-010", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 0).text() == "2026-010"
    assert view.tabla_alertas.item(0, 1).text() == "Capital pagare"
    assert view.tabla_alertas.item(0, 2).text() == fecha_limite.isoformat()
    assert view.tabla_alertas.item(0, 3).text() == "Vence en 30 días"


def test_dashboard_marca_vencido_cuando_la_fecha_limite_ya_paso(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-011", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite + timedelta(days=10)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 1
    assert view.tabla_alertas.item(0, 3).text() == "Vencido"


def test_dashboard_no_alerta_obligacion_pagada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-012", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4), pagada=True)

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_no_alerta_fuera_de_la_ventana_de_90_dias(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-013", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=200)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_omite_obligacion_sin_parametro_configurado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    # deliberadamente no se siembra PRESCRIPCION_EJECUTIVA_MESES
    expediente = _crear_expediente(session, "2026-014", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)
    view.refrescar(hoy=date(2026, 1, 1))  # no debe lanzar ParametroNoDisponibleError

    assert view.tabla_alertas.rowCount() == 0


def test_dashboard_doble_clic_en_alerta_abre_el_expediente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    expediente = _crear_expediente(session, "2026-015", AreaDerecho.CIVIL_FAMILIA)
    _crear_obligacion(session, expediente.id, date(2021, 1, 4))
    expediente_id = expediente.id

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)
    session.close()

    abiertos = []
    view = DashboardView(on_expediente_abierto=lambda id_: abiertos.append(id_))
    qtbot.addWidget(view)
    view.refrescar(hoy=hoy)

    view.tabla_alertas.cellDoubleClicked.emit(0, 0)

    assert abiertos == [expediente_id]
