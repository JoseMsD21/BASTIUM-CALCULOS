from datetime import date
from decimal import Decimal

from PySide6.QtWidgets import QDialog, QFormLayout, QLineEdit
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.form_utils import guardar_o_actualizar, set_row_visible
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    return session_module.get_session()


def test_guardar_o_actualizar_sin_id_existente_crea_una_fila_nueva(monkeypatch):
    session = _sesion_en_memoria(monkeypatch)
    expediente = Expediente(
        radicado="2026-090", demandante="Ana", demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.commit()

    obligacion_id = guardar_o_actualizar(
        session, Obligacion, None,
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL, concepto="Gastos medicos",
        categoria="DANO_EMERGENTE", fecha_origen=date(2025, 11, 20), valor=Decimal("100.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )

    assert session.query(Obligacion).count() == 1
    guardada = session.get(Obligacion, obligacion_id)
    assert guardada.concepto == "Gastos medicos"


def test_guardar_o_actualizar_con_id_existente_actualiza_en_vez_de_insertar(monkeypatch):
    session = _sesion_en_memoria(monkeypatch)
    expediente = Expediente(
        radicado="2026-091", demandante="Ana", demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL, concepto="Original",
        categoria="DANO_EMERGENTE", fecha_origen=date(2025, 11, 20), valor=Decimal("100.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id

    id_devuelto = guardar_o_actualizar(
        session, Obligacion, obligacion_id,
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL, concepto="Editado",
        categoria="DANO_EMERGENTE", fecha_origen=date(2025, 11, 20), valor=Decimal("200.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )

    assert id_devuelto == obligacion_id
    assert session.query(Obligacion).count() == 1  # no se creo una fila nueva
    actualizada = session.get(Obligacion, obligacion_id)
    assert actualizada.concepto == "Editado"
    assert actualizada.valor == Decimal("200.00")


def test_set_row_visible_oculta_tambien_la_etiqueta_generada_por_addrow(qtbot):
    """QFormLayout.addRow(str, widget) genera un QLabel que widget.setVisible()
    solo, NO oculta -- ese es exactamente el bug de labels huerfanas del
    Sprint 39. set_row_visible() debe ocultar la fila completa."""
    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    campo = QLineEdit()
    layout.addRow("Campo de prueba", campo)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, campo, False)

    etiqueta = layout.labelForField(campo)
    assert etiqueta is not None
    assert campo.isVisible() is False
    assert etiqueta.isVisible() is False


def test_set_row_visible_muestra_tambien_la_etiqueta(qtbot):
    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    campo = QLineEdit()
    layout.addRow("Campo de prueba", campo)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, campo, False)
    set_row_visible(layout, campo, True)

    etiqueta = layout.labelForField(campo)
    assert campo.isVisible() is True
    assert etiqueta.isVisible() is True


def test_set_row_visible_no_falla_si_el_widget_no_tiene_etiqueta(qtbot):
    """addRow(widget) de un solo argumento (ej. un QCheckBox que ocupa toda la
    fila) no genera QLabel -- labelForField() devuelve None. set_row_visible
    debe seguir funcionando sin reventar."""
    from PySide6.QtWidgets import QCheckBox

    dialogo = QDialog()
    layout = QFormLayout(dialogo)
    check = QCheckBox("Solo")
    layout.addRow(check)
    qtbot.addWidget(dialogo)
    dialogo.show()

    set_row_visible(layout, check, False)

    assert check.isVisible() is False
