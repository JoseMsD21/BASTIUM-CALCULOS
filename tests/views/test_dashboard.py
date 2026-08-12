from datetime import date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.result import LiquidationResult
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


def test_dashboard_muestra_liquidaciones_recientes_de_todos_los_expedientes(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = _crear_expediente(session, "2026-020", AreaDerecho.CIVIL_FAMILIA)
    registrar_liquidacion(
        session,
        expediente_id=expediente.id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 1, 1),
        resultado=LiquidationResult(items=[]),
        fecha_ejecucion=datetime(2026, 1, 2, 10, 0),
    )
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.tabla_actividad.rowCount() == 1
    assert view.tabla_actividad.item(0, 1).text() == "2026-020"
    assert view.tabla_actividad.item(0, 2).text() == "CIVIL_FAMILIA"


def test_dashboard_actividad_reciente_ordena_recientes_primero_y_recorta_a_10(
    qtbot, monkeypatch
):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = _crear_expediente(session, "2026-021", AreaDerecho.CIVIL_FAMILIA)
    for dia in range(1, 13):
        registrar_liquidacion(
            session,
            expediente_id=expediente.id,
            area_derecho="CIVIL_FAMILIA",
            fecha_corte=date(2026, 1, 1),
            resultado=LiquidationResult(items=[]),
            fecha_ejecucion=datetime(2026, 1, dia, 10, 0),
        )
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert view.tabla_actividad.rowCount() == 10
    assert view.tabla_actividad.item(0, 0).text() == "2026-01-12 10:00"
    assert view.tabla_actividad.item(9, 0).text() == "2026-01-03 10:00"


# --- Sprint 50 (Tarea 3): grafica de expedientes por area ------------------


