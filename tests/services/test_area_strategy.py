from datetime import date as _date
from datetime import datetime as _dt
from decimal import Decimal as _Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.engine.indexation.historical_index import (
    _IPC_INDICE_ACUMULADO,
    _SMLMV_POR_ANIO,
    _TRAMOS_IBC_USURA,
    _UVT_POR_ANIO,
)
from app.engine.liquidation.registry import AreaRegistry
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
    TributarioStrategy,
)
from database.models import Base, ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria(monkeypatch):
    # Fixture autouse global para todo el archivo: TestComercialStrategy ya
    # depende de calcular_tope_usura (Tarea 7, corregido Sprint 2), que ahora lee USURA_MULTIPLICADOR
    # via parametro_service en cada liquidar() -- si esta fixture solo sembrara
    # las claves de Honorarios, todos los tests de Comercial de este archivo
    # fallarian con ParametroNoDisponibleError. Se siembran aqui las claves
    # que cualquier test de este archivo puede necesitar. Valores/fechas de
    # USURA_MULTIPLICADOR calcados de tests/engine/test_usury_validator.py
    # (la fixture equivalente de la Tarea 7) para no divergir del valor real
    # sembrado en bastium.db por scripts/migrate_parametros_legales.py.
    #
    # SMLMV/IPC_INDICE_ACUMULADO (Tarea 12): SancionatorioStrategy (via
    # resolver_base_sancion -> get_smlmv_for_year) y CivilFamiliaStrategy (via
    # get_ipc_interpolado_for_date) ahora leen ambas claves de
    # parametro_service en cada liquidar(). Se siembran desde los mismos
    # diccionarios congelados que consume scripts/migrate_parametros_legales.py
    # (no se re-transcriben a mano) para no divergir del dato real y para no
    # tener que enumerar a mano que anios especificos necesita cada test.
    #
    # IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO (Tarea 13): LaboralStrategy
    # (via MoratoryIndemnityCalculator.calcular -> get_ibc_usura_for_date) ahora
    # lee ambas claves de parametro_service por dia de mora. Se siembran desde
    # la misma tabla congelada _TRAMOS_IBC_USURA que consume
    # scripts/migrate_parametros_legales.py, mismo criterio que SMLMV/IPC arriba.
    #
    # UVT (Tarea 14): SancionatorioStrategy (via resolver_base_sancion ->
    # get_uvt_for_year) ahora resuelve hechos posteriores a 2020-01-01 contra
    # la tabla historica de UVT en vez de lanzar UVTNoDisponibleError siempre.
    # Se siembra igual que SMLMV/IPC/IBC arriba, desde el mismo diccionario
    # congelado _UVT_POR_ANIO que consume scripts/migrate_parametros_legales.py.
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="USURA_MULTIPLICADOR", valor=_Decimal("1.5"), vigente_desde=_date(1997, 7, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="HONORARIOS_TOTAL_PCT", valor=_Decimal("50"), vigente_desde=_date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    for anio, valor in _SMLMV_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="SMLMV", valor=valor, vigente_desde=_date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for anio, valor in _UVT_POR_ANIO.items():
        session.add(ParametroLegal(
            clave="UVT", valor=valor, vigente_desde=_date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for clave, valor in {
        "EXTEMPORANEIDAD_PCT_MENSUAL": Decimal("5"),
        "INEXACTITUD_PCT": Decimal("160"),
        "INEXACTITUD_AGRAVADA_PCT": Decimal("200"),
        "ERROR_ARITMETICO_PCT": Decimal("30"),
        # ET635_PUNTOS_DESCUENTO (Sprint 15): faltaba en esta fixture porque ningun test de
        # TributarioStrategy anterior a la correccion del Art. 867-1 tenia mora real (todos
        # usaban fecha_corte == fecha_origen) -- construir_rate_provider_moratorio_tributario
        # nunca llegaba a leer esta clave. Los tests nuevos de mora > 3 anios si la necesitan.
        "ET635_PUNTOS_DESCUENTO": Decimal("2"),
    }.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=_date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for tramo in _TRAMOS_IBC_USURA:
        session.add(ParametroLegal(
            clave="IBC_CONSUMO_ORDINARIO", valor=tramo.ibc_anual, vigente_desde=tramo.inicio,
            vigente_hasta=tramo.fin, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
        session.add(ParametroLegal(
            clave="USURA_CONSUMO_ORDINARIO", valor=tramo.usura_anual, vigente_desde=tramo.inicio,
            vigente_hasta=tramo.fin, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.add(ParametroLegal(
        clave="SS_PENSION_PCT", valor=_Decimal("0.16"), vigente_desde=_date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    session.add(ParametroLegal(
        clave="SS_SALUD_PCT", valor=_Decimal("0.125"), vigente_desde=_date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
    ))
    for nivel, valor in {
        "I": _Decimal("0.00522"), "II": _Decimal("0.01044"), "III": _Decimal("0.02436"),
        "IV": _Decimal("0.04350"), "V": _Decimal("0.06960"),
    }.items():
        session.add(ParametroLegal(
            clave=f"SS_ARL_NIVEL_{nivel}_PCT", valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for i, valor in enumerate(
        [_Decimal("0.01"), _Decimal("0.012"), _Decimal("0.014"), _Decimal("0.016"),
         _Decimal("0.018"), _Decimal("0.02")], start=1
    ):
        session.add(ParametroLegal(
            clave=f"SS_FSP_TRAMO_{i}_PCT", valor=valor, vigente_desde=_date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def test_registry_expone_las_6_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
        "TRIBUTARIO",
    }


def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


from datetime import date, timedelta
from decimal import Decimal

from database.models import Abono, Obligacion, TipoObligacion


def _obligacion_puntual(expediente_id=1, valor=Decimal("427900.00")):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=valor,
        tasa_efectiva_anual=Decimal("6.00"),
    )


def test_civil_familia_liquida_una_obligacion_puntual_sin_abonos():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    # NOTA: `LiquidationResult.total_interest_accrued()` solo suma los items cuyo
    # `event_type` es explicitamente "INTEREST" (ver app/engine/liquidation/engine.py
    # LiquidationCore._process_event). El interes que se acumula dia a dia via
    # `_accrue_time_passage` NO pasa por ahi -- solo se refleja en `final_balance().interest`.
    # Verificado manualmente: para este mismo caso (427900.00 al 6% EA desde 2025-11-20
    # hasta 2026-01-01) el motor da total_interest_accrued() == 0.00 y
    # final_balance().interest == 2869.44. Por eso esta prueba verifica el saldo, no ese metodo.
    assert resultado.final_balance().principal == Decimal("427900.00")
    assert resultado.final_balance().interest > Decimal("0.00")
    assert resultado.total_payments_applied() == Decimal("0.00")


def test_civil_familia_aplica_un_abono_reduciendo_el_saldo():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()
    abono = Abono(
        id=1, obligacion_id=1, fecha=date(2025, 12, 1), monto=Decimal("100000.00"), referencia="ref-1"
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2026, 1, 1)
    )

    assert resultado.total_payments_applied() == Decimal("100000.00")
    assert resultado.final_balance().total() < obligacion.valor


def test_civil_familia_expande_obligacion_recurrente_en_cuotas_mensuales():
    strategy = CivilFamiliaStrategy()
    obligacion = Obligacion(
        id=2,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=date(2026, 3, 5),
    )

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 5)
    )

    # 3 cuotas de 500000 causadas: enero, febrero, marzo
    assert resultado.final_balance().principal == Decimal("1500000.00")


def test_civil_familia_puntual_sin_indexacion_no_genera_evento_indexation():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()  # aplica_indexacion_ipc no seteado -> falsy

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert all(item.balance.event_type != "INDEXATION" for item in resultado.items)
    assert resultado.final_balance().indexation == Decimal("0.00")


def test_civil_familia_puntual_con_indexacion_genera_evento_indexation_con_monto_correcto():
    obligacion = Obligacion(
        id=3,
        expediente_id=1,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 7, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = [item for item in resultado.items if item.balance.event_type == "INDEXATION"]
    assert len(eventos_indexacion) == 1
    # Calculado manualmente con get_ipc_interpolado_for_date(2024-07-01) y
    # get_ipc_interpolado_for_date(2025-12-31) via IPCIndexation.calculate --
    # 1,000,000 indexado de jul-2024 a dic-2025.
    assert eventos_indexacion[0].indexation_amount == Decimal("77633.53")
    assert eventos_indexacion[0].concept == "Indexación IPC — Dano emergente"
    assert resultado.final_balance().indexation == Decimal("77633.53")


def test_civil_familia_recurrente_con_indexacion_cada_cuota_indexa_desde_su_propia_fecha():
    obligacion = Obligacion(
        id=4,
        expediente_id=1,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2025, 1, 1),
        fecha_fin=date(2025, 2, 5),
        aplica_indexacion_ipc=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    eventos_indexacion = sorted(
        (item for item in resultado.items if item.balance.event_type == "INDEXATION"),
        key=lambda item: item.date,
    )
    # 2 cuotas (5-ene y 5-feb-2025), cada una con su propio monto de indexacion
    # porque cada una arranca a indexar desde una fecha distinta -- si ambas
    # dieran el mismo monto, seria señal de que se esta usando fecha_inicio de
    # la obligacion en vez de la fecha de cada cuota.
    assert len(eventos_indexacion) == 2
    assert eventos_indexacion[0].date == date(2025, 1, 5)
    assert eventos_indexacion[1].date == date(2025, 2, 5)
    assert eventos_indexacion[0].indexation_amount == Decimal("25133.13")
    assert eventos_indexacion[1].indexation_amount == Decimal("22869.89")
    assert eventos_indexacion[0].indexation_amount != eventos_indexacion[1].indexation_amount


def test_civil_familia_genera_evento_de_costas_si_esta_configurado():
    # valor = 123.500.000, fecha_origen forzada a 2024-06-01 (SMLMV 2024 =
    # 1.300.000.00): punto medio exacto del tier menor cuantia (52.000.000 a
    # 195.000.000) -> pct = 7% -> costas = 8.645.000,00. Mismo caso de
    # referencia usado en Tasks 4, 11, 13 y 14.
    obligacion = _obligacion_puntual(valor=_Decimal("123500000.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.tasa_efectiva_anual = _Decimal("0.00")
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = CivilFamiliaStrategy().liquidar(
        [obligacion], [], fecha_corte=obligacion.fecha_origen,
    )
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == _Decimal("132145000.00")  # 123.500.000 + 8.645.000


def test_civil_familia_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=101, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=102, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado_combinado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_b = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
    # El interes combinado debe ser exactamente la suma de cada obligacion liquidada con
    # su propia tasa por separado -- no depende de interacciones entre obligaciones porque
    # no hay abonos en este caso.
    interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
    assert resultado_combinado.final_balance().interest == interes_esperado
    # Si el bug de "toma la tasa de la primera obligacion para todo el expediente" siguiera
    # presente, el interes combinado seria 2 * interes_solo_a (ambas al 12%) en vez de la
    # suma de cada una a su propia tasa -- como B esta al doble de tasa que A, estos dos
    # valores son observablemente distintos, asi que esta asercion por si sola detecta el bug.
    assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest


def test_civil_familia_abono_de_una_obligacion_no_afecta_el_saldo_de_otra():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=103, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=104, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    abono_a = Abono(
        id=201, obligacion_id=103, fecha=date(2026, 1, 5), monto=Decimal("300000.00"), referencia="pago-a"
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[abono_a], fecha_corte=fecha_corte
    )
    resultado_solo_b_sin_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
    )
    resultado_solo_a_con_abono = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a], abonos=[abono_a], fecha_corte=fecha_corte
    )

    assert resultado.total_payments_applied() == Decimal("300000.00")
    # El interes de B no debe verse afectado por el abono registrado contra A: el interes
    # combinado debe ser exactamente A-con-abono + B-sin-abono, no una mezcla donde el abono
    # de A tambien reduce lo que B acumula.
    interes_esperado = (
        resultado_solo_a_con_abono.final_balance().interest + resultado_solo_b_sin_abono.final_balance().interest
    )
    assert resultado.final_balance().interest == interes_esperado


def test_civil_familia_abono_con_obligacion_id_ajeno_al_expediente_lanza_value_error():
    obligacion = _obligacion_puntual()
    abono_huerfano = Abono(
        id=202, obligacion_id=999, fecha=date(2025, 12, 1), monto=Decimal("1000.00"), referencia="huerfano"
    )

    with pytest.raises(ValueError):
        CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono_huerfano], fecha_corte=date(2026, 1, 1)
        )


def test_civil_familia_dos_obligaciones_producen_una_sola_fila_de_cierre_consolidada():
    fecha_corte = date(2026, 1, 11)
    obligacion_a = Obligacion(
        id=105, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("12.00"),
    )
    obligacion_b = Obligacion(
        id=106, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Obligacion B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2026, 1, 1),
        valor=Decimal("1000000.00"), tasa_efectiva_anual=Decimal("24.00"),
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
    )

    filas_de_cierre = [item for item in resultado.items if item.balance.event_type == "LIQUIDATION_CUTOFF"]
    assert len(filas_de_cierre) == 1
    assert resultado.final_balance().principal == Decimal("2000000.00")


from app.engine.liquidation.engine import LiquidationCore


def test_capital_concepts_incluye_los_codigos_comerciales_nuevos():
    core = LiquidationCore()
    assert "CAPITAL_LETRA_CAMBIO" in core._capital_concepts
    assert "CAPITAL_CHEQUE" in core._capital_concepts
    assert "CAPITAL_FACTURA" in core._capital_concepts


def test_capital_concepts_incluye_los_codigos_sancionatorio_y_honorarios():
    core = LiquidationCore()
    assert "MULTA_SANCIONATORIA" in core._capital_concepts
    assert "HONORARIOS_PROFESIONALES" in core._capital_concepts
    assert "COSTAS_PROCESALES" in core._capital_concepts


def test_capital_concepts_incluye_vacaciones():
    core = LiquidationCore()
    assert "VACACIONES" in core._capital_concepts


def test_capital_concepts_incluye_seguridad_social_e_incapacidad():
    core = LiquidationCore()
    assert "COTIZACION_PENSION" in core._capital_concepts
    assert "COTIZACION_SALUD" in core._capital_concepts
    assert "COTIZACION_ARL" in core._capital_concepts
    assert "COTIZACION_FSP" in core._capital_concepts
    assert "INCAPACIDAD_EMPLEADOR" in core._capital_concepts
    assert "SUSPENSION_INFORMATIVA" in core._capital_concepts
    assert "INCAPACIDAD_INFORMATIVA" in core._capital_concepts


def _obligacion_comercial(
    expediente_id=1,
    valor=Decimal("1000000.00"),
    tasa_remuneratoria=Decimal("6.00"),
    tasa_moratoria=Decimal("24.00"),
    ibc=Decimal("20.00"),
    fecha_origen=date(2025, 1, 1),
    fecha_vencimiento=date(2025, 2, 1),
    anatocismo_demanda_judicial=False,
    anatocismo_fecha_acuerdo=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=tasa_remuneratoria,
        tasa_moratoria_anual=tasa_moratoria,
        fecha_vencimiento=fecha_vencimiento,
        ibc_vigente_anual=ibc,
        anatocismo_demanda_judicial=anatocismo_demanda_judicial,
        anatocismo_fecha_acuerdo=anatocismo_fecha_acuerdo,
    )


class _TRMProviderDeCalendario:
    """Test double de TRMProvider (Sprint 12): retorna una TRM distinta por
    fecha exacta, para probar que la conversion es realmente dinamica -- nunca
    hace red."""

    def __init__(self, trm_por_fecha: dict):
        self._trm_por_fecha = trm_por_fecha

    def get_trm(self, fecha_referencia):
        return self._trm_por_fecha[fecha_referencia]


class TestComercialStrategy:
    def test_liquida_una_obligacion_puntual_sin_abonos(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("1000000.00")
        assert resultado.final_balance().interest > Decimal("0.00")
        assert resultado.total_payments_applied() == Decimal("0.00")

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        strategy = ComercialStrategy()
        obligacion = _obligacion_comercial()
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2025, 2, 15), monto=Decimal("200000.00"), referencia="ref-1"
        )

        resultado = strategy.liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.total_payments_applied() == Decimal("200000.00")
        assert resultado.final_balance().total() < obligacion.valor

    def test_usa_tasa_moratoria_tras_el_vencimiento_acumula_mas_interes_que_solo_remuneratoria(self):
        fecha_corte = date(2025, 3, 1)
        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        # Misma obligacion liquidada solo con la tasa remuneratoria (6%) durante todo el periodo,
        # via CivilFamiliaStrategy, que unicamente lee tasa_efectiva_anual.
        obligacion_solo_remuneratoria = _obligacion_comercial()
        resultado_solo_remuneratoria = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_solo_remuneratoria], abonos=[], fecha_corte=fecha_corte
        )

        # La obligacion vence 2025-02-01 y la tasa moratoria (24%) es mayor que la
        # remuneratoria (6%), asi que el interes acumulado en Comercial (que aplica la
        # moratoria desde el vencimiento) debe ser mayor que si se hubiera usado la
        # remuneratoria durante todo el periodo.
        assert resultado_comercial.final_balance().interest > resultado_solo_remuneratoria.final_balance().interest

    def test_sin_mora_usa_solo_tasa_remuneratoria(self):
        fecha_corte = date(2025, 1, 20)  # antes del vencimiento (2025-02-01)

        obligacion_comercial = _obligacion_comercial()
        resultado_comercial = ComercialStrategy().liquidar(
            obligaciones=[obligacion_comercial], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_civil = _obligacion_comercial()
        resultado_civil = CivilFamiliaStrategy().liquidar(
            obligaciones=[obligacion_civil], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_comercial.final_balance().interest == resultado_civil.final_balance().interest

    def test_tasa_moratoria_excede_tope_de_usura_no_lanza_error_y_aplica_sancion_doblada(self):
        # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 2): no se rechaza ni se
        # recorta la tasa silenciosamente. Se liquida con la tasa pactada, se calcula el
        # exceso de interes cobrado frente a la tasa de usura vigente, y se resta del saldo
        # el doble de ese exceso (sancion legal por usura, Ley 45/1990 art. 72).
        #
        # fecha_origen == fecha_vencimiento y tasa_remuneratoria == tasa_moratoria (35%): la
        # obligacion ya esta en mora desde el dia 1, asi que Comercial aplica una sola tasa
        # efectiva (35%) durante todo el periodo, igual que CivilFamiliaStrategy -- eso permite
        # verificar "Intereses_Cobrados" e "Intereses_Cobrados_Con_Tasa_Usura" con un motor
        # independiente (CivilFamiliaStrategy, que no aplica ninguna correccion de usura) en vez
        # de reutilizar el mecanismo interno de ComercialStrategy que se esta probando.
        fecha_corte = date(2025, 3, 1)
        fecha_origen = date(2025, 1, 1)
        obligacion_pactada = _obligacion_comercial(
            tasa_remuneratoria=Decimal("35.00"), tasa_moratoria=Decimal("35.00"), ibc=Decimal("20.00"),
            fecha_origen=fecha_origen, fecha_vencimiento=fecha_origen,
        )

        # Tope legal = 1.5 x 20 = 30%.
        intereses_cobrados = CivilFamiliaStrategy().liquidar(
            obligaciones=[_obligacion_comercial(
                tasa_remuneratoria=Decimal("35.00"), fecha_origen=fecha_origen, fecha_vencimiento=fecha_origen,
            )], abonos=[], fecha_corte=fecha_corte,
        ).final_balance().interest
        intereses_con_tasa_usura = CivilFamiliaStrategy().liquidar(
            obligaciones=[_obligacion_comercial(
                tasa_remuneratoria=Decimal("30.00"), fecha_origen=fecha_origen, fecha_vencimiento=fecha_origen,
            )], abonos=[], fecha_corte=fecha_corte,
        ).final_balance().interest

        exceso_esperado = intereses_cobrados - intereses_con_tasa_usura
        sancion_esperada = exceso_esperado * 2

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_pactada], abonos=[], fecha_corte=fecha_corte
        )

        item_sancion = resultado.items[-1]
        assert "usura" in item_sancion.concept.lower()
        assert item_sancion.interest_amount == -sancion_esperada
        assert resultado.final_balance().interest == intereses_cobrados - sancion_esperada

    def test_tasa_remuneratoria_excede_tope_de_usura_no_lanza_error_y_aplica_sancion_doblada(self):
        fecha_corte = date(2025, 1, 20)  # antes del vencimiento: solo corre la remuneratoria
        obligacion_pactada = _obligacion_comercial(
            tasa_remuneratoria=Decimal("35.00"), tasa_moratoria=Decimal("6.00"), ibc=Decimal("20.00")
        )

        # Tope legal = 1.5 x 20 = 30%. Antes del vencimiento, Comercial usa solo la tasa
        # remuneratoria -- exactamente lo mismo que CivilFamiliaStrategy con esa tasa (ver
        # test_sin_mora_usa_solo_tasa_remuneratoria arriba), asi que sirve de referencia
        # independiente para "Intereses_Cobrados"/"Intereses_Cobrados_Con_Tasa_Usura".
        intereses_cobrados = CivilFamiliaStrategy().liquidar(
            obligaciones=[_obligacion_comercial(tasa_remuneratoria=Decimal("35.00"))],
            abonos=[], fecha_corte=fecha_corte,
        ).final_balance().interest
        intereses_con_tasa_usura = CivilFamiliaStrategy().liquidar(
            obligaciones=[_obligacion_comercial(tasa_remuneratoria=Decimal("30.00"))],
            abonos=[], fecha_corte=fecha_corte,
        ).final_balance().interest

        exceso_esperado = intereses_cobrados - intereses_con_tasa_usura
        sancion_esperada = exceso_esperado * 2

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_pactada], abonos=[], fecha_corte=fecha_corte
        )

        item_sancion = resultado.items[-1]
        assert "usura" in item_sancion.concept.lower()
        assert item_sancion.interest_amount == -sancion_esperada

    def test_tasa_muy_por_encima_del_tope_puede_dejar_saldo_a_favor_del_deudor(self):
        # La sancion (2x el exceso) puede superar el saldo restante de la obligacion --
        # el despacho es explicito en que eso genera un saldo a favor del deudor (numero
        # negativo), no un piso en cero.
        fecha_corte = date(2027, 1, 1)
        obligacion = _obligacion_comercial(
            valor=Decimal("10000.00"), tasa_moratoria=Decimal("1000.00"), ibc=Decimal("20.00")
        )

        resultado = ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte)

        assert resultado.final_balance().total() < Decimal("0.00")

    def test_tasas_dentro_del_tope_no_agregan_item_de_sancion(self):
        obligacion = _obligacion_comercial(tasa_moratoria=Decimal("24.00"), ibc=Decimal("20.00"))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert all("usura" not in item.concept.lower() for item in resultado.items)

    def test_fecha_vencimiento_anterior_a_fecha_origen_lanza_value_error(self):
        obligacion = _obligacion_comercial(
            fecha_origen=date(2025, 2, 1), fecha_vencimiento=date(2025, 1, 1)
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    @pytest.mark.parametrize(
        "campo", ["tasa_moratoria_anual", "fecha_vencimiento", "ibc_vigente_anual", "tasa_efectiva_anual"]
    )
    def test_falta_un_campo_comercial_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_comercial()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_recurrente_no_hace_split_usa_tasa_moratoria_unica(self):
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
        )

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5)
        )

        # 3 cuotas de 500000 causadas: enero, febrero, marzo
        assert resultado.final_balance().principal == Decimal("1500000.00")

    def test_soporta_indexacion_ipc_es_false(self):
        assert ComercialStrategy().soporta_indexacion_ipc is False

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2025, 1, 11)  # antes del vencimiento (2025-06-01) de ambas
        obligacion_a = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1), fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("6.00"),
        )
        obligacion_a.id = 111
        obligacion_b = _obligacion_comercial(
            fecha_origen=date(2025, 1, 1), fecha_vencimiento=date(2025, 6, 1),
            tasa_remuneratoria=Decimal("18.00"),
        )
        obligacion_b.id = 112

        resultado_combinado = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = ComercialStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = ComercialStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_combinado.final_balance().principal == Decimal("2000000.00")
        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest

    def test_items_tienen_rate_source_por_tramo(self):
        obligacion = _obligacion_comercial()

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        fuentes = {item.rate_source for item in resultado.items}
        assert "Tasa remuneratoria pactada (Art. 884 C.Co.)" in fuentes
        assert "Tasa moratoria pactada (Art. 884 C.Co.)" in fuentes

    def test_obligacion_en_usd_convierte_el_capital_a_pesos_antes_de_liquidar(self):
        obligacion_usd = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion_usd.moneda = "USD"
        obligacion_usd.trm_aplicable = Decimal("4000.0000")
        obligacion_usd.trm_fecha_referencia = date(2025, 1, 1)

        resultado_usd = ComercialStrategy().liquidar(
            obligaciones=[obligacion_usd], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        obligacion_cop = _obligacion_comercial(valor=Decimal("40000000.00"))
        resultado_cop = ComercialStrategy().liquidar(
            obligaciones=[obligacion_cop], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado_usd.final_balance().principal == Decimal("40000000.00")
        assert resultado_usd.final_balance().interest == resultado_cop.final_balance().interest

    def test_obligacion_usd_sin_trm_aplicable_usa_el_proveedor_dinamico_en_la_fecha_de_origen(self):
        # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 12): "eliminar
        # la logica de TRM congelada al inicio" -- trm_aplicable ya NO es
        # obligatorio. Sin el, se usa el TRMProvider inyectado (en produccion,
        # SFCTRMProvider, la API en vivo de la SFC), consultado en la fecha real
        # del evento.
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        proveedor = _TRMProviderDeCalendario({date(2025, 1, 1): Decimal("4000.0000")})

        resultado = ComercialStrategy(trm_provider=proveedor).liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("40000000.00")

    def test_abono_en_usd_se_convierte_con_la_trm_de_su_propia_fecha_de_pago(self):
        # El nucleo de la correccion del Sprint 12: cada abono usa la TRM
        # vigente en SU PROPIA fecha, no la del origen de la obligacion (que
        # aqui usa una TRM distinta, 4000, para dejar clara la diferencia).
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        proveedor = _TRMProviderDeCalendario({
            date(2025, 1, 1): Decimal("4000.0000"),
            date(2025, 2, 1): Decimal("4200.0000"),
        })
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2025, 2, 1), monto=Decimal("1000.00"), referencia="ref-1"
        )

        resultado = ComercialStrategy(trm_provider=proveedor).liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        # 1.000 USD x TRM del 2025-02-01 (4.200) = 4.200.000 COP aplicados --
        # NO 1.000 x TRM del origen (4.000) = 4.000.000, que habria sido el
        # resultado con la TRM "congelada" que corrige este sprint.
        assert resultado.total_payments_applied() == Decimal("4200000.00")

    def test_obligacion_usd_con_trm_aplicable_manual_ignora_el_proveedor_dinamico(self):
        # trm_aplicable sigue siendo una anulacion manual valida (compatibilidad):
        # si esta seteado, se usa ese valor fijo para todo, sin tocar el
        # proveedor dinamico -- ni siquiera se consulta.
        obligacion = _obligacion_comercial(valor=Decimal("10000.00"))
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = Decimal("4000.0000")
        proveedor_que_no_deberia_usarse = _TRMProviderDeCalendario({})  # lanzaria KeyError si se consulta
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2025, 2, 1), monto=Decimal("1000.00"), referencia="ref-1"
        )

        resultado = ComercialStrategy(trm_provider=proveedor_que_no_deberia_usarse).liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.total_payments_applied() == Decimal("4000000.00")

    @pytest.mark.parametrize("trm_invalida", [Decimal("0.0000"), Decimal("-100.0000")])
    def test_obligacion_usd_con_trm_no_positiva_lanza_value_error(self, trm_invalida):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = trm_invalida
        obligacion.trm_fecha_referencia = date(2025, 1, 1)

        with pytest.raises(ValueError, match="trm_aplicable"):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_obligacion_sin_moneda_seteada_se_trata_como_cop(self):
        obligacion = _obligacion_comercial()
        assert obligacion.moneda is None  # atributo no seteado en construccion directa, sin sesion

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1)
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_ambas_condiciones_de_anatocismo_a_la_vez_lanza_value_error(self):
        obligacion = _obligacion_comercial(
            anatocismo_demanda_judicial=True,
            anatocismo_fecha_acuerdo=date(2026, 2, 15),
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1))

    def test_recurrente_con_anatocismo_activo_lanza_value_error(self):
        obligacion = Obligacion(
            id=2,
            expediente_id=1,
            tipo=TipoObligacion.RECURRENTE,
            concepto="Cuotas de pagare a plazos",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("500000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("24.00"),
            fecha_vencimiento=date(2025, 1, 1),
            ibc_vigente_anual=Decimal("20.00"),
            dia_pago=5,
            fecha_inicio=date(2025, 1, 1),
            fecha_fin=date(2025, 3, 5),
            anatocismo_demanda_judicial=True,
        )

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 5))

    def test_acuerdo_posterior_que_no_cumple_un_anio_lanza_value_error(self):
        # vencimiento 2025-02-01 + 365 dias = 2026-02-01; un acuerdo antes de esa fecha es invalido.
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 1, 15))

        with pytest.raises(ValueError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1))

    def test_acuerdo_posterior_que_cumple_exactamente_un_anio_no_lanza_error(self):
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 1))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 3, 1)
        )

        assert resultado.final_balance().principal > obligacion.valor

    def test_anatocismo_se_activa_con_demanda_judicial_y_mora_mayor_a_un_anio(self):
        fecha_corte = date(2026, 3, 1)
        obligacion_anatocismo = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_anatocismo = ComercialStrategy().liquidar(
            obligaciones=[obligacion_anatocismo], abonos=[], fecha_corte=fecha_corte
        )

        obligacion_simple = _obligacion_comercial()
        resultado_simple = ComercialStrategy().liquidar(
            obligaciones=[obligacion_simple], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado_anatocismo.final_balance().principal > obligacion_anatocismo.valor
        assert resultado_anatocismo.final_balance().total() > resultado_simple.final_balance().total()

    def test_anatocismo_se_activa_con_acuerdo_posterior_valido(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial(anatocismo_fecha_acuerdo=date(2026, 2, 15))

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal > obligacion.valor

    def test_anatocismo_no_se_activa_sin_condicion_habilitante(self):
        fecha_corte = date(2026, 3, 1)
        obligacion = _obligacion_comercial()

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_anatocismo_no_se_activa_si_fecha_corte_es_anterior_a_capitalizacion(self):
        fecha_corte = date(2025, 6, 1)  # vencimiento (2025-02-01) + 365 dias = 2026-02-01, aun no llega
        obligacion = _obligacion_comercial(anatocismo_demanda_judicial=True)

        resultado = ComercialStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        assert resultado.final_balance().principal == obligacion.valor

    def test_timing_del_abono_relativo_a_la_capitalizacion_determina_cuanto_se_capitaliza(self):
        fecha_capitalizacion = date(2026, 2, 1)  # vencimiento (2025-02-01) + 365 dias
        monto_abono = Decimal("50.00")  # deliberadamente pequeno: nunca llega a tocar el
        # capital, solo el bucket de interes -- eso es lo que hace la comparacion exacta.

        obligacion_abono_antes = _obligacion_comercial(anatocismo_demanda_judicial=True)
        abono_antes = Abono(
            id=1, obligacion_id=1, fecha=date(2026, 1, 31), monto=monto_abono, referencia="ref-1"
        )
        resultado_antes = ComercialStrategy().liquidar(
            obligaciones=[obligacion_abono_antes], abonos=[abono_antes], fecha_corte=date(2026, 3, 1)
        )

        obligacion_abono_despues = _obligacion_comercial(anatocismo_demanda_judicial=True)
        abono_despues = Abono(
            id=1, obligacion_id=1, fecha=date(2026, 2, 2), monto=monto_abono, referencia="ref-1"
        )
        resultado_despues = ComercialStrategy().liquidar(
            obligaciones=[obligacion_abono_despues], abonos=[abono_despues], fecha_corte=date(2026, 3, 1)
        )

        # Un abono un dia ANTES de la capitalizacion (2026-02-01) reduce el interes que
        # alcanza a capitalizarse (el monto es deliberadamente pequeno, nunca toca el
        # capital); el mismo abono un dia DESPUES ya no resta nada del monto ya
        # capitalizado -- la capitalizacion ya ocurrio. La diferencia de capital final
        # entre ambos escenarios debe ser exactamente el monto del abono: prueba que el
        # orden cronologico abono/capitalizacion se respeta de verdad, no solo que "un
        # abono reduce el total" (eso ya lo garantiza AllocationEngine sin necesidad de
        # anatocismo).
        diferencia = resultado_despues.final_balance().principal - resultado_antes.final_balance().principal
        assert diferencia == monto_abono

    def test_anatocismo_capitaliza_periodicamente_en_cada_aniversario(self):
        obligacion_antes_primera = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_antes_primera = ComercialStrategy().liquidar(
            obligaciones=[obligacion_antes_primera], abonos=[], fecha_corte=date(2026, 1, 31)
        )

        obligacion_despues_primera = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_despues_primera = ComercialStrategy().liquidar(
            obligaciones=[obligacion_despues_primera], abonos=[], fecha_corte=date(2027, 1, 31)
        )

        obligacion_despues_segunda = _obligacion_comercial(anatocismo_demanda_judicial=True)
        resultado_despues_segunda = ComercialStrategy().liquidar(
            obligaciones=[obligacion_despues_segunda], abonos=[], fecha_corte=date(2027, 2, 2)
        )

        principal_antes_primera = resultado_antes_primera.final_balance().principal
        principal_despues_primera = resultado_despues_primera.final_balance().principal
        principal_despues_segunda = resultado_despues_segunda.final_balance().principal

        # Antes de la primera capitalizacion (2026-02-01), el capital nunca crece por
        # anatocismo -- sigue igual al valor original.
        assert principal_antes_primera == obligacion_antes_primera.valor

        # Justo antes de la segunda capitalizacion (2027-02-01): ya paso la primera, el
        # capital creció una vez.
        assert principal_despues_primera > obligacion_despues_primera.valor

        # Justo despues de la segunda capitalizacion: el capital crece de nuevo, a partir
        # de la base YA aumentada por la primera -- no del valor original. Si la segunda
        # capitalizacion compusiera solo sobre el valor original (bug de "reset" en el
        # bucle), el segundo salto seria igual al primero; en compuesto real sobre una
        # base mayor, el segundo salto debe ser estrictamente mayor que el primero.
        primer_salto = principal_despues_primera - obligacion_despues_primera.valor
        segundo_salto = principal_despues_segunda - principal_despues_primera
        assert segundo_salto > primer_salto


def test_comercial_genera_evento_de_costas_si_esta_configurado():
    # Mismo caso de referencia que Tasks 4/11/12/14: 123.500.000 en el punto
    # medio del tier menor cuantia de 2024 -> costas = 8.645.000,00.
    obligacion = _obligacion_comercial(valor=Decimal("123500000.00"))
    obligacion.fecha_origen = date(2024, 6, 1)
    obligacion.fecha_vencimiento = date(2024, 7, 1)  # debe ser posterior a fecha_origen
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = ComercialStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COSTAS_PROCESALES" in tipos_evento
    assert resultado.final_balance().principal == Decimal("132145000.00")  # 123.500.000 + 8.645.000


def test_comercial_usd_calcula_costas_sobre_el_valor_convertido_a_pesos_no_sobre_el_valor_en_usd():
    # Regresion: confirma que las costas se calculan sobre valor_pesos (post
    # conversion TRM), no sobre obligacion.valor crudo en USD -- si alguien
    # revierte a pasar obligacion.valor, este test debe fallar.
    obligacion = _obligacion_comercial(valor=Decimal("30875.00"))
    obligacion.moneda = "USD"
    obligacion.trm_aplicable = Decimal("4000.00")
    obligacion.trm_fecha_referencia = date(2024, 6, 1)
    obligacion.fecha_origen = date(2024, 6, 1)
    obligacion.fecha_vencimiento = date(2024, 7, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"

    resultado = ComercialStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
    # 30.875 USD * 4.000 TRM = 123.500.000 pesos -> costas = 8.645.000,00 (7%,
    # punto medio del tier menor cuantia) -> total 132.145.000,00. Si el
    # calculo usara el valor crudo en USD (30.875) como pretensiones, el
    # resultado seria completamente distinto (y probablemente lanzaria
    # TarifaNoDisponibleError o un monto absurdo).
    assert resultado.final_balance().principal == Decimal("132145000.00")


def test_civil_familia_soporta_indexacion_ipc_es_true():
    assert CivilFamiliaStrategy().soporta_indexacion_ipc is True


def test_civil_familia_items_tienen_rate_source_poblado():
    strategy = CivilFamiliaStrategy()
    obligacion = _obligacion_puntual()

    resultado = strategy.liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
    )

    assert all(
        item.rate_source == "Tasa pactada en la obligación (Art. 1617 C.C.)"
        for item in resultado.items
    )


def _obligacion_sancionatoria(
    expediente_id=1,
    cantidad_smlmv_uvt=Decimal("2"),
    fecha_origen=date(2019, 6, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Multa SIC",
        categoria="MULTA_SANCIONATORIA",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        cantidad_smlmv_uvt=cantidad_smlmv_uvt,
    )


class TestSancionatorioStrategy:
    def test_liquida_multa_pre_2020_convirtiendo_smlmv_a_pesos(self):
        obligacion = _obligacion_sancionatoria()

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
        )

        # SMLMV 2019 = 828116.00 (ver historical_index.py); 2 SMLMV = 1656232.00.
        assert resultado.final_balance().principal == Decimal("1656232.00")

    def test_liquida_multa_posterior_a_2020_convirtiendo_uvt_a_pesos(self):
        obligacion = _obligacion_sancionatoria(fecha_origen=date(2021, 1, 1))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        # UVT 2021 = 36308.00; cantidad_smlmv_uvt por defecto en el factory es 2.
        assert resultado.final_balance().principal == Decimal("72616.00")

    def test_falta_cantidad_smlmv_uvt_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=None)

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_sancionatoria()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2019, 6, 1)
            )

    def test_multa_impaga_acumula_interes_moratorio_si_se_pacto_tasa(self):
        obligacion = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))

        resultado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2020, 6, 1)
        )

        assert resultado.final_balance().interest > Decimal("0.00")

    def test_soporta_indexacion_ipc_es_false(self):
        assert SancionatorioStrategy().soporta_indexacion_ipc is False

    def test_sancionatorio_genera_evento_de_costas_si_esta_configurado(self):
        # cantidad_smlmv_uvt=1000 con el fecha_origen por defecto del fixture
        # (2019-06-01, pre-2020 -> usa SMLMV, no UVT): monto_pesos = 1000 *
        # 828116.00 = 828.116.000,00 -- muy por encima de 150 SMLMV(2019) =
        # 124.217.400,00, cae en el tier "mayor cuantia" (sin techo), que siempre
        # usa el porcentaje minimo del rango (3%) sin necesidad de interpolar.
        # costas = 828.116.000 * 3% = 24.843.480,00, pero el tope de 20 SMLMV(2019)
        # = 16.562.320,00 es menor -> se aplica el tope. Este caso ademas ejercita
        # el tope de la Task 4 con un ejemplo end-to-end real.
        obligacion = _obligacion_sancionatoria(cantidad_smlmv_uvt=_Decimal("1000"))
        obligacion.costas_tipo_proceso = "declarativo_general"
        obligacion.costas_instancia = "primera"

        resultado = SancionatorioStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_origen)
        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COSTAS_PROCESALES" in tipos_evento
        assert resultado.final_balance().principal == _Decimal("844678320.00")  # 828.116.000 + 16.562.320

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2019, 6, 11)
        obligacion_a = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("12.00"))
        obligacion_a.id = 121
        obligacion_b = _obligacion_sancionatoria(tasa_efectiva_anual=Decimal("24.00"))
        obligacion_b.id = 122

        resultado_combinado = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = SancionatorioStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest


