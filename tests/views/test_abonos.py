from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion, Abono
from app.views.abonos import AbonoFormDialog


def _obligacion_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-020",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def test_guarda_abono_asociado_a_obligacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")
    dialog.campo_referencia.setText("Consignacion Bancolombia")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardado = session.query(Abono).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("100000.00")
    assert guardado.referencia == "Consignacion Bancolombia"
    session.close()


def test_monto_cero_lanza_error_de_validacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("0.00")

    with pytest.raises(ValueError):
        dialog.guardar()


def test_abono_que_supera_el_valor_de_la_obligacion_muestra_advertencia_no_bloqueante(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)  # valor=427900.00

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("500000.00")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    abono_id = dialog.guardar()

    # La advertencia se muestra...
    assert len(avisos) == 1
    assert "sobrepago" in avisos[0][0].lower()
    # ...pero NO bloquea el guardado.
    session = session_module.get_session()
    guardado = session.query(Abono).filter_by(obligacion_id=obligacion_id).one()
    assert guardado.monto == Decimal("500000.00")
    assert guardado.id == abono_id
    session.close()


def test_abono_dentro_del_valor_de_la_obligacion_no_muestra_advertencia(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)  # valor=427900.00

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")
    dialog.campo_fecha.setDate(date(2026, 1, 15))

    dialog.guardar()

    assert len(avisos) == 0


def test_abonos_acumulados_que_superan_el_valor_muestran_advertencia(qtbot, monkeypatch):
    # El primer abono (300000) no supera el valor (427900). El segundo (200000) hace
    # que la suma acumulada (500000) si lo supere -- la heuristica debe sumar abonos
    # previos, no comparar solo el monto del abono nuevo contra el valor.
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    monkeypatch.setattr("app.views.abonos.QMessageBox.warning", lambda *a, **k: None)
    primer_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("300000.00")
    primer_dialog.campo_fecha.setDate(date(2026, 1, 10))
    primer_dialog.guardar()

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )
    segundo_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(segundo_dialog)
    segundo_dialog.campo_monto.setText("200000.00")
    segundo_dialog.campo_fecha.setDate(date(2026, 1, 20))
    segundo_dialog.guardar()

    assert len(avisos) == 1
