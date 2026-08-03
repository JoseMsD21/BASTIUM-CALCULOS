from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.eventos_laborales import EventoLaboralFormDialog
from database.models import (
    AreaDerecho,
    Base,
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


def test_fecha_fin_anterior_o_igual_a_fecha_inicio_lanza_value_error(qtbot, monkeypatch):
    import pytest

    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha_inicio.setDate(date(2020, 5, 10))
    dialog.campo_fecha_fin.setDate(date(2020, 5, 10))

    with pytest.raises(ValueError):
        dialog.guardar()