from app.core.exceptions import CuotaLitisExcedeTopeError


def _obligacion_honorarios(
    expediente_id=1,
    honorarios_fijos_pactados=Decimal("1000000.00"),
    cuota_litis_pactada_pct=Decimal("20.00"),
    beneficio_obtenido=Decimal("10000000.00"),
    costas_pct_manual=None,
    fecha_origen=date(2026, 1, 1),
    tasa_efectiva_anual=Decimal("0.00"),
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Honorarios proceso ejecutivo",
        categoria="HONORARIOS_PROFESIONALES",
        fecha_origen=fecha_origen,
        valor=Decimal("0.00"),
        tasa_efectiva_anual=tasa_efectiva_anual,
        honorarios_fijos_pactados=honorarios_fijos_pactados,
        cuota_litis_pactada_pct=cuota_litis_pactada_pct,
        beneficio_obtenido=beneficio_obtenido,
        costas_pct_manual=costas_pct_manual,
    )


from app.services.area_strategy import _evento_costas_procesales


def test_evento_costas_procesales_usa_costas_pct_manual_si_esta_presente():
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("5.00"))
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("10000000.00"))
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("500000.00")
    assert evento.event_type == "COSTAS_PROCESALES"


def test_evento_costas_procesales_usa_calculo_automatico_si_hay_tipo_e_instancia():
    # fecha_origen se fuerza a 2024-06-01 (SMLMV 2024 = 1.300.000.00) para que
    # 123.500.000 caiga exactamente en el punto medio del tier menor cuantia
    # (52.000.000 a 195.000.000) -> pct = 10 - 0.5*6 = 7%. El default de
    # _obligacion_honorarios (fecha_origen=2026-01-01) tambien funcionaria,
    # pero forzar el año mantiene el mismo caso de referencia usado en el
    # resto del plan (Tasks 4, 12, 13).
    obligacion = _obligacion_honorarios()
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))
    assert evento is not None
    assert evento.payload["amount"] == _Decimal("8645000.00")


