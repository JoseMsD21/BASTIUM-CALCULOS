from datetime import date

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente
from app.views.expedientes import ExpedientesListView, ExpedienteFormDialog


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))


def test_lista_muestra_expedientes_existentes(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-001",
            demandante="Ana",
            demandado="Luis",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-001"


def test_dialogo_crea_expediente_civil_familia(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-002")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    expediente_id = dialog.guardar()

    session = session_module.get_session()
    guardado = session.get(Expediente, expediente_id)
    assert guardado.radicado == "2026-002"
    assert guardado.area_derecho == AreaDerecho.CIVIL_FAMILIA
    session.close()


def test_dialogo_deshabilita_areas_no_implementadas(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    modelo = dialog.combo_area.model()
    # Indice 0 = Civil/Familia (habilitada), indice 1 = Comercial (habilitada
    # desde Sprint 2), indice 2 = Laboral (todavia deshabilitada).
    assert modelo.item(0).isEnabled() is True
    assert modelo.item(1).isEnabled() is True
    assert modelo.item(2).isEnabled() is False


def test_dialogo_edita_expediente_existente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-003",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 5",
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    expediente_a_editar = session.get(Expediente, expediente_id)

    dialog = ExpedienteFormDialog(expediente=expediente_a_editar)
    qtbot.addWidget(dialog)
    session.close()

    assert dialog.windowTitle() == "Editar expediente"
    assert dialog.campo_radicado.text() == "2026-003"
    assert dialog.campo_juzgado.text() == "Juzgado 5"

    dialog.campo_demandante.setText("Ana Maria")
    resultado_id = dialog.guardar()

    assert resultado_id == expediente_id

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    actualizado = session.get(Expediente, expediente_id)
    assert actualizado.demandante == "Ana Maria"
    assert actualizado.radicado == "2026-003"
    session.close()
