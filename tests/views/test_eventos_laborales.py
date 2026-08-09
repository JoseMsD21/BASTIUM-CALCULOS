from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.eventos_laborales import EventoLaboralFormDialog
from database.models import (
    AreaDerecho,
    Base,
    EventoLaboral,
    Expediente,
    MotivoSuspension,
    Obligacion,
    TipoEventoLaboral,
    TipoObligacion,
)


def _obligacion_laboral_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-020", demandante="Ana", demandado="Luis",
        area_derecho=AreaDerecho.LABORAL, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato", categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1), valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"), fecha_inicio=date(2020, 1, 1), fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def test_guarda_evento_suspension(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    dialog.campo_fecha_inicio.setDate(date(2020, 3, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 3, 15))
    dialog.combo_motivo.setCurrentIndex(0)  # Huelga

    dialog.guardar()

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    evento = obligacion.eventos_laborales[0]
    assert evento.tipo == TipoEventoLaboral.SUSPENSION
    assert evento.motivo_suspension == MotivoSuspension.HUELGA
    session.close()


def test_guarda_evento_incapacidad_comun_sin_motivo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # Incapacidad comun
    dialog.campo_fecha_inicio.setDate(date(2020, 5, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 5, 4))

    dialog.guardar()

    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    evento = obligacion.eventos_laborales[0]
    assert evento.tipo == TipoEventoLaboral.INCAPACIDAD_COMUN
    assert evento.motivo_suspension is None
    session.close()


def test_combo_motivo_oculto_si_tipo_no_es_suspension(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_motivo.isVisible() is True  # Suspension es el default (indice 0)
    dialog.combo_tipo.setCurrentIndex(2)  # Incapacidad laboral
    assert dialog.combo_motivo.isVisible() is False


def test_label_motivo_suspension_no_queda_huerfana_en_evento_incapacidad(qtbot, monkeypatch):
    """Sprint 39: la etiqueta "Motivo de suspension" generada por
    QFormLayout.addRow(str, combo_motivo) debe ocultarse junto con el combo
    cuando el tipo de evento no es Suspension -- si solo se oculta el combo
    queda una fila huerfana (etiqueta de texto visible sin su campo)."""
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.show()

    etiqueta_motivo = dialog._layout_formulario.labelForField(dialog.combo_motivo)
    assert etiqueta_motivo is not None

    dialog.combo_tipo.setCurrentIndex(1)  # Incapacidad comun
    assert etiqueta_motivo.isVisible() is False
    assert dialog.combo_motivo.isVisible() is False

    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    assert etiqueta_motivo.isVisible() is True
    assert dialog.combo_motivo.isVisible() is True


def test_fecha_fin_anterior_o_igual_a_fecha_inicio_lanza_value_error(qtbot, monkeypatch):
    import pytest

    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha_inicio.setDate(date(2020, 5, 10))
    dialog.campo_fecha_fin.setDate(date(2020, 5, 10))

    with pytest.raises(ValueError):
        dialog.guardar()


def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    dialog.campo_fecha_inicio.setDate(date(2020, 3, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 3, 15))
    dialog.combo_motivo.setCurrentIndex(0)  # Huelga

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 1
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 0
    session.close()


def test_evento_id_precarga_los_campos_del_evento_existente(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)
    session = session_module.get_session()
    evento = EventoLaboral(
        obligacion_id=obligacion_id, tipo=TipoEventoLaboral.SUSPENSION,
        fecha_inicio=date(2020, 3, 1), fecha_fin=date(2020, 3, 15),
        motivo_suspension=MotivoSuspension.HUELGA,
    )
    session.add(evento)
    session.commit()
    evento_id = evento.id
    session.close()

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id, evento_id=evento_id)
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo.currentData() == TipoEventoLaboral.SUSPENSION
    assert dialog.campo_fecha_inicio.date().toPython() == date(2020, 3, 1)
    assert dialog.campo_fecha_fin.date().toPython() == date(2020, 3, 15)
    assert dialog.combo_motivo.currentData() == MotivoSuspension.HUELGA


def test_evento_id_titulo_del_dialogo_dice_editar(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)
    session = session_module.get_session()
    evento = EventoLaboral(
        obligacion_id=obligacion_id, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
    )
    session.add(evento)
    session.commit()
    evento_id = evento.id
    session.close()

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id, evento_id=evento_id)
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Editar evento contractual"


def test_guardar_con_evento_id_actualiza_en_vez_de_crear_uno_nuevo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)
    session = session_module.get_session()
    evento = EventoLaboral(
        obligacion_id=obligacion_id, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
    )
    session.add(evento)
    session.commit()
    evento_id = evento.id
    session.close()

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id, evento_id=evento_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha_fin.setDate(date(2020, 5, 10))  # cambia la fecha de fin

    id_devuelto = dialog.guardar()

    assert id_devuelto == evento_id
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 1  # no se creo una fila nueva
    assert obligacion.eventos_laborales[0].fecha_fin == date(2020, 5, 10)
    session.close()


def test_enter_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # Suspension
    dialog.campo_fecha_inicio.setDate(date(2020, 3, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 3, 15))
    dialog.combo_motivo.setCurrentIndex(0)  # Huelga

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Return)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.eventos_laborales) == 1
    session.close()