def test_evento_costas_procesales_manual_gana_sobre_automatico():
    # 5% (no 7%, el automatico) -- dentro del rango permitido para menor cuantia
    # (3%-7%, respuesta del despacho Sprint 18) para que la validacion nueva no falle.
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("5.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))
    assert evento.payload["amount"] == _Decimal("6175000.00")  # 5% manual, no el 7% automatico


def test_evento_costas_procesales_manual_fuera_de_rango_lanza_error():
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 18): mayor cuantia
    # (>150 SMMLV) permite 1%-5% -- el sistema debe rechazar, no truncar, un valor
    # fuera de ese rango (ejemplo textual del despacho: "el usuario no podra ingresar
    # un 8% de agencias en derecho" en un proceso de Mayor Cuantia).
    from app.core.exceptions import CostasFueraDeRangoError

    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("8.00"), fecha_origen=_date(2026, 1, 1))
    # SMLMV 2026 = 1.750.905 -> 300.000.000 / 1.750.905 = ~171 SMMLV -> Mayor Cuantia.
    with pytest.raises(CostasFueraDeRangoError):
        _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("300000000.00"))


def test_evento_costas_procesales_manual_dentro_de_rango_no_lanza_error():
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("3.00"), fecha_origen=_date(2026, 1, 1))

    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("300000000.00"))

    assert evento is not None
    assert evento.payload["amount"] == _Decimal("9000000.00")


