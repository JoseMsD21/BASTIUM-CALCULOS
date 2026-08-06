from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.dashboard import DashboardView
from database.models import AreaDerecho, Base, Expediente


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
