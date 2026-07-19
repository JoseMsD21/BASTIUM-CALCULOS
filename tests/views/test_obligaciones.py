from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion
from app.views.obligaciones import ObligacionFormDialog


def _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-010",
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


def test_guarda_obligacion_puntual(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("427900.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.PUNTUAL
    assert guardada.concepto == "Gastos medicos"
    session.close()


def test_guarda_obligacion_recurrente_con_dia_de_pago(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Cuota alimentaria")
    dialog.campo_valor.setText("500000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 1, 1))
    dialog.campo_dia_pago.setValue(5)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.RECURRENTE
    assert guardada.dia_pago == 5
    session.close()


def test_valor_negativo_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("-100.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest
    with pytest.raises(ValueError):
        dialog.guardar()


def test_guarda_obligacion_comercial_con_tasa_moratoria_y_ibc(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tasa_moratoria_anual == Decimal("24.00")
    assert guardada.ibc_vigente_anual == Decimal("20.00")
    assert guardada.fecha_vencimiento == date(2025, 2, 1)
    session.close()


def test_campos_comerciales_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    # isVisible() solo refleja la visibilidad real (heredada de los ancestros) si
    # el dialogo fue mostrado -- sin dialog.show(), toda esta asercion pasaria sin
    # importar el valor real de setVisible() en los campos.
    assert dialog.campo_tasa_moratoria.isVisible() is False
    assert dialog.campo_fecha_vencimiento.isVisible() is False
    assert dialog.campo_ibc_vigente.isVisible() is False


def test_campos_comerciales_visibles_para_area_comercial(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_tasa_moratoria.isVisible() is True
    assert dialog.campo_fecha_vencimiento.isVisible() is True
    assert dialog.campo_ibc_vigente.isVisible() is True


def test_guarda_obligacion_sancionatoria(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Multa SIC")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2019, 6, 1))
    dialog.campo_cantidad_smlmv_uvt.setText("2")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.cantidad_smlmv_uvt == Decimal("2")
    session.close()


def test_guarda_obligacion_honorarios_con_costas(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("20.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")
    dialog.campo_costas_pct.setText("5.00")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.honorarios_fijos_pactados == Decimal("1000000.00")
    assert guardada.cuota_litis_pactada_pct == Decimal("20.00")
    assert guardada.beneficio_obtenido == Decimal("10000000.00")
    assert guardada.costas_pct_manual == Decimal("5.00")
    session.close()


def test_guarda_obligacion_honorarios_sin_costas_queda_en_none(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios sin costas")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("500000.00")
    dialog.campo_cuota_litis_pct.setText("10.00")
    dialog.campo_beneficio_obtenido.setText("5000000.00")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.costas_pct_manual is None
    session.close()


def test_campos_sancionatorio_y_honorarios_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is False
    assert dialog.campo_honorarios_fijos.isVisible() is False
    assert dialog.campo_cuota_litis_pct.isVisible() is False
    assert dialog.campo_beneficio_obtenido.isVisible() is False
    assert dialog.campo_costas_pct.isVisible() is False
    assert dialog.campo_valor.isVisible() is True


def test_campos_sancionatorio_visibles_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is True
    assert dialog.campo_valor.isVisible() is False
    assert dialog.campo_honorarios_fijos.isVisible() is False


def test_campos_honorarios_visibles_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_honorarios_fijos.isVisible() is True
    assert dialog.campo_cuota_litis_pct.isVisible() is True
    assert dialog.campo_beneficio_obtenido.isVisible() is True
    assert dialog.campo_costas_pct.isVisible() is True
    assert dialog.campo_valor.isVisible() is False
    assert dialog.campo_cantidad_smlmv_uvt.isVisible() is False


def test_combo_tipo_no_ofrece_recurrente_para_sancionatorio(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo.count() == 1
    assert dialog.combo_tipo.itemData(0) == "PUNTUAL"


def test_combo_tipo_no_ofrece_recurrente_para_honorarios(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo.count() == 1
    assert dialog.combo_tipo.itemData(0) == "PUNTUAL"


def test_combo_tipo_si_ofrece_recurrente_para_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo.count() == 2
    assert dialog.combo_tipo.itemData(1) == "RECURRENTE"