def test_evento_costas_procesales_sin_ninguno_de_los_dos_retorna_none():
    obligacion = _obligacion_honorarios()
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("10000000.00"))
    assert evento is None


class TestHonorariosStrategy:
    def test_liquida_honorarios_dentro_del_tope_total(self):
        # cuota litis = 10M * 20% = 2M. total = 1M + 2M = 3M (30% <= 50% tope total, OK).
        obligacion = _obligacion_honorarios()

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3000000.00")

    def test_cuota_litis_sola_por_encima_de_30_por_ciento_no_lanza_error_si_el_total_no_excede_50(self):
        # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 4): no se aplican dos topes en
        # cascada -- el unico tope legal es el 50% acumulado. cuota litis = 10M * 35% = 3.5M (35%
        # individual, por encima de lo que antes era un tope propio de 30%), pero honorarios_fijos=0
        # asi que el total (3.5M) sigue por debajo del 50% (5M) -> ya no debe fallar.
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("0.00"), cuota_litis_pactada_pct=Decimal("35.00")
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3500000.00")

    def test_suma_total_excede_50_por_ciento_lanza_error_citando_ley_1123_de_2007(self):
        # cuota litis = 10M * 45% = 4.5M. total = 1M + 4.5M = 5.5M > 5M (50% de 10M).
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("1000000.00"), cuota_litis_pactada_pct=Decimal("45.00")
        )

        with pytest.raises(CuotaLitisExcedeTopeError, match="Ley 1123/2007"):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_genera_evento_de_costas_si_costas_pct_manual_esta_seteado(self):
        # honorarios = 1M + (10M*10%=1M) = 2M. costas = 10M * 5% = 500000.
        obligacion = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), costas_pct_manual=Decimal("5.00")
        )

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("2500000.00")

    def test_sin_costas_pct_manual_no_genera_evento_de_costas(self):
        obligacion = _obligacion_honorarios(cuota_litis_pactada_pct=Decimal("10.00"))

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        # honorarios = 1M + (10M*10%=1M) = 2M, sin costas.
        assert resultado.final_balance().principal == Decimal("2000000.00")

    @pytest.mark.parametrize(
        "campo", ["honorarios_fijos_pactados", "cuota_litis_pactada_pct", "beneficio_obtenido"]
    )
    def test_falta_un_campo_obligatorio_lanza_value_error(self, campo):
        obligacion = _obligacion_honorarios()
        setattr(obligacion, campo, None)

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_honorarios()
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_soporta_indexacion_ipc_es_false(self):
        assert HonorariosStrategy().soporta_indexacion_ipc is False

    def test_dos_obligaciones_tasas_distintas_fechas_solapadas_liquidan_con_su_propia_tasa(self):
        fecha_corte = date(2026, 1, 11)
        obligacion_a = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("12.00")
        )
        obligacion_a.id = 131
        obligacion_b = _obligacion_honorarios(
            cuota_litis_pactada_pct=Decimal("10.00"), tasa_efectiva_anual=Decimal("24.00")
        )
        obligacion_b.id = 132

        resultado_combinado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_a = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_a], abonos=[], fecha_corte=fecha_corte
        )
        resultado_solo_b = HonorariosStrategy().liquidar(
            obligaciones=[obligacion_b], abonos=[], fecha_corte=fecha_corte
        )

        interes_esperado = resultado_solo_a.final_balance().interest + resultado_solo_b.final_balance().interest
        assert resultado_combinado.final_balance().interest == interes_esperado
        assert resultado_combinado.final_balance().interest != Decimal("2") * resultado_solo_a.final_balance().interest


