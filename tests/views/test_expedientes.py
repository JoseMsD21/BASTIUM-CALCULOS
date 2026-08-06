from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.expedientes import ExpedienteFormDialog, ExpedientesListView
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion


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


def test_dialogo_habilita_todas_las_areas(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    modelo = dialog.combo_area.model()
    assert modelo.rowCount() == len(AREAS_DERECHO)
    # Las 5 areas del derecho estan habilitadas desde el Sprint 3 (Laboral
    # fue la ultima en habilitarse) -- ver Pendientes.md.
    for indice in range(modelo.rowCount()):
        assert modelo.item(indice).isEnabled() is True


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


def test_tabla_tiene_columnas_de_editar_y_eliminar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-005",
            demandante="Pedro",
            demandado="Rosa",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.columnCount() == 6
    assert view.tabla.cellWidget(0, 4) is not None
    assert view.tabla.cellWidget(0, 5) is not None


def test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-004",
            demandante="Carlos",
            demandado="Maria",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    dialogos_creados = []

    class _DialogStub:
        def __init__(self, parent, expediente):
            dialogos_creados.append(expediente.radicado)

        def exec(self):
            return False

    monkeypatch.setattr("app.views.expedientes.ExpedienteFormDialog", _DialogStub)

    view._editar_expediente(view._expediente_ids_por_fila[0])

    assert dialogos_creados == ["2026-004"]


def test_eliminar_expediente_confirmado_borra_el_registro(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-006",
        demandante="Sofia",
        demandado="Diego",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-006", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    session.close()
    assert view.tabla.rowCount() == 0


def test_eliminar_expediente_con_radicado_incorrecto_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-007",
        demandante="Laura",
        demandado="Mario",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("radicado-equivocado", True),
    )
    monkeypatch.setattr("app.views.expedientes.QMessageBox.warning", lambda *args, **kwargs: None)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_cancelado_en_primer_dialogo_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-008",
        demandante="Elena",
        demandado="Pablo",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_borra_en_cascada_sus_obligaciones(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-009",
        demandante="Ines",
        demandado="Tomas",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()

    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital",
            categoria="CAPITAL",
            fecha_origen=date(2026, 1, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-009", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    assert session.query(Obligacion).count() == 0
    session.close()


def test_boton_guardar_del_formulario_tiene_icono_y_clase_primaria(qtbot):
    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_boton_nuevo_expediente_tiene_clase_primaria(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.boton_nuevo.property("class") == "primary"


def test_boton_eliminar_de_cada_fila_tiene_icono_y_clase_destructiva(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-099",
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

    boton_eliminar = view.tabla.cellWidget(0, 5)
    assert not boton_eliminar.icon().isNull()
    assert boton_eliminar.property("class") == "destructive"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-050")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-050").one_or_none()
    assert guardado is not None
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-051")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-051").one_or_none()
    assert guardado is None
    session.close()