def test_dashboard_grafica_se_puebla_con_expedientes_por_area(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _crear_expediente(session, "2026-030", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-031", AreaDerecho.CIVIL_FAMILIA)
    _crear_expediente(session, "2026-032", AreaDerecho.COMERCIAL)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    etiquetas_esperadas = [etiqueta for _codigo, etiqueta, _habilitada in AREAS_DERECHO]
    conteos_esperados = [
        2 if etiqueta == "Civil / Familia" else 1 if etiqueta == "Comercial" else 0
        for etiqueta in etiquetas_esperadas
    ]

    ejes = view.figura_por_area.axes[0]
    barras = ejes.containers[0]
    assert [etiqueta.get_text() for etiqueta in ejes.get_xticklabels()] == etiquetas_esperadas
    assert [barra.get_height() for barra in barras] == conteos_esperados


def test_dashboard_grafica_se_actualiza_al_refrescar_con_datos_nuevos(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _crear_expediente(session, "2026-033", AreaDerecho.LABORAL)
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    ejes = view.figura_por_area.axes[0]
    barras_antes = [barra.get_height() for barra in ejes.containers[0]]
    assert sum(barras_antes) == 1

    session = session_module.get_session()
    _crear_expediente(session, "2026-034", AreaDerecho.LABORAL)
    session.close()
    view.refrescar()

    ejes = view.figura_por_area.axes[0]
    barras_despues = [barra.get_height() for barra in ejes.containers[0]]
    assert sum(barras_despues) == 2


def test_dashboard_grafica_usa_colores_de_la_paleta_de_marca(qtbot, monkeypatch):
    from app.core import theme_colors

    _sesion_en_memoria(monkeypatch)
    view = DashboardView()
    qtbot.addWidget(view)

    ejes = view.figura_por_area.axes[0]
    barras = ejes.containers[0]
    color_barra = barras[0].get_facecolor()
    color_esperado = _hex_a_rgba_matplotlib(theme_colors.PRIMARIO)
    assert color_barra == color_esperado


def _hex_a_rgba_matplotlib(hex_color: str) -> tuple:
    from matplotlib.colors import to_rgba

    return to_rgba(hex_color)


# --- Sprint 55: 3 bugs de UI en el Dashboard --------------------------------


def test_dashboard_tablas_no_son_editables(qtbot, monkeypatch):
    """Hallazgo 3: doble clic en una celda de cualquiera de las 3 tablas del
    Dashboard entraba en modo edicion sin persistir el cambio en ningun lado --
    solo confunde. Mismo patron que ya usan configuracion.py y
    expediente_detalle.py (NoEditTriggers)."""
    from PySide6.QtWidgets import QAbstractItemView

    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)

    for tabla in (view.tabla_por_area, view.tabla_alertas, view.tabla_actividad):
        assert tabla.editTriggers() == QAbstractItemView.EditTrigger.NoEditTriggers


def test_dashboard_resize_reajusta_el_layout_de_la_grafica_sin_recalcular_datos(
    qtbot, monkeypatch
):
    """Hallazgo 2: _refrescar_grafica_por_area() solo llamaba tight_layout() una
    vez, al refrescar datos -- sin un manejador de resize, las etiquetas de la
    grafica de barras quedaban apretadas/superpuestas al redimensionar la
    ventana. No hay un patron establecido en el repo para testear layout de
    matplotlib embebido pixel a pixel, asi que este test verifica lo que si es
    observable y determinista: que redimensionar el canvas dispara un nuevo
    tight_layout()+draw_idle() sobre la figura YA dibujada, sin volver a
    consultar la base de datos (no debe llamarse a refrescar())."""
    _sesion_en_memoria(monkeypatch)

    view = DashboardView()
    qtbot.addWidget(view)
    view.show()
    qtbot.waitExposed(view)

    llamadas_refrescar = []
    monkeypatch.setattr(view, "refrescar", lambda *a, **k: llamadas_refrescar.append(1))

    llamadas_tight_layout = []
    tight_layout_original = view.figura_por_area.tight_layout

    def tight_layout_contado(*args, **kwargs):
        llamadas_tight_layout.append(1)
        return tight_layout_original(*args, **kwargs)

    monkeypatch.setattr(view.figura_por_area, "tight_layout", tight_layout_contado)

    view.resize(900, 700)
    qtbot.wait(50)

    assert llamadas_tight_layout, "redimensionar debe volver a acomodar el layout de la figura"
    assert llamadas_refrescar == [], "el resize no debe volver a consultar datos"


# --- Sprint 53: patron N+1 de consultas en el Dashboard --------------------


def test_dashboard_refrescar_no_abre_una_sesion_por_obligacion_con_fechas_origen_distintas(
    qtbot, monkeypatch
):
    """Caso realista y el que exige la Definicion de Hecho del Sprint 53: las
    obligaciones NO suelen compartir `fecha_origen`. La cache de
    `cache_de_liquidacion()` sola solo colapsa `get_parametro` cuando la
    (clave, fecha) es EXACTAMENTE igual entre dos llamadas -- con 8
    fechas_origen distintas, sin `precargar_parametro` (Sprint 53,
    app/services/parametro_service.py) cada fecha distinta seguiria abriendo
    su propia sesion SQLAlchemy (`_resolver_fila`), reproduciendo el patron
    N+1 aun con la cache activa. `precargar_parametro` trae TODAS las filas
    de PRESCRIPCION_EJECUTIVA_MESES en una sola consulta y deja que
    `get_parametro` resuelva cualquier fecha en memoria contra ellas."""
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    fechas_origen = [date(2021, 1, 1) + timedelta(days=indice) for indice in range(8)]
    for indice, fecha_origen in enumerate(fechas_origen):
        expediente = _crear_expediente(session, f"2026-11{indice}", AreaDerecho.CIVIL_FAMILIA)
        _crear_obligacion(session, expediente.id, fecha_origen)
    session.close()

    fecha_limite_referencia = calcular_prescripcion(fechas_origen[0], TipoAccion.EJECUTIVA)
    hoy = fecha_limite_referencia - timedelta(days=30)

    view = DashboardView()
    qtbot.addWidget(view)

    llamadas_get_session: list[None] = []
    get_session_original = session_module.get_session

    def get_session_contada():
        llamadas_get_session.append(None)
        return get_session_original()

    monkeypatch.setattr(session_module, "get_session", get_session_contada)

    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 8
    # 1 sesion para leer los expedientes (refrescar()) + 1 sesion para
    # precargar TODAS las filas de PRESCRIPCION_EJECUTIVA_MESES de una vez
    # (precargar_parametro) -- nunca 8 (una por fecha_origen distinta).
    assert len(llamadas_get_session) == 2


def test_dashboard_refrescar_no_abre_una_sesion_por_obligacion_con_la_misma_fecha_origen(
    qtbot, monkeypatch
):
    """Caso adicional: cuando varias obligaciones SI comparten exactamente la
    misma fecha_origen (ej. una carga en lote del mismo pagare), tanto la
    cache por (clave, fecha) de cache_de_liquidacion como la precarga de
    precargar_parametro evitan abrir una sesion por obligacion."""
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    _sembrar_parametro_prescripcion_ejecutiva(session)
    for indice in range(8):
        expediente = _crear_expediente(session, f"2026-10{indice}", AreaDerecho.CIVIL_FAMILIA)
        _crear_obligacion(session, expediente.id, date(2021, 1, 4))
    session.close()

    fecha_limite = calcular_prescripcion(date(2021, 1, 4), TipoAccion.EJECUTIVA)
    hoy = fecha_limite - timedelta(days=30)

    view = DashboardView()
    qtbot.addWidget(view)

    llamadas_get_session: list[None] = []
    get_session_original = session_module.get_session

    def get_session_contada():
        llamadas_get_session.append(None)
        return get_session_original()

    monkeypatch.setattr(session_module, "get_session", get_session_contada)

    view.refrescar(hoy=hoy)

    assert view.tabla_alertas.rowCount() == 8
    assert len(llamadas_get_session) == 2