from app.engine.labor.moratory_indemnity import MoratoryIndemnityCalculator


def _obligacion_laboral(
    expediente_id=1,
    salario=Decimal("3000000.00"),
    fecha_inicio=date(2020, 1, 1),
    fecha_fin=date(2020, 12, 31),
    pagada=False,
    fecha_pago_total=None,
    tipo=TipoObligacion.PUNTUAL,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=tipo,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=fecha_inicio,
        valor=salario,
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagada=pagada,
        fecha_pago_total=fecha_pago_total,
    )


class TestLaboralStrategy:
    def test_liquida_sin_mora_si_se_pago_el_mismo_dia_de_terminacion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" not in tipos_evento
        # dias_trabajados = 365 (2020-01-01 a 2020-12-31): cesantias 3041666.67 +
        # intereses 370069.44 + prima x2 1520833.33 + vacaciones 1520833.33
        assert resultado.final_balance().principal == Decimal("7974236.10")

    def test_liquida_con_mora_solo_fase1(self):
        # Pagado 30 dias despues de terminar el contrato -- solo fase 1.
        obligacion = _obligacion_laboral(fecha_pago_total=date(2021, 1, 30))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SANCION_MORATORIA" in tipos_evento
        # salario_diario = 3M/30 = 100000; 30 dias de retardo = 3000000.00
        assert resultado.final_balance().principal == Decimal("10974236.10")  # 7974236.10 + 3000000.00

    def test_liquida_con_mora_cruzando_a_fase2(self):
        # Sin pagar: fecha_corte muy posterior a la terminacion del contrato,
        # suficiente para cruzar a fase 2 (mas de 720 dias de retardo).
        obligacion = _obligacion_laboral()
        fecha_corte = obligacion.fecha_fin + timedelta(days=800)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7974236.10")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_esperada.dias_fase2 > 0
        assert resultado.final_balance().principal == monto_prestaciones + mora_esperada.total

    def test_aplica_un_abono_reduciendo_el_saldo(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2021, 1, 15), monto=Decimal("1000000.00"), referencia="ref-1"
        )

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[abono], fecha_corte=date(2021, 6, 1)
        )

        assert resultado.total_payments_applied() == Decimal("1000000.00")
        assert resultado.final_balance().total() < Decimal("7974236.10")

    def test_mas_de_una_obligacion_lanza_value_error(self):
        obligacion_1 = _obligacion_laboral(expediente_id=1)
        obligacion_2 = _obligacion_laboral(expediente_id=1)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion_1, obligacion_2], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_tipo_recurrente_lanza_value_error(self):
        obligacion = _obligacion_laboral(tipo=TipoObligacion.RECURRENTE)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1))

    def test_fecha_fin_anterior_a_fecha_inicio_lanza_value_error(self):
        obligacion = _obligacion_laboral(fecha_inicio=date(2020, 12, 31), fecha_fin=date(2020, 1, 1))

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1))

    def test_pagada_true_sin_fecha_pago_total_lanza_value_error(self):
        # pagada=True sin fecha_pago_total es un estado inconsistente: si se
        # dejara pasar, liquidar() trataria la obligacion como no pagada y
        # correria la mora hasta fecha_corte, sobrestimandola silenciosamente.
        obligacion = _obligacion_laboral(pagada=True, fecha_pago_total=None)

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1))

    def test_fecha_pago_total_posterior_a_fecha_corte_se_recorta_al_corte(self):
        # "Foto historica": si el pago real ocurrio despues del corte elegido
        # para este reporte, la mora se calcula solo hasta fecha_corte, no
        # hasta la fecha de pago real (que todavia esta en el futuro respecto
        # al corte).
        fecha_corte = date(2021, 3, 1)
        obligacion = _obligacion_laboral(fecha_pago_total=date(2022, 1, 1))

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7974236.10")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert resultado.final_balance().principal == monto_prestaciones + mora_esperada.total

    def test_soporta_indexacion_ipc_es_false(self):
        assert LaboralStrategy().soporta_indexacion_ipc is False

    def test_incluir_seguridad_social_sin_nivel_riesgo_lanza_value_error(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = None

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_incluir_seguridad_social_agrega_cotizaciones_a_la_deuda(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" in tipos_evento
        assert "COTIZACION_SALUD" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        # 7974236.10 (prestaciones existentes) + cotizaciones sobre 365 dias,
        # IBC 3000000.00, nivel I, sin suspension ni FSP (ver SeguridadSocialCalculator):
        # pension = 3000000*0.16*365/30 = 5840000.00
        # salud   = 3000000*0.125*365/30 = 4562500.00
        # arl     = 3000000*0.00522*365/30 = 190530.00
        assert resultado.final_balance().principal == Decimal("18567266.10")

    def test_sin_incluir_seguridad_social_no_hay_regresion(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        # incluir_seguridad_social queda en su default (False)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "COTIZACION_PENSION" not in tipos_evento
        assert resultado.final_balance().principal == Decimal("7974236.10")

    def test_incapacidad_comun_agrega_solo_el_monto_del_empleador_a_la_deuda(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),  # 3 dias
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_EMPLEADOR" in tipos_evento
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        # IBC = 3000000.00 (sin suspension, sin FSP); dias 1-2 empleador
        # 66.67% = 133340.00; dia 3 EPS 66.67% = 66670.00 (informativo, no suma).
        eventos_incapacidad_empleador = [
            item for item in resultado.items if item.balance.event_type == "INCAPACIDAD_EMPLEADOR"
        ]
        assert eventos_incapacidad_empleador[0].capital_base >= Decimal("133340.00")

    def test_incapacidad_laboral_no_agrega_nada_a_la_deuda_pero_deja_traza(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL,
            fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 11),  # 10 dias
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        assert "INCAPACIDAD_EMPLEADOR" not in tipos_evento

    def test_suspension_excluye_arl_de_esos_dias_y_deja_traza(self):
        from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.SUSPENSION,
            fecha_inicio=date(2020, 3, 1), fecha_fin=date(2020, 3, 31),  # 30 dias
            motivo_suspension=MotivoSuspension.HUELGA,
        )]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SUSPENSION_INFORMATIVA" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento
        eventos_arl = [item for item in resultado.items if item.balance.event_type == "COTIZACION_ARL"]
        # dias_trabajados=365, dias_suspension=30: arl = 3000000*0.00522*(365-30)/30
        assert eventos_arl[0].capital_base > Decimal("0.00")

    def test_suspension_e_incapacidad_combinadas_en_el_mismo_contrato(self):
        from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.SUSPENSION,
                fecha_inicio=date(2020, 3, 1), fecha_fin=date(2020, 3, 31),
                motivo_suspension=MotivoSuspension.HUELGA,
            ),
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
            ),
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        tipos_evento = {item.balance.event_type for item in resultado.items}
        assert "SUSPENSION_INFORMATIVA" in tipos_evento
        assert "INCAPACIDAD_EMPLEADOR" in tipos_evento
        assert "INCAPACIDAD_INFORMATIVA" in tipos_evento
        assert "COTIZACION_ARL" in tipos_evento

    def test_mora_fase2_no_incluye_cotizaciones_de_seguridad_social_en_la_base(self):
        # Regresion: con incluir_seguridad_social=True y retardo suficiente
        # para cruzar a fase 2 del Art. 65 CST, la base de la indemnizacion
        # moratoria (monto_adeudado) debe seguir siendo solo prestaciones
        # sociales -- NO debe incluir las cotizaciones de seguridad social no
        # pagadas (esas tienen consecuencias legales separadas, fuera de
        # alcance de este sprint).
        obligacion = _obligacion_laboral()
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        fecha_corte = obligacion.fecha_fin + timedelta(days=800)

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=fecha_corte
        )

        monto_prestaciones = Decimal("7974236.10")
        mora_esperada = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_esperada.dias_fase2 > 0

        # prestaciones (7974236.10) + cotizaciones (pension+salud+arl sobre
        # 365 dias, IBC 3000000.00, nivel I, sin suspension/FSP -- mismo
        # valor que test_incluir_seguridad_social_agrega_cotizaciones_a_la_
        # deuda) + mora calculada SOLO sobre prestaciones (el fix).
        monto_prestaciones_y_cotizaciones = Decimal("18567266.10")
        assert (
            resultado.final_balance().principal
            == monto_prestaciones_y_cotizaciones + mora_esperada.total
        )

        # Si la mora hubiera usado (bug) prestaciones+cotizaciones como base,
        # el total de la mora seria mayor -- confirma que el fix realmente
        # cambia el resultado y no es una coincidencia numerica.
        mora_con_bug = MoratoryIndemnityCalculator.calcular(
            salario_mensual=obligacion.valor,
            monto_adeudado=monto_prestaciones_y_cotizaciones,
            fecha_terminacion=obligacion.fecha_fin,
            fecha_pago_o_corte=fecha_corte,
        )
        assert mora_con_bug.total > mora_esperada.total

    def test_cotizacion_pension_expone_label_amigable_como_concept(self):
        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        eventos_pension = [
            item for item in resultado.items if item.balance.event_type == "COTIZACION_PENSION"
        ]
        assert len(eventos_pension) == 1
        assert "COTIZACION_PENSION" not in eventos_pension[0].concept
        assert "Pension" in eventos_pension[0].concept

    def test_eventos_laborales_sin_incluir_seguridad_social_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        # incluir_seguridad_social queda en su default (False) a proposito.
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
        )]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_evento_laboral_con_fecha_fuera_del_contrato_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2021, 1, 1), fecha_fin=date(2021, 1, 5),  # posterior a fecha_fin del contrato (2020-12-31)
        )]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_evento_laboral_con_fecha_inicio_anterior_al_contrato_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [EventoLaboral(
            obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2019, 12, 20), fecha_fin=date(2019, 12, 25),  # anterior a fecha_inicio del contrato (2020-01-01)
        )]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_dos_eventos_laborales_solapados_lanza_value_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 10),
            ),
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 5), fecha_fin=date(2020, 5, 15),  # se solapa con el anterior (5/5 - 5/10)
            ),
        ]

        with pytest.raises(ValueError):
            LaboralStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

    def test_eventos_laborales_consecutivos_no_solapados_no_lanza_error(self):
        from database.models import EventoLaboral, TipoEventoLaboral

        obligacion = _obligacion_laboral(fecha_pago_total=date(2020, 12, 31))
        obligacion.incluir_seguridad_social = True
        obligacion.nivel_riesgo_arl = "I"
        obligacion.eventos_laborales = [
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 10),
            ),
            EventoLaboral(
                obligacion_id=1, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
                fecha_inicio=date(2020, 5, 10), fecha_fin=date(2020, 5, 15),  # empieza justo cuando termina el anterior, no se solapa
            ),
        ]

        resultado = LaboralStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
        )

        assert resultado is not None  # no lanza error

    def test_laboral_genera_evento_de_costas_si_esta_configurado(self):
        from app.engine.costs.agencias_en_derecho import (
            Instancia,
            TipoProceso,
            calcular_agencias_en_derecho,
        )
        from app.engine.temporal.schedulers.labor import LaborScheduler

        # _obligacion_laboral no acepta 'valor' como parametro (usa 'salario'), y
        # LaboralStrategy genera varios eventos ademas de costas (cesantias,
        # prima, vacaciones) -- final_balance().principal mezclaria todo. Se aisla
        # el monto de costas comparando el capital_base acumulado justo antes y
        # justo despues del item de costas, en vez de sumar todo el saldo.
        # Nota: COSTAS_PROCESALES se fecha en obligacion.fecha_origen (=
        # fecha_inicio), anterior a fecha_fin (fecha de cesantias/prima/
        # vacaciones) -- por eso siempre ordena de primero (indice 0) y la
        # rama "capital_previo" con indice_costas > 0 no se ejercita en este
        # caso particular; se deja la forma generica (delta entre item actual
        # y el anterior) porque es la misma tecnica usada en las demas
        # strategies y sigue siendo correcta (capital_previo = 0.00 cuando
        # costas es el primer item).
        obligacion = _obligacion_laboral(
            salario=Decimal("123500000.00"), fecha_inicio=date(2024, 1, 1), fecha_fin=date(2024, 6, 1),
        )
        obligacion.costas_tipo_proceso = "declarativo_general"
        obligacion.costas_instancia = "primera"

        resultado = LaboralStrategy().liquidar([obligacion], [], fecha_corte=obligacion.fecha_fin)

        tipos_evento = [item.balance.event_type for item in resultado.items]
        assert "COSTAS_PROCESALES" in tipos_evento
        indice_costas = tipos_evento.index("COSTAS_PROCESALES")
        capital_previo = (
            resultado.items[indice_costas - 1].capital_base if indice_costas > 0 else Decimal("0.00")
        )
        monto_costas = resultado.items[indice_costas].capital_base - capital_previo

        # La base de costas es monto_prestaciones (cesantias + intereses +
        # prima + vacaciones para todo el contrato), NO obligacion.valor (que
        # es solo el salario mensual) -- ver LaboralStrategy.liquidar. Se
        # recalcula aqui, de forma independiente, con el mismo LaborScheduler
        # que usa produccion, para no depender de una constante "magica" sin
        # trazabilidad.
        dias_trabajados = (obligacion.fecha_fin - obligacion.fecha_inicio).days
        eventos_prestaciones = LaborScheduler(
            salario_base=obligacion.valor, dias_trabajados=dias_trabajados,
            fecha_liquidacion=obligacion.fecha_fin,
        ).generate()
        monto_prestaciones = sum((e.payload["amount"] for e in eventos_prestaciones), Decimal("0.00"))
        assert monto_prestaciones == Decimal("133003096.28")

        # fecha_origen (= fecha_inicio) 2024-01-01 -> SMLMV 2024 = 1.300.000,00
        # -> declarativo_general / primera instancia, tier MENOR cuantia
        # (52.000.000-195.000.000): interpolacion lineal Paragrafo 3 art. 3
        # (Acuerdo PSAA16-10554) da porcentaje = 6.601268687552447552...% ->
        # 133.003.096,28 * ese % = 8.779.891,75 -- verificado tambien llamando
        # calcular_agencias_en_derecho directamente con pretensiones_reconocidas
        # = monto_prestaciones.
        assert monto_costas == Decimal("8779891.75")
        assert monto_costas == calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso("declarativo_general"), instancia=Instancia("primera"),
            pretensiones_reconocidas=monto_prestaciones, fecha_radicacion=obligacion.fecha_inicio,
        )

    def test_costas_procesales_no_afecta_la_indemnizacion_moratoria(self):
        # Regresion critica: costas procesales debe aparecer como evento
        # independiente, pero NUNCA debe alimentar monto_adeudado (la base del
        # Art. 65 CST para SANCION_MORATORIA) -- ver LaboralStrategy.liquidar,
        # donde monto_prestaciones se captura en un Decimal ANTES de appendear
        # el evento de costas a `eventos`. Si costas se hubiera insertado antes
        # de esa linea (bug), monto_adeudado incluiria costas y la mora
        # calculada seria mayor -- PERO SOLO en fase 2 (dias_retardo > 720):
        # fase 1 (Art. 65 CST) es "un dia de salario por cada dia de retardo",
        # no usa monto_adeudado en absoluto (ver MoratoryIndemnityCalculator.
        # calcular), asi que un escenario de solo fase 1 no detectaria este
        # bug. Se usa el mismo patron de
        # test_mora_fase2_no_incluye_cotizaciones_de_seguridad_social_en_la_base
        # (retardo de 800 dias, cruza a fase 2) para que la comparacion sea
        # realmente sensible al bug.
        #
        # Se corre el mismo escenario (mismo salario, mismas fechas, mora
        # fase 2) dos veces -- una sin costas configuradas y otra con -- y se
        # compara el monto exacto de SANCION_MORATORIA (aislado via delta de
        # capital_base, igual tecnica que para costas arriba) entre ambas
        # corridas: deben ser identicos.
        def _liquidar_y_aislar_mora(con_costas: bool) -> Decimal:
            # fecha_fin=2024-05-01 (en vez de 2024-06-01, usado en el test de
            # costas de arriba) para que fecha_fin + 800 dias (2026-07-10)
            # siga cayendo dentro de los tramos IBC/Usura sembrados por la
            # fixture (hasta 2026-07-31) -- con 2024-06-01 el retardo de 800
            # dias cae en 2026-08, fuera de rango, y ademas monto_prestaciones
            # (105.448.531,01 para este contrato mas corto) debe seguir
            # cayendo en el tier MENOR cuantia de declarativo_general/primera
            # (52M-195M) para que costas se pueda calcular sin
            # TarifaNoDisponibleError (el acuerdo no tiene tarifa para tier
            # MINIMA en primera instancia -- las cuantias minimas se tramitan
            # en unica instancia, no en dos instancias).
            obligacion = _obligacion_laboral(
                salario=Decimal("123500000.00"), fecha_inicio=date(2024, 1, 1), fecha_fin=date(2024, 5, 1),
            )
            if con_costas:
                obligacion.costas_tipo_proceso = "declarativo_general"
                obligacion.costas_instancia = "primera"
            # 800 dias de retardo: cruza a fase 2 (limite fase 1 = 720 dias),
            # donde monto_adeudado si entra en el calculo de intereses.
            fecha_corte = obligacion.fecha_fin + timedelta(days=800)

            resultado = LaboralStrategy().liquidar([obligacion], [], fecha_corte=fecha_corte)

            tipos_evento = [item.balance.event_type for item in resultado.items]
            assert "SANCION_MORATORIA" in tipos_evento
            if con_costas:
                assert "COSTAS_PROCESALES" in tipos_evento
            indice_mora = tipos_evento.index("SANCION_MORATORIA")
            capital_previo = (
                resultado.items[indice_mora - 1].capital_base if indice_mora > 0 else Decimal("0.00")
            )
            return resultado.items[indice_mora].capital_base - capital_previo

        monto_mora_sin_costas = _liquidar_y_aislar_mora(con_costas=False)
        monto_mora_con_costas = _liquidar_y_aislar_mora(con_costas=True)

        assert monto_mora_sin_costas > Decimal("0.00")  # sanity: la mora si se disparo
        assert monto_mora_con_costas == monto_mora_sin_costas


