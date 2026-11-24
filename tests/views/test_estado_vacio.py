"""Sprint 128: estados vacios con la mascota de BASTIUM."""

from datetime import date

import database.session as session_module
from app.views.dashboard import DashboardView
from app.views.estado_vacio import EstadoVacio
from app.views.expedientes import ExpedientesListView
from database.models import AreaDerecho, Expediente


def test_estado_vacio_muestra_la_mascota_y_el_mensaje(qtbot):
    estado = EstadoVacio("No hay nada todavía.")
    qtbot.addWidget(estado)

    assert not estado.etiqueta_mascota.pixmap().isNull()
    assert estado.mensaje() == "No hay nada todavía."

    estado.set_mensaje("Otro mensaje")
    assert estado.etiqueta_mensaje.text() == "Otro mensaje"


def test_inicio_sin_datos_muestra_la_mascota_en_vez_de_tablas_vacias(qtbot):
    view = DashboardView()
    qtbot.addWidget(view)

    assert view.tabla_alertas.isHidden()
    assert not view.estado_vacio_alertas.isHidden()
    assert "90 días" in view.estado_vacio_alertas.mensaje()
    assert view.tabla_actividad.isHidden()
    assert not view.estado_vacio_actividad.isHidden()


def test_inicio_con_actividad_muestra_la_tabla_y_oculta_la_mascota(qtbot):
    from datetime import datetime

    from database.models import AuditLog

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-900",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        AuditLog(
            expediente_id=expediente.id,
            usuario="abogado",
            fecha_ejecucion=datetime(2026, 6, 1, 10, 0),
            fecha_corte=date(2026, 6, 1),
            area_derecho="CIVIL_FAMILIA",
            resultado_json="{}",
        )
    )
    session.commit()
    session.close()

    view = DashboardView()
    qtbot.addWidget(view)

    assert not view.tabla_actividad.isHidden()
    assert view.estado_vacio_actividad.isHidden()


def test_listado_de_expedientes_vacio_lleva_la_mascota(qtbot):
    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert not view.widget_estado_vacio.isHidden()
    assert not view.etiqueta_mascota_estado_vacio.pixmap().isNull()
