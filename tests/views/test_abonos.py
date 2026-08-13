from datetime import date
from decimal import Decimal

import pytest
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDialog, QLabel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.views.abonos import AbonoFormDialog
from database.models import Abono, AreaDerecho, Base, Expediente, Obligacion, TipoObligacion


def _obligacion_de_prueba(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

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


def test_campos_no_autoexplicativos_tienen_tooltip(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    for nombre_campo in ("campo_fecha", "campo_monto", "campo_referencia"):
        widget = getattr(dialog, nombre_campo)
        assert widget.toolTip() != "", f"{nombre_campo} deberia tener un tooltip"


def test_monto_muestra_icono_informativo(qtbot, monkeypatch):
    """Sprint 59: 'Monto' es el campo con efecto no obvio (interactua con la
    heuristica de sobrepago) -- recibe el icono (i) explicito, mismo patron
    compartido de agregar_ayuda que los demas formularios principales."""
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    iconos_info = [
        hijo
        for hijo in dialog._contenedor_campo_monto.findChildren(QLabel)
        if hijo.toolTip() != ""
    ]
    assert len(iconos_info) == 1


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


def test_abono_que_supera_el_valor_de_la_obligacion_muestra_advertencia_no_bloqueante(
    qtbot, monkeypatch
):
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


def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2026, 1, 15))
    dialog.campo_monto.setText("100000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.abonos) == 1
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("100000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.abonos) == 0
    session.close()


def test_enter_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_fecha.setDate(date(2026, 1, 15))
    dialog.campo_monto.setText("100000.00")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Return)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert len(obligacion.abonos) == 1
    session.close()


# --- Sprint 60: editar abono (abono_id opcional) ----------------------------


def _obligacion_con_valor(monkeypatch, valor: Decimal) -> int:
    """Igual que `_obligacion_de_prueba` pero con un `valor` a medida -- lo
    necesita `test_editar_abono_no_cuenta_su_propio_valor_anterior_como_sobrepago`
    para reproducir el escenario exacto donde el bug original se manifestaba."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-021",
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
        valor=valor,
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()
    return obligacion_id


def test_abono_id_none_crea_titulo_y_estado_de_creacion(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Agregar abono"
    assert dialog._abono_id is None


def test_abono_id_precarga_los_campos_del_abono_existente(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    primer_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("100000.00")
    primer_dialog.campo_referencia.setText("Original")
    primer_dialog.campo_fecha.setDate(date(2026, 1, 15))
    abono_id = primer_dialog.guardar()

    dialog = AbonoFormDialog(obligacion_id=obligacion_id, abono_id=abono_id)
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Editar abono"
    assert dialog.campo_monto.text() == "100000.00"
    assert dialog.campo_referencia.text() == "Original"
    assert dialog.campo_fecha.date() == QDate(2026, 1, 15)


def test_abono_id_actualiza_la_fila_existente_en_vez_de_crear_una_nueva(qtbot, monkeypatch):
    obligacion_id = _obligacion_de_prueba(monkeypatch)

    primer_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("100000.00")
    primer_dialog.campo_fecha.setDate(date(2026, 1, 15))
    abono_id = primer_dialog.guardar()

    dialog = AbonoFormDialog(obligacion_id=obligacion_id, abono_id=abono_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("250000.00")
    dialog.campo_referencia.setText("Editado")
    resultado_id = dialog.guardar()

    assert resultado_id == abono_id
    session = session_module.get_session()
    assert session.query(Abono).count() == 1  # no se creo una fila nueva
    guardado = session.query(Abono).filter_by(id=abono_id).one()
    assert guardado.monto == Decimal("250000.00")
    assert guardado.referencia == "Editado"
    session.close()


def test_editar_abono_no_cuenta_su_propio_valor_anterior_como_sobrepago(qtbot, monkeypatch):
    """Reproduce el escenario donde el bug original se manifestaba: obligacion de
    $100.000 con un abono existente de $90.000, editado a $95.000. El calculo
    viejo (sin excluir el abono en edicion de `abonos_previos`) habria sumado
    90.000 (valor viejo, todavia en `obligacion.abonos`) + 95.000 (valor nuevo)
    = 185.000 > 100.000 -> falso sobrepago. El calculo correcto excluye el
    abono en edicion: 0 + 95.000 = 95.000 <= 100.000 -> sin advertencia. Nota:
    95.000 por si solo NO supera 100.000, asi que este caso solo lo detecta un
    codigo que efectivamente excluye el valor viejo -- a diferencia de
    `test_abono_id_actualiza_la_fila_existente_en_vez_de_crear_una_nueva`
    (100.000 -> 250.000 sobre una obligacion de 427.900), que pasa igual con o
    sin el fix porque nunca se acerca al limite de sobrepago."""
    obligacion_id = _obligacion_con_valor(monkeypatch, Decimal("100000.00"))

    monkeypatch.setattr("app.views.abonos.QMessageBox.warning", lambda *a, **k: None)
    primer_dialog = AbonoFormDialog(obligacion_id=obligacion_id)
    qtbot.addWidget(primer_dialog)
    primer_dialog.campo_monto.setText("90000.00")
    primer_dialog.campo_fecha.setDate(date(2026, 1, 15))
    abono_id = primer_dialog.guardar()

    avisos = []
    monkeypatch.setattr(
        "app.views.abonos.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )
    dialog = AbonoFormDialog(obligacion_id=obligacion_id, abono_id=abono_id)
    qtbot.addWidget(dialog)
    dialog.campo_monto.setText("95000.00")

    dialog.guardar()

    assert avisos == []
    session = session_module.get_session()
    guardado = session.query(Abono).filter_by(id=abono_id).one()
    assert guardado.monto == Decimal("95000.00")
    session.close()