def _obligacion_tributaria(
    expediente_id=1,
    categoria="IMPUESTO_A_CARGO",
    fecha_origen=date(2024, 3, 1),
    valor=Decimal("0.00"),
    base_sancion_tributaria=None,
    meses_extemporaneidad=None,
    sancion_agravada=False,
    ingresos_brutos=None,
    devoluciones_rebajas_descuentos=None,
    costos=None,
    deducciones=None,
    rentas_exentas=None,
):
    return Obligacion(
        id=1,
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Impuesto de renta 2024",
        categoria=categoria,
        fecha_origen=fecha_origen,
        valor=valor,
        tasa_efectiva_anual=Decimal("0.00"),
        base_sancion_tributaria=base_sancion_tributaria,
        meses_extemporaneidad=meses_extemporaneidad,
        sancion_agravada=sancion_agravada,
        ingresos_brutos=ingresos_brutos,
        devoluciones_rebajas_descuentos=devoluciones_rebajas_descuentos,
        costos=costos,
        deducciones=deducciones,
        rentas_exentas=rentas_exentas,
    )


class TestTributarioStrategy:
    def test_impuesto_a_cargo_sin_sanciones_ni_abonos_liquida_el_valor(self):
        obligacion = _obligacion_tributaria(categoria="IMPUESTO_A_CARGO", valor=Decimal("10000000.00"))

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.final_balance().principal == Decimal("10000000.00")

    def test_sancion_extemporaneidad_liquida_el_monto_calculado(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD",
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
            fecha_origen=date(2024, 3, 1),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        # 5% x 2 meses = 10% de 10,000,000 = 1,000,000 (por encima del piso de 10 UVT).
        assert resultado.final_balance().indexation == Decimal("1000000.00")

    def test_falta_categoria_no_reconocida_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="CATEGORIA_INEXISTENTE")

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_falta_base_sancion_en_extemporaneidad_lanza_value_error(self):
        obligacion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=None, meses_extemporaneidad=2
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_obligacion_recurrente_lanza_value_error(self):
        obligacion = _obligacion_tributaria(categoria="IMPUESTO_A_CARGO", valor=Decimal("100.00"))
        obligacion.tipo = TipoObligacion.RECURRENTE

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_orden_de_imputacion_sanciones_intereses_impuesto(self):
        # Desde el Sprint 15 (correccion del Art. 867-1 E.T., 2026-08-01), TributarioStrategy
        # liquida cada obligacion en su propio LiquidationCore aislado (mismo patron que
        # Comercial/CivilFamilia desde el Sprint 21, ver _liquidar_por_obligacion) -- es la
        # unica forma de darle 0% de interes a una sancion con mora > 3 anios mientras el
        # impuesto sigue acumulando el interes E.T. 635. Efecto secundario aceptado y
        # documentado (Pendientes.md, Sprint 15): un abono ya no se imputa automaticamente
        # contra el saldo combinado del expediente (sanciones primero, impuesto despues) --
        # cada abono debe indicar explicitamente, via `obligacion_id`, cual obligacion paga,
        # igual que en las demas areas desde el Sprint 21. Dentro de CADA obligacion, el
        # orden de imputacion (indexacion/sancion -> interes -> capital) sigue vigente,
        # simplemente ya no hay una bolsa compartida entre obligaciones distintas.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("1000000.00"), fecha_origen=date(2024, 3, 1)
        )
        impuesto.id = 1
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=Decimal("1000000.00"),
            meses_extemporaneidad=1, fecha_origen=date(2024, 3, 1),
        )
        sancion.id = 2
        # Sancion efectiva: 5% x 1 mes = 50,000, muy por debajo del piso de 10 UVT 2024
        # (470,650.00) -> queda en 470,650.00. El abono a la sancion la paga por completo
        # y sobra 29,350 (que en la liquidacion aislada de esa obligacion no tiene a donde
        # ir, ya que no hay otro bucket dentro de la misma obligacion).
        abono_sancion = Abono(
            id=1, obligacion_id=2, fecha=date(2024, 3, 1), monto=Decimal("500000.00"),
            referencia="Abono a la sancion",
        )
        abono_impuesto = Abono(
            id=2, obligacion_id=1, fecha=date(2024, 3, 1), monto=Decimal("200000.00"),
            referencia="Abono al impuesto",
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto, sancion],
            abonos=[abono_sancion, abono_impuesto],
            fecha_corte=date(2024, 3, 1),
        )

        saldo = resultado.final_balance()
        # Sin intereses (mismo dia, cero dias transcurridos): impuesto 1,000,000 - 200,000 =
        # 800,000 (bucket 'principal'); sancion 470,650 - 470,650 = 0 (pagada de sobra, el
        # exceso de 29,350 no reduce el impuesto porque ya no comparten balance).
        assert saldo.indexation == Decimal("0.00")
        assert saldo.interest == Decimal("0.00")
        assert saldo.principal == Decimal("800000.00")

    def test_renta_liquida_no_genera_evento_y_queda_en_resultado_renta_liquida(self):
        obligacion = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA",
            ingresos_brutos=Decimal("100000000.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"),
            costos=Decimal("40000000.00"),
            deducciones=Decimal("20000000.00"),
            rentas_exentas=Decimal("5000000.00"),
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2024, 3, 1)
        )

        assert resultado.is_empty()
        assert resultado.renta_liquida is not None
        assert resultado.renta_liquida.renta_liquida_gravable == Decimal("35000000.00")
        assert resultado.final_balance().total() == Decimal("0.00")

    def test_impuesto_con_mora_mayor_a_3_anios_indexa_y_topa_al_interes_de_usura_plena(self):
        # Caso real del despacho (Preguntas-Para-Abogado.md, Sprint 15): impuesto de
        # $100.000.000 vencido el 2018-05-10, liquidado el 2023-05-10 (5 anios de mora).
        # El interes E.T. 635 ya calculado (123.160.595,20) mas la indexacion IPC sin topar
        # (32.814.627,80) superarian el techo de usura plena (130.933.902,61) -- la
        # indexacion debe recortarse a 7.773.307,41 (verificado independientemente en
        # tests/engine/tax/test_actualizacion_867_1.py, mismo caso).
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("100000000.00"), fecha_origen=date(2018, 5, 10)
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto], abonos=[], fecha_corte=date(2023, 5, 10)
        )

        saldo = resultado.final_balance()
        assert saldo.principal == Decimal("100000000.00")
        assert saldo.interest == Decimal("123160595.20")
        assert saldo.indexation == Decimal("7773307.41")
        assert saldo.interest + saldo.indexation == Decimal("130933902.61")  # == techo de usura plena

    def test_impuesto_con_mora_de_3_anios_o_menos_no_indexa(self):
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("100000000.00"), fecha_origen=date(2020, 5, 10)
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto], abonos=[], fecha_corte=date(2023, 5, 10)  # exactamente 3 anios
        )

        assert resultado.final_balance().indexation == Decimal("0.00")

    def test_sancion_con_mora_mayor_a_3_anios_no_acumula_interes_solo_indexacion(self):
        # Respuesta del despacho (Sprint 15): "para el pago extemporaneo de sanciones, no
        # se liquida interes de mora, sino que se aplica exclusivamente la actualizacion
        # inflacionaria".
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2, fecha_origen=date(2018, 5, 10),
        )
        # Sancion efectiva: 5% x 2 meses = 10% de 10.000.000 = 1.000.000.

        resultado = TributarioStrategy().liquidar(
            obligaciones=[sancion], abonos=[], fecha_corte=date(2023, 5, 10)
        )

        saldo = resultado.final_balance()
        # Las sanciones caen en el bucket 'indexation', nunca 'principal' -- estructuralmente
        # nunca acumulan interes por si solas (ver nota del siguiente test). El efecto
        # verificable de la correccion es que la indexacion queda por encima del monto
        # nominal de la sancion (1.000.000), por el 867-1 adicional.
        assert saldo.interest == Decimal("0.00")
        assert saldo.indexation > Decimal("1000000.00")

    def test_sancion_con_mora_de_3_anios_o_menos_no_agrega_indexacion(self):
        # Nota: las sanciones caen en el bucket 'indexation' (no 'principal'), asi que
        # nunca acumulan interes por si solas (LiquidationCore._accrue_time_passage solo
        # acumula interes sobre 'principal', salvo Suma Unica -- comportamiento estructural
        # del motor, no algo que este sprint cambie). El unico efecto verificable de la
        # correccion del Art. 867-1 sobre una sancion es si se agrega o no el evento de
        # indexacion adicional.
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2, fecha_origen=date(2020, 5, 10),
        )
        # Sancion efectiva: 5% x 2 meses = 10% de 10.000.000 = 1.000.000.

        resultado = TributarioStrategy().liquidar(
            obligaciones=[sancion], abonos=[], fecha_corte=date(2023, 5, 10)  # exactamente 3 anios
        )

        saldo = resultado.final_balance()
        assert saldo.interest == Decimal("0.00")
        assert saldo.indexation == Decimal("1000000.00")  # sin el 867-1 adicional

    def test_dos_obligaciones_renta_liquida_en_el_mismo_expediente_lanza_value_error(self):
        renta_1 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA", ingresos_brutos=Decimal("1.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"), costos=Decimal("0.00"),
            deducciones=Decimal("0.00"), rentas_exentas=Decimal("0.00"),
        )
        renta_2 = _obligacion_tributaria(
            categoria="RENTA_LIQUIDA", ingresos_brutos=Decimal("2.00"),
            devoluciones_rebajas_descuentos=Decimal("0.00"), costos=Decimal("0.00"),
            deducciones=Decimal("0.00"), rentas_exentas=Decimal("0.00"),
        )

        with pytest.raises(ValueError):
            TributarioStrategy().liquidar(
                obligaciones=[renta_1, renta_2], abonos=[], fecha_corte=date(2024, 3, 1)
            )

    def test_soporta_indexacion_ipc_es_false(self):
        assert TributarioStrategy().soporta_indexacion_ipc is False


