"""Sprint 95 (conexion a la UI): dialogo para registrar horas extra
(HED/HEN/HEFD/HEFN) en una obligacion Laboral."""

from datetime import date
from decimal import Decimal

import pytest

import database.session as session_module
from app.views.horas_extra_laborales import HoraExtraLaboralFormDialog
from database.models import (
    AreaDerecho,
    Expediente,
    HoraExtraLaboral,
    Obligacion,
    TipoObligacion,
)
from tests.views.conftest import crear_sesion_en_memoria


def _obligacion_laboral_de_prueba(monkeypatch) -> int:
    session = crear_sesion_en_memoria(monkeypatch)
    expediente = Expediente(
        radicado="2026-095",
        demandante="Trabajador",
        demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2024, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2025, 12, 31),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def _dialogo(qtbot, monkeypatch) -> tuple[HoraExtraLaboralFormDialog, int]:
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)
    dialogo = HoraExtraLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialogo)
    dialogo.show()
    return dialogo, obligacion_id


def _seleccionar_concepto(dialogo, codigo: str) -> None:
    dialogo.combo_concepto.setCurrentIndex(dialogo.combo_concepto.findData(codigo))


def _guardada(obligacion_id: int) -> HoraExtraLaboral:
    session = session_module.get_session()
    fila = session.query(HoraExtraLaboral).filter_by(obligacion_id=obligacion_id).one()
    session.close()
    return fila


def test_combo_ofrece_los_4_conceptos_del_motor(qtbot, monkeypatch):
    dialogo, _ = _dialogo(qtbot, monkeypatch)

    codigos = [dialogo.combo_concepto.itemData(i) for i in range(dialogo.combo_concepto.count())]
    assert codigos == ["HED", "HEN", "HEFD", "HEFN"]


def test_guarda_hed_con_factor_del_motor_y_sin_porcentaje(qtbot, monkeypatch):
    dialogo, obligacion_id = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HED")
    dialogo.campo_fecha_causacion.setDate(date(2024, 3, 15))
    dialogo.campo_horas.setText("10")
    dialogo.campo_valor_hora.setText("10000")

    dialogo.guardar()

    fila = _guardada(obligacion_id)
    assert fila.concepto == "HED"
    assert fila.fecha_causacion == date(2024, 3, 15)
    assert fila.numero_horas == Decimal("10")
    assert fila.valor_hora == Decimal("10000")
    assert fila.porcentaje_manual is None


def test_factor_vigente_se_muestra_segun_concepto_y_fecha(qtbot, monkeypatch):
    dialogo, _ = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HEFD")
    dialogo.campo_fecha_causacion.setDate(date(2025, 8, 10))

    assert "2,05" in dialogo.etiqueta_factor.text()
    assert dialogo.campo_porcentaje_manual.isVisible() is False


def test_hora_festiva_antes_del_tramo_1_pide_porcentaje_y_explica_por_que(qtbot, monkeypatch):
    dialogo, _ = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HEFN")
    dialogo.campo_fecha_causacion.setDate(date(2025, 6, 30))

    assert dialogo.campo_porcentaje_manual.isVisible() is True
    assert dialogo.etiqueta_explicacion_porcentaje.isVisible() is True
    assert "01/07/2025" in dialogo.etiqueta_explicacion_porcentaje.text()


def test_hora_festiva_antes_del_tramo_1_sin_porcentaje_no_guarda(qtbot, monkeypatch):
    dialogo, _ = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HEFD")
    dialogo.campo_fecha_causacion.setDate(date(2025, 6, 30))
    dialogo.campo_horas.setText("2")
    dialogo.campo_valor_hora.setText("10000")

    with pytest.raises(ValueError, match="porcentaje"):
        dialogo.guardar()


def test_hora_festiva_antes_del_tramo_1_guarda_el_porcentaje_digitado(qtbot, monkeypatch):
    dialogo, obligacion_id = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HEFD")
    dialogo.campo_fecha_causacion.setDate(date(2025, 6, 30))
    dialogo.campo_horas.setText("2")
    dialogo.campo_valor_hora.setText("10000")
    dialogo.campo_porcentaje_manual.setText("100")

    dialogo.guardar()

    assert _guardada(obligacion_id).porcentaje_manual == Decimal("100")


def test_porcentaje_digitado_se_descarta_si_el_motor_tiene_factor(qtbot, monkeypatch):
    dialogo, obligacion_id = _dialogo(qtbot, monkeypatch)
    _seleccionar_concepto(dialogo, "HEFD")
    dialogo.campo_fecha_causacion.setDate(date(2025, 6, 30))
    dialogo.campo_porcentaje_manual.setText("100")
    dialogo.campo_fecha_causacion.setDate(date(2025, 7, 1))
    dialogo.campo_horas.setText("2")
    dialogo.campo_valor_hora.setText("10000")

    dialogo.guardar()

    assert _guardada(obligacion_id).porcentaje_manual is None


@pytest.mark.parametrize("horas", ["0", "-1", "abc", ""])
def test_horas_invalidas_no_guardan(qtbot, monkeypatch, horas):
    dialogo, _ = _dialogo(qtbot, monkeypatch)
    dialogo.campo_horas.setText(horas)
    dialogo.campo_valor_hora.setText("10000")

    with pytest.raises(ValueError):
        dialogo.guardar()


@pytest.mark.parametrize("valor", ["0", "-5", "diez"])
def test_valor_hora_invalido_no_guarda(qtbot, monkeypatch, valor):
    dialogo, _ = _dialogo(qtbot, monkeypatch)
    dialogo.campo_horas.setText("2")
    dialogo.campo_valor_hora.setText(valor)

    with pytest.raises(ValueError):
        dialogo.guardar()
