from datetime import date, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFormLayout, QGridLayout, QLabel
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.services.recurrencia_fechas_fijas import deserializar_fechas_anuales
from app.views.obligaciones import ObligacionFormDialog
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    TipoObligacion,
    TipoReajusteAnual,
    TipoRecurrencia,
)


def _filas_con_etiqueta_huerfana(layout: QFormLayout) -> list[str]:
    """Devuelve el texto de cada etiqueta de `layout` cuya visibilidad no
    coincide con la de su widget de campo (Sprint 39): una fila "huerfana" es
    una etiqueta visible sin su campo (o viceversa), que es exactamente el
    bug que produce QFormLayout.addRow(str, widget) + widget.setVisible(...)
    suelto sin ocultar tambien la etiqueta generada."""
    huerfanas = []
    for fila in range(layout.rowCount()):
        item_etiqueta = layout.itemAt(fila, QFormLayout.ItemRole.LabelRole)
        item_campo = layout.itemAt(fila, QFormLayout.ItemRole.FieldRole)
        if item_etiqueta is None or item_campo is None:
            continue
        etiqueta = item_etiqueta.widget()
        campo = item_campo.widget()
        if etiqueta is None or campo is None:
            continue
        if etiqueta.isVisible() != campo.isVisible():
            huerfanas.append(etiqueta.text())
    return huerfanas


def _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

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