def test_civil_familia_suma_unica_activa_interes_es_mayor_que_legado():
    obligacion_legado = Obligacion(
        id=6, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    obligacion_suma_unica = Obligacion(
        id=7, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 12, 31)
    )
    resultado_suma_unica = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_suma_unica], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    # Mismo capital, misma indexacion (77633.53, ver test_civil_familia_puntual_con_indexacion_...),
    # misma tasa y periodo -- la unica diferencia es la base del interes.
    assert resultado_legado.final_balance().indexation == Decimal("77633.53")
    assert resultado_suma_unica.final_balance().indexation == Decimal("77633.53")
    assert resultado_legado.final_balance().interest == Decimal("87488.20")
    assert resultado_suma_unica.final_balance().interest == Decimal("94283.40")
    assert resultado_suma_unica.final_balance().interest > resultado_legado.final_balance().interest


def test_civil_familia_suma_unica_mezclada_en_el_expediente_liquida_cada_obligacion_con_su_propio_criterio():
    # Desde el Sprint 21, cada obligacion corre en su propio LiquidationCore
    # (PendingDebt independiente, ver _liquidar_por_obligacion), asi que ya no
    # hay un unico saldo compartido a nivel de expediente -- mezclar criterios
    # de Suma Unica entre obligaciones del mismo expediente ya no es un error
    # de captura (a diferencia de la version original de este test, escrita
    # antes del Sprint 21): cada obligacion simplemente liquida con su propio
    # criterio, y _fusionar_resultados suma los saldos individuales.
    obligacion_a = Obligacion(
        id=8, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente A",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_b = Obligacion(
        id=9, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente B",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_a, obligacion_b], abonos=[], fecha_corte=date(2025, 12, 31)
    )

    # Verificado contra el motor real: obligacion_a sola (Suma Unica) da
    # indexation=77633.53/interest=94283.40; obligacion_b sola (legado) da
    # indexation=38816.76/interest=43746.84. El resultado fusionado del
    # expediente es la suma exacta de ambos saldos independientes.
    fb = resultado.final_balance()
    assert fb.principal == Decimal("1500000.00")
    assert fb.indexation == Decimal("116450.29")
    assert fb.interest == Decimal("138030.24")


