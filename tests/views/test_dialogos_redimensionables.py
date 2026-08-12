"""Confirma que los 7 QDialog del proyecto tengan los flags de
minimizar/maximizar activos (Sprint 56) via `hacer_redimensionable()`.

Cada `_xxx_form_dialog(qtbot)` construye el dialogo con los mismos argumentos
minimos que ya usan los tests existentes de cada vista (ver
tests/views/test_abonos.py, test_configuracion.py, test_descuentos_laborales.py,
test_eventos_laborales.py, test_expedientes.py, test_obligaciones.py) -- la
base de datos en memoria la provee el fixture autouse `_db_en_memoria_por_defecto`
de tests/conftest.py, asi que no hace falta crear un engine propio aqui.
"""

from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt

import database.session as session_module
from app.views.abonos import AbonoFormDialog
from app.views.configuracion import HistorialParametroDialog, ParametroFormDialog
from app.views.descuentos_laborales import DescuentoLaboralFormDialog
from app.views.eventos_laborales import EventoLaboralFormDialog
from app.views.expedientes import ExpedienteFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Expediente, Obligacion, TipoObligacion


def _crear_expediente(area: AreaDerecho) -> int:
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-999",
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _crear_obligacion_civil() -> int:
    expediente_id = _crear_expediente(AreaDerecho.CIVIL_FAMILIA)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("100.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def _crear_obligacion_laboral() -> int:
    expediente_id = _crear_expediente(AreaDerecho.LABORAL)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def _abono_form_dialog(qtbot):
    obligacion_id = _crear_obligacion_civil()
    dialogo = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialogo)
    return dialogo


def _parametro_form_dialog(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    return dialogo


def _historial_parametro_dialog(qtbot):
    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)
    return dialogo


def _descuento_laboral_form_dialog(qtbot):
    obligacion_id = _crear_obligacion_laboral()
    dialogo = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialogo)
    return dialogo


def _evento_laboral_form_dialog(qtbot):
    obligacion_id = _crear_obligacion_laboral()
    dialogo = EventoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialogo)
    return dialogo


def _expediente_form_dialog(qtbot):
    dialogo = ExpedienteFormDialog()
    qtbot.addWidget(dialogo)
    return dialogo


def _obligacion_form_dialog(qtbot):
    expediente_id = _crear_expediente(AreaDerecho.CIVIL_FAMILIA)
    dialogo = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialogo)
    return dialogo


@pytest.mark.parametrize(
    "construir_dialogo",
    [
        _abono_form_dialog,
        _parametro_form_dialog,
        _historial_parametro_dialog,
        _descuento_laboral_form_dialog,
        _evento_laboral_form_dialog,
        _expediente_form_dialog,
        _obligacion_form_dialog,
    ],
    ids=[
        "AbonoFormDialog",
        "ParametroFormDialog",
        "HistorialParametroDialog",
        "DescuentoLaboralFormDialog",
        "EventoLaboralFormDialog",
        "ExpedienteFormDialog",
        "ObligacionFormDialog",
    ],
)
def test_dialogo_tiene_flags_de_minimizar_y_maximizar(qtbot, construir_dialogo):
    dialogo = construir_dialogo(qtbot)
    flags = dialogo.windowFlags()
    assert flags & Qt.WindowType.WindowMinimizeButtonHint
    assert flags & Qt.WindowType.WindowMaximizeButtonHint