def test_guarda_obligacion_recurrente_civil_familia_con_reajuste_smmlv(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Cuota alimentaria")
    dialog.campo_valor.setText("500000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 1, 1))
    dialog.campo_dia_pago.setValue(5)
    indice_smmlv = dialog.combo_tipo_reajuste_anual.findData("SMMLV")
    dialog.combo_tipo_reajuste_anual.setCurrentIndex(indice_smmlv)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo_reajuste_anual == TipoReajusteAnual.SMMLV
    session.close()


def test_guarda_obligacion_recurrente_civil_familia_sin_tocar_reajuste_queda_ninguno(
    qtbot, monkeypatch
):
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
    assert guardada.tipo_reajuste_anual == TipoReajusteAnual.NINGUNO
    session.close()


def test_guarda_obligacion_puntual_civil_familia_queda_con_reajuste_ninguno(qtbot, monkeypatch):
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
    assert guardada.tipo_reajuste_anual == TipoReajusteAnual.NINGUNO
    session.close()


def test_combo_reajuste_anual_visible_solo_para_recurrente_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    assert dialog.combo_tipo_reajuste_anual.isVisible() is False

    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    assert dialog.combo_tipo_reajuste_anual.isVisible() is True


def test_combo_reajuste_anual_oculto_para_comercial_recurrente(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE

    assert dialog.combo_tipo_reajuste_anual.isVisible() is False


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


def test_tasa_moratoria_comercial_absurdamente_alta_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("99999.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_ibc_vigente_negativo_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("-20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


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


def test_cantidad_smlmv_uvt_no_positiva_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Multa SIC")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2019, 6, 1))
    dialog.campo_cantidad_smlmv_uvt.setText("0")

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


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


def test_indicador_unidad_muestra_smlmv_antes_del_corte(qtbot, monkeypatch):
    """Sprint 45: junto a `campo_cantidad_smlmv_uvt`, un indicador dinamico
    debe mostrar la unidad (SMLMV o UVT) que se aplicara segun la fecha de
    origen -- reutilizando el corte del 2020-01-01 ya resuelto en
    `smlmv_to_uvt.py`, sin duplicarlo en la UI."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.campo_fecha_origen.setDate(date(2019, 12, 31))

    assert "SMLMV" in dialog.label_unidad_smlmv_uvt.text()
    assert "UVT" not in dialog.label_unidad_smlmv_uvt.text()


def test_indicador_unidad_muestra_uvt_desde_el_corte(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))

    assert "UVT" in dialog.label_unidad_smlmv_uvt.text()
    assert "SMLMV" not in dialog.label_unidad_smlmv_uvt.text()


def test_indicador_unidad_se_actualiza_en_vivo_al_cambiar_fecha(qtbot, monkeypatch):
    """El indicador debe reaccionar a `dateChanged` sin necesidad de guardar
    el formulario -- cambia de SMLMV a UVT y de vuelta, en el mismo dialogo."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)

    dialog.campo_fecha_origen.setDate(date(2015, 3, 10))
    assert "SMLMV" in dialog.label_unidad_smlmv_uvt.text()

    dialog.campo_fecha_origen.setDate(date(2023, 5, 20))
    assert "UVT" in dialog.label_unidad_smlmv_uvt.text()

    dialog.campo_fecha_origen.setDate(date(2010, 8, 1))
    assert "SMLMV" in dialog.label_unidad_smlmv_uvt.text()


def test_indicador_unidad_oculto_para_areas_distintas_de_sancionatorio(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.label_unidad_smlmv_uvt.isVisible() is False


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


def test_guarda_obligacion_laboral_con_fechas_de_contrato(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.PUNTUAL
    assert guardada.fecha_inicio == date(2020, 1, 1)
    assert guardada.fecha_fin == date(2020, 12, 31)
    assert guardada.tasa_efectiva_anual == Decimal("0.00")
    assert guardada.pagada is False
    assert guardada.fecha_pago_total is None
    session.close()


def test_guarda_obligacion_laboral_marcada_como_pagada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))
    dialog.check_pagada.setChecked(True)
    dialog.campo_fecha_pago_total.setDate(date(2021, 1, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.pagada is True
    assert guardada.fecha_pago_total == date(2021, 1, 15)
    session.close()


def test_valor_cero_o_negativo_en_laboral_lanza_error(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_campos_laborales_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_fecha_fin.isVisible() is False
    assert dialog.check_pagada.isVisible() is False
    assert dialog.campo_fecha_pago_total.isVisible() is False


def test_campos_laborales_visibles_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_fecha_fin.isVisible() is True
    assert dialog.check_pagada.isVisible() is True
    assert dialog.combo_tipo.isVisible() is False
    assert dialog.campo_tasa.isVisible() is False
    assert dialog.campo_valor.isVisible() is True


def test_campo_fecha_pago_total_solo_visible_si_pagada_marcada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_fecha_pago_total.isVisible() is False
    dialog.check_pagada.setChecked(True)
    assert dialog.campo_fecha_pago_total.isVisible() is True
    dialog.check_pagada.setChecked(False)
    assert dialog.campo_fecha_pago_total.isVisible() is False


def test_check_indexacion_visible_en_las_5_areas_con_checkbox_manual(qtbot, monkeypatch):
    # Sprint 43: el despacho confirmo IPC para las 5 areas restantes, cada una con su
    # propia regla de exclusion/coexistencia -- el checkbox pasa a ser visible en
    # Comercial/Laboral/Sancionatorio/Honorarios ademas de Civil/Familia. TRIBUTARIO
    # se queda oculto: ahi IPC es automatico (Art. 867-1 E.T.), no una eleccion manual.
    areas_con_checkbox = {
        "CIVIL_FAMILIA": AreaDerecho.CIVIL_FAMILIA,
        "COMERCIAL": AreaDerecho.COMERCIAL,
        "LABORAL": AreaDerecho.LABORAL,
        "SANCIONATORIO": AreaDerecho.SANCIONATORIO,
        "HONORARIOS": AreaDerecho.HONORARIOS,
    }
    for area_str, area_enum in areas_con_checkbox.items():
        expediente_id = _expediente_de_prueba(monkeypatch, area=area_enum)
        dialog = ObligacionFormDialog(expediente_id=expediente_id, area=area_str)
        qtbot.addWidget(dialog)
        dialog.show()
        assert dialog.check_aplica_indexacion_ipc.isVisible() is True, area_str

    expediente_id_tributario = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)
    dialog_tributario = ObligacionFormDialog(
        expediente_id=expediente_id_tributario, area="TRIBUTARIO"
    )
    qtbot.addWidget(dialog_tributario)
    dialog_tributario.show()
    assert dialog_tributario.check_aplica_indexacion_ipc.isVisible() is False


def test_check_pacto_expreso_indexacion_visible_solo_en_comercial(qtbot, monkeypatch):
    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(
        expediente_id=expediente_id_comercial, area="COMERCIAL"
    )
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.check_pacto_expreso_indexacion.isVisible() is True

    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_pacto_expreso_indexacion.isVisible() is False


def test_check_protegida_inflacion_uvr_visible_solo_en_tributario(qtbot, monkeypatch):
    expediente_id_tributario = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)
    dialog_tributario = ObligacionFormDialog(
        expediente_id=expediente_id_tributario, area="TRIBUTARIO"
    )
    qtbot.addWidget(dialog_tributario)
    dialog_tributario.show()
    assert dialog_tributario.check_protegida_inflacion_uvr.isVisible() is True

    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_protegida_inflacion_uvr.isVisible() is False


def test_guarda_obligacion_con_indexacion_ipc_marcada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is True
    session.close()


def test_guarda_obligacion_sin_marcar_indexacion_queda_en_false(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is False
    session.close()


def test_guarda_obligacion_comercial_con_pacto_expreso_indexacion(qtbot, monkeypatch):
    # Sprint 43: la GUI debe persistir pacto_expreso_indexacion (habilita el modo b
    # de la regla XOR de indexacion IPC en ComercialStrategy).
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
    dialog.check_aplica_indexacion_ipc.setChecked(True)
    dialog.check_pacto_expreso_indexacion.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is True
    assert guardada.pacto_expreso_indexacion is True
    session.close()


def test_guarda_obligacion_comercial_sin_pacto_expreso_queda_en_false(qtbot, monkeypatch):
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
    assert guardada.pacto_expreso_indexacion is False
    session.close()


def test_guarda_obligacion_tributaria_con_proteccion_inflacion_uvr(qtbot, monkeypatch):
    # Sprint 43: la GUI debe persistir protegida_inflacion_uvr (prohibicion de doble
    # cobro en TributarioStrategy).
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("Impuesto de renta 2024")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))
    dialog.check_protegida_inflacion_uvr.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.protegida_inflacion_uvr is True
    session.close()


def test_guarda_obligacion_laboral_con_indexacion_ipc_marcada(qtbot, monkeypatch):
    # Sprint 43: _guardar_laboral() antes no pasaba aplica_indexacion_ipc en absoluto
    # (el checkbox estaba oculto para LABORAL) -- ahora debe persistirlo.
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))
    dialog.check_aplica_indexacion_ipc.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.aplica_indexacion_ipc is True
    session.close()


def test_guarda_obligacion_laboral_con_seguridad_social(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))
    dialog.check_incluir_seguridad_social.setChecked(True)
    dialog.combo_nivel_riesgo_arl.setCurrentIndex(0)  # "I"

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.incluir_seguridad_social is True
    assert guardada.nivel_riesgo_arl == "I"
    session.close()


def test_guarda_obligacion_laboral_sin_seguridad_social_por_defecto(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.incluir_seguridad_social is False
    assert guardada.nivel_riesgo_arl is None
    session.close()


def test_laboral_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("  ")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_laboral_fecha_inicio_contrato_posterior_a_fecha_de_corte_lanza_error(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(
        monkeypatch, area=AreaDerecho.LABORAL
    )  # corte = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte
    dialog.campo_fecha_fin.setDate(date(2026, 12, 31))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_combo_nivel_riesgo_arl_visible_solo_si_checkbox_activo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_nivel_riesgo_arl.isVisible() is False
    dialog.check_incluir_seguridad_social.setChecked(True)
    assert dialog.combo_nivel_riesgo_arl.isVisible() is True


def test_label_fecha_origen_cambia_para_area_laboral(qtbot, monkeypatch):
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)

    etiqueta_laboral = dialog_laboral.layout_datos_basicos.labelForField(
        dialog_laboral.campo_fecha_origen
    ).text()
    etiqueta_civil = dialog_civil.layout_datos_basicos.labelForField(
        dialog_civil.campo_fecha_origen
    ).text()

    assert etiqueta_laboral != etiqueta_civil
    assert etiqueta_laboral == "Fecha de inicio del contrato"
    assert etiqueta_civil == "Fecha de origen (Puntual)"


def test_combo_moneda_visible_solo_para_area_comercial(qtbot, monkeypatch):
    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(
        expediente_id=expediente_id_comercial, area="COMERCIAL"
    )
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.combo_moneda.isVisible() is True

    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.combo_moneda.isVisible() is False


def test_campos_trm_visibles_solo_si_moneda_es_usd_en_comercial(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.combo_moneda.currentData() == "COP"
    assert dialog.campo_trm_aplicable.isVisible() is False
    assert dialog.campo_trm_fecha_referencia.isVisible() is False

    indice_usd = dialog.combo_moneda.findData("USD")
    dialog.combo_moneda.setCurrentIndex(indice_usd)
    assert dialog.campo_trm_aplicable.isVisible() is True
    assert dialog.campo_trm_fecha_referencia.isVisible() is True

    dialog.combo_moneda.setCurrentIndex(dialog.combo_moneda.findData("COP"))
    assert dialog.campo_trm_aplicable.isVisible() is False
    assert dialog.campo_trm_fecha_referencia.isVisible() is False


def test_guarda_obligacion_comercial_en_usd_con_trm(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Capital de pagare en USD")
    dialog.campo_valor.setText("10000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("20.00")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))
    dialog.combo_moneda.setCurrentIndex(dialog.combo_moneda.findData("USD"))
    dialog.campo_trm_aplicable.setText("4150.2500")
    dialog.campo_trm_fecha_referencia.setDate(date(2025, 1, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.moneda == "USD"
    assert guardada.trm_aplicable == Decimal("4150.2500")
    assert guardada.trm_fecha_referencia == date(2025, 1, 1)
    session.close()


def test_guarda_obligacion_comercial_en_cop_deja_trm_en_none(qtbot, monkeypatch):
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
    assert guardada.moneda == "COP"
    assert guardada.trm_aplicable is None
    assert guardada.trm_fecha_referencia is None
    session.close()


def test_guarda_obligacion_tributaria_impuesto_a_cargo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("Impuesto de renta 2024")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "IMPUESTO_A_CARGO"
    assert guardada.valor == Decimal("10000000.00")
    session.close()


def test_tributario_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("   ")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_tributario_fecha_origen_posterior_a_fecha_de_corte_lanza_error(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(
        monkeypatch, area=AreaDerecho.TRIBUTARIO
    )  # corte = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.combo_categoria.setCurrentIndex(0)  # IMPUESTO_A_CARGO
    dialog.campo_concepto.setText("Impuesto de renta 2026")
    dialog.campo_valor.setText("10000000.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_guarda_sancion_extemporaneidad_con_meses_de_atraso(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("SANCION_EXTEMPORANEIDAD")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Sancion extemporaneidad renta 2024")
    dialog.campo_base_sancion.setText("10000000.00")
    dialog.campo_meses_extemporaneidad.setValue(2)
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "SANCION_EXTEMPORANEIDAD"
    assert guardada.base_sancion_tributaria == Decimal("10000000.00")
    assert guardada.meses_extemporaneidad == 2
    session.close()


def test_guarda_sancion_inexactitud_agravada(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("SANCION_INEXACTITUD")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Sancion inexactitud renta 2024")
    dialog.campo_base_sancion.setText("5000000.00")
    dialog.check_sancion_agravada.setChecked(True)
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "SANCION_INEXACTITUD"
    assert guardada.sancion_agravada is True
    session.close()


def test_guarda_renta_liquida_con_los_5_campos(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    indice = dialog.combo_categoria.findData("RENTA_LIQUIDA")
    dialog.combo_categoria.setCurrentIndex(indice)
    dialog.campo_concepto.setText("Renta liquida gravable 2024")
    dialog.campo_ingresos_brutos.setText("100000000.00")
    dialog.campo_devoluciones.setText("0.00")
    dialog.campo_costos.setText("40000000.00")
    dialog.campo_deducciones.setText("20000000.00")
    dialog.campo_rentas_exentas.setText("5000000.00")
    dialog.campo_fecha_origen.setDate(date(2024, 3, 1))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.categoria == "RENTA_LIQUIDA"
    assert guardada.ingresos_brutos == Decimal("100000000.00")
    assert guardada.rentas_exentas == Decimal("5000000.00")
    session.close()


def test_campos_de_sancion_ocultos_al_elegir_impuesto_a_cargo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="TRIBUTARIO")
    qtbot.addWidget(dialog)
    dialog.show()
    indice = dialog.combo_categoria.findData("IMPUESTO_A_CARGO")
    dialog.combo_categoria.setCurrentIndex(indice)

    assert dialog.campo_valor.isVisible()
    assert not dialog.campo_base_sancion.isVisible()
    assert not dialog.campo_ingresos_brutos.isVisible()


def test_campos_anatocismo_visibles_solo_para_comercial_puntual(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_anatocismo_demanda_judicial.isVisible() is True
    assert dialog.check_anatocismo_acuerdo.isVisible() is True

    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    assert dialog.check_anatocismo_demanda_judicial.isVisible() is False
    assert dialog.check_anatocismo_acuerdo.isVisible() is False


def test_campos_anatocismo_ocultos_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_anatocismo_demanda_judicial.isVisible() is False
    assert dialog.check_anatocismo_acuerdo.isVisible() is False
    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is False


def test_campos_anatocismo_ocultos_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_anatocismo_demanda_judicial.isVisible() is False
    assert dialog.check_anatocismo_acuerdo.isVisible() is False


def test_campo_fecha_acuerdo_visible_solo_si_checkbox_marcado(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is False
    dialog.check_anatocismo_acuerdo.setChecked(True)
    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is True
    dialog.check_anatocismo_acuerdo.setChecked(False)
    assert dialog.campo_anatocismo_fecha_acuerdo.isVisible() is False


def test_guarda_obligacion_comercial_con_anatocismo_demanda_judicial(qtbot, monkeypatch):
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
    dialog.check_anatocismo_demanda_judicial.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.anatocismo_demanda_judicial is True
    assert guardada.anatocismo_fecha_acuerdo is None
    session.close()


def test_guarda_obligacion_comercial_con_anatocismo_acuerdo_posterior(qtbot, monkeypatch):
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
    dialog.check_anatocismo_acuerdo.setChecked(True)
    dialog.campo_anatocismo_fecha_acuerdo.setDate(date(2026, 2, 15))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.anatocismo_demanda_judicial is False
    assert guardada.anatocismo_fecha_acuerdo == date(2026, 2, 15)
    session.close()


def test_check_interes_sobre_capital_indexado_visible_solo_en_civil_familia(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_interes_sobre_capital_indexado.isVisible() is True

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(
        expediente_id=expediente_id_comercial, area="COMERCIAL"
    )
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.check_interes_sobre_capital_indexado.isVisible() is False


def test_guarda_obligacion_con_interes_sobre_capital_indexado_marcado(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)
    dialog.check_interes_sobre_capital_indexado.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.interes_sobre_capital_indexado is True
    session.close()


def test_guarda_obligacion_sin_marcar_interes_sobre_capital_indexado_queda_en_false(
    qtbot, monkeypatch
):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Dano emergente")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2024, 7, 1))
    dialog.check_aplica_indexacion_ipc.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.interes_sobre_capital_indexado is False
    session.close()


def test_comercial_con_ibc_invalido_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Capital de pagare")
    dialog.campo_valor.setText("1000000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 1, 1))
    dialog.campo_tasa_moratoria.setText("24.00")
    dialog.campo_ibc_vigente.setText("no es un numero")
    dialog.campo_fecha_vencimiento.setDate(date(2025, 2, 1))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_honorarios_con_beneficio_obtenido_invalido_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("20.00")
    dialog.campo_beneficio_obtenido.setText("no es un numero")

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_cuota_litis_fuera_de_rango_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("150.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_costas_pct_fuera_de_rango_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="HONORARIOS")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Honorarios proceso ejecutivo")
    dialog.campo_tasa.setText("0.00")
    dialog.campo_fecha_origen.setDate(date(2026, 1, 1))
    dialog.campo_honorarios_fijos.setText("1000000.00")
    dialog.campo_cuota_litis_pct.setText("20.00")
    dialog.campo_beneficio_obtenido.setText("10000000.00")
    dialog.campo_costas_pct.setText("-5.00")

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_tasa_efectiva_negativa_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("-1.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_tasa_efectiva_absurdamente_alta_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("99999.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_concepto_vacio_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("   ")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_fecha_origen_posterior_a_fecha_de_corte_lanza_error_de_validacion(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)  # fecha_corte_default = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("100000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2026, 7, 1))  # posterior al corte

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_fecha_inicio_recurrente_posterior_a_fecha_de_corte_lanza_error_de_validacion(
    qtbot, monkeypatch
):
    expediente_id = _expediente_de_prueba(monkeypatch)  # fecha_corte_default = 2026-06-01

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Cuota alimentaria")
    dialog.campo_valor.setText("500000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 7, 1))  # posterior al corte
    dialog.campo_dia_pago.setValue(5)

    import pytest

    with pytest.raises(ValueError):
        dialog.guardar()


def test_boton_guardar_tiene_icono_y_clase_primaria(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_grupo_datos_basicos_siempre_visible(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.grupo_datos_basicos.isVisible() is True


def test_grupo_tasas_intereses_oculto_para_laboral_y_tributario(qtbot, monkeypatch):
    # Sprint 43: LABORAL ya NO oculta el grupo completo -- ahora lo necesita para el
    # checkbox "Aplica indexación IPC" (todos los demas campos del grupo siguen
    # ocultos individualmente para esta area, ver
    # test_check_indexacion_visible_en_las_5_areas_con_checkbox_manual). TRIBUTARIO
    # sigue oculto: ahi IPC es automatico, sin checkbox.
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_laboral.show()
    assert dialog_laboral.grupo_tasas_intereses.isVisible() is True
    assert dialog_laboral.check_aplica_indexacion_ipc.isVisible() is True

    expediente_id_tributario = _expediente_de_prueba(monkeypatch, area=AreaDerecho.TRIBUTARIO)
    dialog_tributario = ObligacionFormDialog(
        expediente_id=expediente_id_tributario, area="TRIBUTARIO"
    )
    qtbot.addWidget(dialog_tributario)
    dialog_tributario.show()
    assert dialog_tributario.grupo_tasas_intereses.isVisible() is False

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(
        expediente_id=expediente_id_comercial, area="COMERCIAL"
    )
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.grupo_tasas_intereses.isVisible() is True


def test_grupo_honorarios_costas_visible_solo_para_esa_area(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.grupo_honorarios_costas.isVisible() is False

    expediente_id_honorarios = _expediente_de_prueba(monkeypatch, area=AreaDerecho.HONORARIOS)
    dialog_honorarios = ObligacionFormDialog(
        expediente_id=expediente_id_honorarios, area="HONORARIOS"
    )
    qtbot.addWidget(dialog_honorarios)
    dialog_honorarios.show()
    assert dialog_honorarios.grupo_honorarios_costas.isVisible() is True


def test_grupo_datos_basicos_es_colapsable_y_conserva_los_datos_al_colapsar(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.campo_concepto.setText("Gastos medicos")

    dialog.grupo_datos_basicos.setChecked(False)

    assert dialog.campo_concepto.isVisible() is False
    assert dialog.campo_concepto.text() == "Gastos medicos"

    dialog.grupo_datos_basicos.setChecked(True)
    assert dialog.campo_concepto.isVisible() is True


@pytest.mark.parametrize("area", list(AreaDerecho))
def test_grid_de_secciones_tiene_2_columnas_y_boton_fuera_del_scroll(qtbot, monkeypatch, area):
    """Sprint 72: "Datos basicos" y "Tasas e intereses" quedan lado a lado (misma
    fila, columnas distintas) en vez de apiladas verticalmente, para que el
    dialogo no crezca tanto en alto que "Guardar" quede fuera de la vista.
    "Honorarios y costas" queda debajo de "Datos basicos", en su misma columna
    (solo ocupa espacio cuando el area es Honorarios). El grid vive dentro de
    `area_desplazable_secciones` (un QScrollArea, agregado tras code review de
    Sprint 72: ver el comentario junto a su construccion en obligaciones.py) --
    "Guardar" queda FUERA de ese QScrollArea, en el QVBoxLayout externo del
    dialogo, para permanecer siempre visible sin importar la posicion del
    scroll. Parametrizado sobre las 6 areas porque la combinacion de filas/
    columnas visibles varia por area (ej. Honorarios es la unica con las 3
    secciones visibles a la vez)."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=area)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area=area.value)
    qtbot.addWidget(dialog)

    grid = dialog.area_desplazable_secciones.widget().layout()
    assert isinstance(grid, QGridLayout)

    fila_datos, columna_datos, _, _ = grid.getItemPosition(
        grid.indexOf(dialog.grupo_datos_basicos)
    )
    fila_tasas, columna_tasas, _, _ = grid.getItemPosition(
        grid.indexOf(dialog.grupo_tasas_intereses)
    )
    fila_honorarios, columna_honorarios, _, _ = grid.getItemPosition(
        grid.indexOf(dialog.grupo_honorarios_costas)
    )

    # Datos basicos y Tasas e intereses: misma fila, columna distinta (lado a lado).
    assert fila_datos == fila_tasas
    assert columna_datos != columna_tasas

    # Honorarios y costas: debajo de Datos basicos, en su misma columna.
    assert columna_honorarios == columna_datos
    assert fila_honorarios != fila_datos

    # El boton Guardar no vive en el grid -- queda en el layout externo del dialogo.
    assert grid.indexOf(dialog.boton_guardar) == -1
    layout_externo = dialog.layout()
    assert layout_externo.indexOf(dialog.boton_guardar) != -1
    assert layout_externo.indexOf(dialog.area_desplazable_secciones) != -1


@pytest.mark.parametrize("area", list(AreaDerecho))
def test_dialogo_mantiene_tamano_fijo_bajo_1366x768_tras_mostrarse(qtbot, monkeypatch, area):
    """Sprint 72 (fix tras code review): un `self.resize(...)` solo fija el
    tamaño ANTES de que Qt active el layout -- una vez el dialogo se muestra de
    verdad via `.show()`/`.exec()` (como lo invoca expediente_detalle.py:390 y
    :413, el unico call site real), Qt recalculaba el ancho minimo del
    QGridLayout con "Datos basicos" y "Tasas e intereses" lado a lado y lo
    sobreescribia -- 4 de las 6 areas (incluida CIVIL_FAMILIA, la de por
    defecto) terminaban mas anchas que 1366px. El fix envuelve el grid en un
    QScrollArea (`area_desplazable_secciones`), que desacopla el tamaño minimo
    del contenido del tamaño minimo del dialogo -- el contenido que no quepa
    se desplaza en vez de agrandar la ventana. Se verifica llamando a
    `.show()` + `qtbot.waitExposed(...)` (no solo construyendo el dialogo, que
    no dispara la activacion real del layout) y parametrizado sobre las 6
    areas -- antes del fix, solo LABORAL y TRIBUTARIO se mantenian dentro del
    tamaño fijado."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=area)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area=area.value)
    qtbot.addWidget(dialog)

    dialog.show()
    qtbot.waitExposed(dialog)

    assert dialog.size().width() <= 1366
    assert dialog.size().height() <= 768

    # El boton Guardar esta visible y dentro del area del dialogo, sin importar
    # cuanto contenido tenga esa area dentro del QScrollArea.
    assert dialog.boton_guardar.isVisible() is True
    esquina_inferior_boton = dialog.boton_guardar.mapTo(
        dialog, dialog.boton_guardar.rect().bottomRight()
    )
    assert esquina_inferior_boton.y() <= dialog.size().height()


def test_campo_tasa_tiene_tooltip_legal(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    assert dialog.campo_tasa.toolTip() != ""


def test_campo_tasa_muestra_icono_informativo_del_valor_por_defecto(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    etiquetas_info = [
        hijo
        for hijo in dialog._contenedor_campo_tasa.findChildren(QLabel)
        if hijo.toolTip() == "Valor por defecto: interés civil legal, Art. 1617 C.C."
    ]
    assert len(etiquetas_info) == 1


def test_campos_no_autoexplicativos_tienen_tooltip(qtbot, monkeypatch):
    """Sprint 59: cada campo del formulario que captura un dato juridico o
    financiero no obvio (tasas, fechas de corte, unidades, tipos) debe tener
    un tooltip explicativo -- excluye campos autoexplicativos como
    "Concepto" (texto libre) que ya se verifican en otros tests."""
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)

    campos_con_tooltip_esperado = [
        "combo_tipo",
        "combo_categoria",
        "campo_fecha_origen",
        "campo_fecha_inicio",
        "campo_dia_pago",
        "combo_tipo_reajuste_anual",
        "campo_base_sancion",
        "campo_meses_extemporaneidad",
        "check_sancion_agravada",
        "campo_ingresos_brutos",
        "campo_devoluciones",
        "campo_costos",
        "campo_deducciones",
        "campo_rentas_exentas",
        "campo_fecha_fin",
        "check_pagada",
        "campo_fecha_pago_total",
        "check_incluir_seguridad_social",
        "campo_fecha_vencimiento",
        "check_anatocismo_acuerdo",
        "campo_anatocismo_fecha_acuerdo",
        "combo_moneda",
        "campo_trm_fecha_referencia",
        "campo_honorarios_fijos",
        "campo_beneficio_obtenido",
    ]
    for nombre_campo in campos_con_tooltip_esperado:
        widget = getattr(dialog, nombre_campo)
        assert widget.toolTip() != "", f"{nombre_campo} deberia tener un tooltip"


def test_concepto_vacio_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_concepto.setText("Gastos medicos")
    assert dialog.campo_concepto.property("class") != "invalid"

    dialog.campo_concepto.setText("   ")
    assert dialog.campo_concepto.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_concepto].isVisible() is True

    dialog.campo_concepto.setText("Gastos medicos otra vez")
    assert dialog.campo_concepto.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_concepto].isVisible() is False


def test_valor_negativo_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_valor.setText("-100.00")

    assert dialog.campo_valor.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_valor].isVisible() is True

    dialog.campo_valor.setText("100.00")
    assert dialog.campo_valor.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_valor].isVisible() is False


def test_tasa_fuera_de_rango_se_marca_invalida_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_tasa.setText("99999.00")

    assert dialog.campo_tasa.property("class") == "invalid"
    assert dialog._iconos_advertencia[dialog.campo_tasa].isVisible() is True

    dialog.campo_tasa.setText("6.00")
    assert dialog.campo_tasa.property("class") != "invalid"
    assert dialog._iconos_advertencia[dialog.campo_tasa].isVisible() is False


def test_tasa_no_numerica_se_marca_invalida_en_tiempo_real(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_tasa.setText("abc")

    assert dialog.campo_tasa.property("class") == "invalid"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("427900.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.concepto == "Gastos medicos"
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Gastos medicos")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    cantidad = session.query(Obligacion).filter_by(expediente_id=expediente_id).count()
    assert cantidad == 0
    session.close()


def test_enter_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id)
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    dialog.campo_concepto.setText("Gastos medicos")
    dialog.campo_valor.setText("427900.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_origen.setDate(date(2025, 11, 20))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Return)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.concepto == "Gastos medicos"
    session.close()


def test_orden_de_tabulacion_sigue_el_orden_visual_para_civil_familia(qtbot, monkeypatch):
    # Caso representativo (CIVIL_FAMILIA, tipo PUNTUAL por defecto): de los ~35 campos
    # del formulario (repartido en 3 QGroupBox colapsables, Sprint 34), solo estos
    # quedan visibles -- el resto son especificos de otras areas (Comercial,
    # Sancionatorio, Honorarios, Laboral, Tributario) y Qt salta automaticamente los
    # widgets no visibles al tabular, siguiendo el orden estatico configurado.
    expediente_id = _expediente_de_prueba(monkeypatch)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    orden_esperado = [
        dialog.combo_tipo,
        dialog.combo_categoria,
        dialog.campo_concepto,
        dialog.campo_valor,
        dialog.campo_fecha_origen,
        dialog.campo_tasa,
        dialog.check_aplica_indexacion_ipc,
        dialog.check_interes_sobre_capital_indexado,
        dialog.boton_guardar,
    ]

    orden_esperado[0].setFocus()
    qtbot.wait(20)
    assert dialog.focusWidget() is orden_esperado[0]

    for widget_esperado in orden_esperado[1:]:
        qtbot.keyClick(dialog, Qt.Key.Key_Tab)
        assert dialog.focusWidget() is widget_esperado


def test_sancionatorio_sin_labels_huerfanas_valor_y_nivel_riesgo_arl(qtbot, monkeypatch):
    """Definicion de Hecho del Sprint 39: en area SANCIONATORIO, 'Valor' y
    'Nivel de riesgo ARL' (los 2 casos originalmente reportados) no deben
    quedar como filas huerfanas -- ni ellos ni ningun otro campo del
    formulario."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.SANCIONATORIO)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="SANCIONATORIO")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_valor.isVisible() is False
    assert dialog.combo_nivel_riesgo_arl.isVisible() is False

    assert _filas_con_etiqueta_huerfana(dialog.layout_datos_basicos) == []
    assert _filas_con_etiqueta_huerfana(dialog.layout_tasas_intereses) == []
    assert _filas_con_etiqueta_huerfana(dialog.layout_honorarios_costas) == []


def test_civil_familia_puntual_sin_labels_huerfanas(qtbot, monkeypatch):
    """Ningun campo no aplicable a CIVIL_FAMILIA/Puntual (ej. 'Fecha de inicio
    (Recurrente)', 'Dia de pago (Recurrente)', los campos de Sancionatorio,
    Honorarios, Tributario y Laboral) debe dejar su etiqueta visible sin su
    widget."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.combo_tipo.setCurrentIndex(0)  # Puntual

    assert _filas_con_etiqueta_huerfana(dialog.layout_datos_basicos) == []
    assert _filas_con_etiqueta_huerfana(dialog.layout_tasas_intereses) == []
    assert _filas_con_etiqueta_huerfana(dialog.layout_honorarios_costas) == []


def test_sin_labels_huerfanas_en_cada_area_y_categoria_tributaria(qtbot, monkeypatch):
    """Barrido amplio (Sprint 39): ninguna combinacion de area (y, para
    TRIBUTARIO, de categoria) deja una fila huerfana en ninguno de los 3
    QFormLayout del dialogo."""
    for area in (
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "SANCIONATORIO",
        "HONORARIOS",
        "LABORAL",
        "TRIBUTARIO",
    ):
        area_derecho = getattr(AreaDerecho, area)
        expediente_id = _expediente_de_prueba(monkeypatch, area=area_derecho)

        dialog = ObligacionFormDialog(expediente_id=expediente_id, area=area)
        qtbot.addWidget(dialog)
        dialog.show()

        if area == "TRIBUTARIO":
            for indice_categoria in range(dialog.combo_categoria.count()):
                dialog.combo_categoria.setCurrentIndex(indice_categoria)
                assert _filas_con_etiqueta_huerfana(dialog.layout_datos_basicos) == [], (
                    f"area={area} categoria={dialog.combo_categoria.currentData()}"
                )
        else:
            assert _filas_con_etiqueta_huerfana(dialog.layout_datos_basicos) == [], f"area={area}"

        assert _filas_con_etiqueta_huerfana(dialog.layout_tasas_intereses) == [], f"area={area}"
        assert _filas_con_etiqueta_huerfana(dialog.layout_honorarios_costas) == [], f"area={area}"


# --- Sprint 44, punto 1: salario = SMMLV automatico -------------------------


def test_check_es_smmlv_visible_solo_para_area_laboral(qtbot, monkeypatch):
    expediente_id_laboral = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    dialog_laboral = ObligacionFormDialog(expediente_id=expediente_id_laboral, area="LABORAL")
    qtbot.addWidget(dialog_laboral)
    dialog_laboral.show()
    assert dialog_laboral.check_es_smmlv.isVisible() is True

    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_es_smmlv.isVisible() is False


def test_campo_valor_se_oculta_al_marcar_es_smmlv_en_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.campo_valor.isVisible() is True
    dialog.check_es_smmlv.setChecked(True)
    assert dialog.campo_valor.isVisible() is False
    dialog.check_es_smmlv.setChecked(False)
    assert dialog.campo_valor.isVisible() is True


def test_guarda_obligacion_laboral_con_es_smmlv_resuelve_el_valor(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
    session = session_module.get_session()
    from database.models import ParametroLegal

    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1300000.00"),
            vigente_desde=date(2024, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.commit()
    session.close()

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_fecha_origen.setDate(date(2024, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2024, 12, 31))
    dialog.check_es_smmlv.setChecked(True)

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.es_smmlv is True
    assert guardada.valor == Decimal("1300000.00")
    session.close()


def test_guarda_obligacion_laboral_sin_es_smmlv_por_defecto(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="LABORAL")
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Liquidacion de contrato")
    dialog.campo_valor.setText("3000000.00")
    dialog.campo_fecha_origen.setDate(date(2020, 1, 1))
    dialog.campo_fecha_fin.setDate(date(2020, 12, 31))

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.es_smmlv is False
    session.close()


# --- Sprint 44, punto 2: edicion de una obligacion ya guardada --------------


def test_obligacion_id_titulo_del_dialogo_dice_editar(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
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

    dialog = ObligacionFormDialog(expediente_id=expediente_id, obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert dialog.windowTitle() == "Editar obligacion"


def test_obligacion_id_precarga_los_campos_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
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

    dialog = ObligacionFormDialog(expediente_id=expediente_id, obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert dialog.campo_concepto.text() == "Gastos medicos"
    assert dialog.campo_valor.text() == "427900.00"
    # tasa_efectiva_anual es Numeric(9, 4) -- vuelve de la BD con 4 decimales
    # (6.0000), no los 2 originalmente digitados (6.00).
    assert Decimal(dialog.campo_tasa.text()) == Decimal("6.00")
    assert dialog.campo_fecha_origen.date().toPython() == date(2025, 11, 20)


def test_obligacion_id_precarga_el_reajuste_anual_recurrente(qtbot, monkeypatch):
    # Hallazgo de una prueba practica del despacho: el combo de reajuste anual
    # nunca se precargaba al editar -- siempre mostraba "Ninguno" (su primer
    # item) sin importar el valor real guardado, aunque el guardado en si
    # funcionaba bien (ver test_guarda_obligacion_recurrente_civil_familia_con_reajuste_smmlv).
    expediente_id = _expediente_de_prueba(monkeypatch)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        dia_pago=5,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(expediente_id=expediente_id, obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo_reajuste_anual.currentData() == "SMMLV"


def test_reguardar_una_obligacion_editada_no_revierte_el_reajuste_anual(qtbot, monkeypatch):
    # Complemento del test anterior: sin la precarga, volver a guardar una
    # obligacion editada (sin tocar el combo de reajuste) revertia
    # silenciosamente tipo_reajuste_anual a NINGUNO en la base de datos --
    # porque guardar() siempre lee el valor actual del combo. Este test
    # verifica el escenario completo end-to-end: guardar de nuevo debe
    # preservar el SMMLV ya guardado.
    expediente_id = _expediente_de_prueba(monkeypatch)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        dia_pago=5,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(expediente_id=expediente_id, obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert guardada.tipo_reajuste_anual == TipoReajusteAnual.SMMLV
    session.close()


def test_obligacion_id_precarga_fecha_de_pago_real_en_laboral(qtbot, monkeypatch):
    # Motivo original del hallazgo (Sprint 44): "fecha de pago real" quedaba
    # inaccesible una vez guardada la obligacion porque no habia forma de
    # editarla -- este test confirma que ahora se precarga correctamente.
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
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
        pagada=True,
        fecha_pago_total=date(2021, 1, 15),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(
        expediente_id=expediente_id,
        area="LABORAL",
        obligacion_id=obligacion_id,
    )
    qtbot.addWidget(dialog)
    dialog.show()

    assert dialog.check_pagada.isChecked() is True
    assert dialog.campo_fecha_pago_total.isVisible() is True
    assert dialog.campo_fecha_pago_total.date().toPython() == date(2021, 1, 15)


def test_guardar_con_obligacion_id_actualiza_en_vez_de_crear_una_nueva(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Original",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(expediente_id=expediente_id, obligacion_id=obligacion_id)
    qtbot.addWidget(dialog)
    dialog.campo_concepto.setText("Editado")
    dialog.campo_valor.setText("200000.00")

    id_devuelto = dialog.guardar()

    assert id_devuelto == obligacion_id
    session = session_module.get_session()
    assert session.query(Obligacion).count() == 1  # no se creo una fila nueva
    actualizada = session.get(Obligacion, obligacion_id)
    assert actualizada.concepto == "Editado"
    assert actualizada.valor == Decimal("200000.00")
    session.close()


def test_guardar_con_obligacion_id_laboral_actualiza_en_vez_de_crear_una_nueva(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.LABORAL)
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

    dialog = ObligacionFormDialog(
        expediente_id=expediente_id,
        area="LABORAL",
        obligacion_id=obligacion_id,
    )
    qtbot.addWidget(dialog)
    dialog.check_pagada.setChecked(True)
    dialog.campo_fecha_pago_total.setDate(date(2021, 2, 1))

    id_devuelto = dialog.guardar()

    assert id_devuelto == obligacion_id
    session = session_module.get_session()
    assert session.query(Obligacion).count() == 1
    actualizada = session.get(Obligacion, obligacion_id)
    assert actualizada.pagada is True
    assert actualizada.fecha_pago_total == date(2021, 2, 1)


# --- Sprint 73: obligaciones RECURRENTE con fechas anuales fijas ------------


def test_combo_tipo_recurrencia_visible_solo_para_recurrente_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.combo_tipo.setCurrentIndex(0)  # PUNTUAL
    assert dialog.combo_tipo_recurrencia.isVisible() is False

    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    assert dialog.combo_tipo_recurrencia.isVisible() is True


def test_combo_tipo_recurrencia_oculto_para_comercial_recurrente(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="COMERCIAL")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE

    assert dialog.combo_tipo_recurrencia.isVisible() is False


def test_campo_fechas_anuales_fijas_visible_solo_cuando_tipo_recurrencia_lo_es(
    qtbot, monkeypatch
):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE

    indice_mensual = dialog.combo_tipo_recurrencia.findData("MENSUAL")
    dialog.combo_tipo_recurrencia.setCurrentIndex(indice_mensual)
    assert dialog.campo_fechas_anuales_fijas.isVisible() is False

    indice_fechas_fijas = dialog.combo_tipo_recurrencia.findData("FECHAS_ANUALES_FIJAS")
    dialog.combo_tipo_recurrencia.setCurrentIndex(indice_fechas_fijas)
    assert dialog.campo_fechas_anuales_fijas.isVisible() is True


def test_guarda_obligacion_recurrente_fechas_anuales_fijas_gastos_vestuario(qtbot, monkeypatch):
    """Definicion de Hecho del Sprint 73 (extremo de captura): una obligacion
    de "gastos de vestuario" con 3 fechas anuales fijas (junio, diciembre, y
    el "cumpleanos" del beneficiario, ingresado a mano como una entrada MM-DD
    mas -- ver limitacion documentada en TipoRecurrencia, Sprint 74 todavia no
    implementado) se guarda con tipo_recurrencia FECHAS_ANUALES_FIJAS y la
    lista de fechas serializada."""
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Gastos de vestuario")
    dialog.campo_valor.setText("150000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 1, 1))
    indice_fechas_fijas = dialog.combo_tipo_recurrencia.findData("FECHAS_ANUALES_FIJAS")
    dialog.combo_tipo_recurrencia.setCurrentIndex(indice_fechas_fijas)
    # Cumpleanos del beneficiario (23 de marzo) entrado a mano, junto con
    # junio y diciembre -- exactamente el caso del reporte del usuario.
    dialog.campo_fechas_anuales_fijas.setText("06-15, 12-15, 03-23")

    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    assert guardada.tipo == TipoObligacion.RECURRENTE
    assert guardada.tipo_recurrencia == TipoRecurrencia.FECHAS_ANUALES_FIJAS
    assert deserializar_fechas_anuales(guardada.fechas_anuales_fijas) == [
        "06-15",
        "12-15",
        "03-23",
    ]
    session.close()


def test_guarda_obligacion_recurrente_civil_familia_sin_tocar_recurrencia_queda_mensual(
    qtbot, monkeypatch
):
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
    assert guardada.tipo_recurrencia == TipoRecurrencia.MENSUAL
    assert guardada.fechas_anuales_fijas is None
    session.close()


def test_guardar_fechas_anuales_fijas_con_lista_vacia_lanza_error_de_validacion(
    qtbot, monkeypatch
):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialog.campo_concepto.setText("Gastos de vestuario")
    dialog.campo_valor.setText("150000.00")
    dialog.campo_tasa.setText("6.00")
    dialog.campo_fecha_inicio.setDate(date(2026, 1, 1))
    indice_fechas_fijas = dialog.combo_tipo_recurrencia.findData("FECHAS_ANUALES_FIJAS")
    dialog.combo_tipo_recurrencia.setCurrentIndex(indice_fechas_fijas)
    dialog.campo_fechas_anuales_fijas.setText("")

    with pytest.raises(ValueError, match="al menos una fecha"):
        dialog.guardar()


def test_obligacion_id_precarga_tipo_recurrencia_y_fechas_anuales_fijas(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Gastos de vestuario",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas='["06-15", "12-15", "03-23"]',
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(
        expediente_id=expediente_id, area="CIVIL_FAMILIA", obligacion_id=obligacion_id
    )
    qtbot.addWidget(dialog)

    assert dialog.combo_tipo_recurrencia.currentData() == "FECHAS_ANUALES_FIJAS"
    assert dialog.campo_fechas_anuales_fijas.text() == "06-15, 12-15, 03-23"


def test_reguardar_fechas_anuales_fijas_editada_no_las_revierte_a_mensual(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    session = session_module.get_session()
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Gastos de vestuario",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas='["06-15", "12-15", "03-23"]',
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    dialog = ObligacionFormDialog(
        expediente_id=expediente_id, area="CIVIL_FAMILIA", obligacion_id=obligacion_id
    )
    qtbot.addWidget(dialog)
    dialog.guardar()

    session = session_module.get_session()
    guardada = session.query(Obligacion).filter_by(id=obligacion_id).one()
    assert guardada.tipo_recurrencia == TipoRecurrencia.FECHAS_ANUALES_FIJAS
    assert deserializar_fechas_anuales(guardada.fechas_anuales_fijas) == [
        "06-15",
        "12-15",
        "03-23",
    ]
    session.close()


def test_civil_familia_recurrente_fechas_fijas_sin_labels_huerfanas(qtbot, monkeypatch):
    expediente_id = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)

    dialog = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog)
    dialog.show()
    dialog.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    indice_fechas_fijas = dialog.combo_tipo_recurrencia.findData("FECHAS_ANUALES_FIJAS")
    dialog.combo_tipo_recurrencia.setCurrentIndex(indice_fechas_fijas)

    assert _filas_con_etiqueta_huerfana(dialog.layout_datos_basicos) == []
