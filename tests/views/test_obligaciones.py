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


def test_check_indexacion_visible_solo_en_civil_familia(qtbot, monkeypatch):
    expediente_id_civil = _expediente_de_prueba(monkeypatch, area=AreaDerecho.CIVIL_FAMILIA)
    dialog_civil = ObligacionFormDialog(expediente_id=expediente_id_civil, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialog_civil)
    dialog_civil.show()
    assert dialog_civil.check_aplica_indexacion_ipc.isVisible() is True

    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
    qtbot.addWidget(dialog_comercial)
    dialog_comercial.show()
    assert dialog_comercial.check_aplica_indexacion_ipc.isVisible() is False


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

    etiqueta_laboral = dialog_laboral.layout_formulario.labelForField(dialog_laboral.campo_fecha_origen).text()
    etiqueta_civil = dialog_civil.layout_formulario.labelForField(dialog_civil.campo_fecha_origen).text()

    assert etiqueta_laboral != etiqueta_civil
    assert etiqueta_laboral == "Fecha de inicio del contrato"
    assert etiqueta_civil == "Fecha de origen (Puntual)"


def test_combo_moneda_visible_solo_para_area_comercial(qtbot, monkeypatch):
    expediente_id_comercial = _expediente_de_prueba(monkeypatch, area=AreaDerecho.COMERCIAL)
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
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
    dialog_comercial = ObligacionFormDialog(expediente_id=expediente_id_comercial, area="COMERCIAL")
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


def test_guarda_obligacion_sin_marcar_interes_sobre_capital_indexado_queda_en_false(qtbot, monkeypatch):
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
