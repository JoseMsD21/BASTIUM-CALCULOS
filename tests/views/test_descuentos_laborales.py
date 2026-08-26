from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.descuentos_laborales import DescuentoLaboralFormDialog
from database.models import (
    AreaDerecho,
    Base,
    DescuentoLaboral,
    Expediente,
    Obligacion,
    TipoObligacion,
)


def _obligacion_laboral_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-080",
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


def test_guarda_descuento_legal_con_motivo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2021, 1, 15))
    dialog.campo_monto.setText("500000.00")
    dialog.check_es_legal.setChecked(True)
    dialog.campo_motivo.setText("Prestamo cooperativa")

    dialog.guardar()

    session = session_module.get_session()
    guardado = session.query(DescuentoLaboral).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("500000.00")
    assert guardado.es_legal is True
    assert guardado.motivo == "Prestamo cooperativa"
    session.close()


def test_guarda_descuento_ilegal_sin_motivo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2021, 1, 15))
    dialog.campo_monto.setText("500000.00")
    dialog.check_es_legal.setChecked(False)

    dialog.guardar()

    session = session_module.get_session()
    guardado = session.query(DescuentoLaboral).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.es_legal is False
    assert guardado.motivo is None
    session.close()


def test_check_es_legal_esta_marcado_por_defecto(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert dialog.check_es_legal.isChecked() is True


def test_monto_cero_lanza_error_de_validacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("0.00")

    with pytest.raises(ValueError):
        dialog.guardar()


def test_monto_negativo_lanza_error_de_validacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("-500000.00")

    with pytest.raises(ValueError):
        dialog.guardar()


def test_descuento_que_supera_el_valor_de_la_obligacion_muestra_advertencia_no_bloqueante(
    qtbot, monkeypatch
):
    # Sprint 111 (regresion del Sprint 44): DescuentoLaboralFormDialog no
    # tenia la misma heuristica no bloqueante de "posible sobrepago" que ya
    # tiene AbonoFormDialog, pese a que LaboralStrategy.liquidar() resta un
    # descuento del neto adeudado igual que un abono.
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)  # valor=3000000.00

    avisos = []
    monkeypatch.setattr(
        "app.views.descuentos_laborales.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("3500000.00")
    dialog.campo_fecha.setDate(date(2021, 1, 15))

    descuento_id = dialog.guardar()

    # La advertencia se muestra...
    assert len(avisos) == 1
    assert "sobrepago" in avisos[0][0].lower()
    # ...pero NO bloquea el guardado.
    session = session_module.get_session()
    guardado = session.query(DescuentoLaboral).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("3500000.00")
    assert guardado.id == descuento_id
    session.close()


def test_descuento_dentro_del_valor_de_la_obligacion_no_muestra_advertencia(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)  # valor=3000000.00

    avisos = []
    monkeypatch.setattr(
        "app.views.descuentos_laborales.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("500000.00")
    dialog.campo_fecha.setDate(date(2021, 1, 15))

    dialog.guardar()

    assert len(avisos) == 0


def test_descuentos_acumulados_que_superan_el_valor_muestran_advertencia(qtbot, monkeypatch):
    # El primer descuento (2000000) no supera el valor (3000000). El segundo
    # (1500000) hace que la suma acumulada (3500000) si lo supere -- la
    # heuristica debe sumar descuentos previos, no comparar solo el monto
    # nuevo contra el valor.
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    monkeypatch.setattr(
        "app.views.descuentos_laborales.QMessageBox.warning", lambda *a, **k: None
    )
    primer_dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("2000000.00")
    primer_dialog.campo_fecha.setDate(date(2021, 1, 10))
    primer_dialog.guardar()

    avisos = []
    monkeypatch.setattr(
        "app.views.descuentos_laborales.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )
    segundo_dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(segundo_dialog)
    segundo_dialog.campo_monto.setText("1500000.00")
    segundo_dialog.campo_fecha.setDate(date(2021, 1, 20))
    segundo_dialog.guardar()

    assert len(avisos) == 1
    assert "sobrepago" in avisos[0][0].lower()


def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2021, 1, 15))
    dialog.campo_monto.setText("500000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.descuentos_laborales) == 1
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    obligacion_id = _obligacion_laboral_de_prueba(monkeypatch)

    dialog = DescuentoLaboralFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("500000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.descuentos_laborales) == 0
    session.close()