def test_civil_familia_suma_unica_ignora_obligaciones_sin_indexacion_activa():
    obligacion_indexada = Obligacion(
        id=10, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Dano emergente",
        categoria="DANO_EMERGENTE", fecha_origen=date(2024, 7, 1), valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )
    obligacion_sin_indexar = Obligacion(
        id=11, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Otro concepto",
        categoria="DANOS_MORALES", fecha_origen=date(2024, 7, 1), valor=Decimal("200000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=False,
        interes_sobre_capital_indexado=False,
    )

    # La obligacion sin indexacion activa no aporta indexation al saldo fusionado,
    # sin importar su propio valor de interes_sobre_capital_indexado (Suma Unica
    # solo tiene efecto cuando aplica_indexacion_ipc tambien es True).
    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_indexada, obligacion_sin_indexar], abonos=[], fecha_corte=date(2025, 12, 31)
    )
    assert resultado.final_balance().indexation == Decimal("77633.53")


def test_pdf_pagina_69_ejemplo_credito_indexado_50_millones_2010_a_2025():
    # PDF pag. 69, "Actualizacion por IPC": capital $50.000.000 firmado el 1/1/2010,
    # liquidado el 1/1/2025. El PDF usa indices ilustrativos (140 -> 200, Va=$71.428.571)
    # solo como ejemplo pedagogico; este test usa la serie IPC real del motor
    # (historical_index.py, transcrita de las paginas 55-62 del mismo PDF) para las
    # mismas fechas y el mismo capital, por lo que el resultado numerico es distinto
    # del ilustrativo de la pag. 69 -- ver docstring del test y spec de este sprint.
    obligacion = Obligacion(
        id=12, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Credito indexado",
        categoria="DANO_EMERGENTE", fecha_origen=date(2010, 1, 1), valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=True,
    )

    resultado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 1, 1)
    )

    fb = resultado.final_balance()
    # Va (capital ya indexado) = principal + indexation, calculado con la serie IPC
    # real: Va = 50.000.000 x (IPC(2025-01-01) / IPC(2010-01-01)).
    assert fb.principal == Decimal("50000000.00")
    assert fb.indexation == Decimal("51762113.73")
    va = fb.principal + fb.indexation
    assert va == Decimal("101762113.73")
    # Paso 2 (Suma Unica): interes civil 6% EA aplicado sobre Va, no sobre el capital
    # historico -- verificado independientemente replicando la acumulacion diaria del
    # motor (DailyInterest + EffectiveRateConverter) con capital=Va constante durante
    # todo el periodo (la indexacion se causa el mismo dia que el capital).
    assert fb.interest == Decimal("89015614.51")

    # Contraste: con el algoritmo legado (interes solo sobre el capital historico),
    # el mismo caso da un interes bastante menor -- confirma que Suma Unica
    # efectivamente cambia el resultado, no solo que el motor no truena.
    obligacion_legado = Obligacion(
        id=13, expediente_id=1, tipo=TipoObligacion.PUNTUAL, concepto="Credito indexado",
        categoria="DANO_EMERGENTE", fecha_origen=date(2010, 1, 1), valor=Decimal("50000000.00"),
        tasa_efectiva_anual=Decimal("6.00"), aplica_indexacion_ipc=True,
        interes_sobre_capital_indexado=False,
    )
    resultado_legado = CivilFamiliaStrategy().liquidar(
        obligaciones=[obligacion_legado], abonos=[], fecha_corte=date(2025, 1, 1)
    )
    assert resultado_legado.final_balance().interest == Decimal("43737103.72")
    assert fb.interest > resultado_legado.final_balance().interest
