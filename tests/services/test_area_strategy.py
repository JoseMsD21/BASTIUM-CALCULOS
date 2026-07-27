from datetime import date as _date, datetime as _dt
from decimal import Decimal as _Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import AreaNoImplementadaError
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
    # depende de validar_tasa_usura (Tarea 7), que ahora lee USURA_MULTIPLICADOR
    # via parametro_service en cada liquidar() -- si esta fixture solo sembrara
    # las claves de Honorarios, todos los tests de Comercial de este archivo
    # fallarian con ParametroNoDisponibleError. Se siembran aqui las 3 claves
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
        clave="CUOTA_LITIS_INDIVIDUAL_PCT", valor=_Decimal("30"), vigente_desde=_date(2007, 1, 1),
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


@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
    strategy = AreaRegistry.get_strategy(area_name)
    assert isinstance(strategy, strategy_cls)
    with pytest.raises(AreaNoImplementadaError):
        strategy.liquidar(obligaciones=[], abonos=[], fecha_corte=None)


from datetime import date, timedelta
from decimal import Decimal

from database.models import AreaDerecho, Abono, Expediente, Obligacion, TipoObligacion


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


from app.core.exceptions import TasaUsurariaError


def _obligacion_comercial(
    expediente_id=1,
    valor=Decimal("1000000.00"),
    tasa_remuneratoria=Decimal("6.00"),
    tasa_moratoria=Decimal("24.00"),
    ibc=Decimal("20.00"),
    fecha_origen=date(2025, 1, 1),
    fecha_vencimiento=date(2025, 2, 1),
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
    )


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

    def test_tasa_moratoria_excede_tope_de_usura_lanza_error(self):
        obligacion = _obligacion_comercial(tasa_moratoria=Decimal("35.00"), ibc=Decimal("20.00"))

        with pytest.raises(TasaUsurariaError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_tasa_remuneratoria_excede_tope_de_usura_lanza_error(self):
        obligacion = _obligacion_comercial(tasa_remuneratoria=Decimal("35.00"), ibc=Decimal("20.00"))

        with pytest.raises(TasaUsurariaError):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

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

    def test_obligacion_usd_sin_trm_aplicable_lanza_value_error(self):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_fecha_referencia = date(2025, 1, 1)

        with pytest.raises(ValueError, match="trm_aplicable"):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

    def test_obligacion_usd_sin_trm_fecha_referencia_lanza_value_error(self):
        obligacion = _obligacion_comercial()
        obligacion.moneda = "USD"
        obligacion.trm_aplicable = Decimal("4000.0000")

        with pytest.raises(ValueError, match="trm_fecha_referencia"):
            ComercialStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2025, 3, 1))

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
    obligacion = _obligacion_honorarios(costas_pct_manual=_Decimal("2.00"))
    obligacion.fecha_origen = _date(2024, 6, 1)
    obligacion.costas_tipo_proceso = "declarativo_general"
    obligacion.costas_instancia = "primera"
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("123500000.00"))
    assert evento.payload["amount"] == _Decimal("2470000.00")  # 2% manual, no el 7% automatico


def test_evento_costas_procesales_sin_ninguno_de_los_dos_retorna_none():
    obligacion = _obligacion_honorarios()
    evento = _evento_costas_procesales(obligacion, pretensiones_reconocidas=_Decimal("10000000.00"))
    assert evento is None


class TestHonorariosStrategy:
    def test_liquida_honorarios_dentro_de_ambos_topes(self):
        # cuota litis = 10M * 20% = 2M (20% <= 30% tope individual, OK).
        # total = 1M + 2M = 3M (30% <= 50% tope total, OK).
        obligacion = _obligacion_honorarios()

        resultado = HonorariosStrategy().liquidar(
            obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1)
        )

        assert resultado.final_balance().principal == Decimal("3000000.00")

    def test_cuota_litis_sola_excede_30_por_ciento_lanza_error(self):
        # cuota litis = 10M * 35% = 3.5M > 3M (30% de 10M).
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("0.00"), cuota_litis_pactada_pct=Decimal("35.00")
        )

        with pytest.raises(CuotaLitisExcedeTopeError):
            HonorariosStrategy().liquidar(obligaciones=[obligacion], abonos=[], fecha_corte=date(2026, 1, 1))

    def test_suma_total_excede_50_por_ciento_aunque_cuota_litis_sola_no_exceda_30(self):
        # cuota litis = 10M * 25% = 2.5M (25% <= 30%, OK individualmente).
        # total = 3M + 2.5M = 5.5M > 5M (50% de 10M) -> debe fallar por el tope total.
        obligacion = _obligacion_honorarios(
            honorarios_fijos_pactados=Decimal("3000000.00"), cuota_litis_pactada_pct=Decimal("25.00")
        )

        with pytest.raises(CuotaLitisExcedeTopeError):
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
        # Impuesto a cargo de 1,000,000 y sancion de extemporaneidad de 1,000,000 (5% x 1
        # mes = 50,000, muy por debajo del piso de 10 UVT 2024 = 470,650.00, asi que la
        # sancion efectiva queda en 470,650.00), ambos con fecha_origen 2024-03-01. El abono
        # tambien cae el 2024-03-01 (mismo dia que fecha_corte) para que la acumulacion
        # automatica de interes (que corre por dias transcurridos) no aplique -- asi el
        # resultado es 100% aritmetica de imputacion, sin depender de tasas historicas de
        # usura para un rango de fechas.
        impuesto = _obligacion_tributaria(
            categoria="IMPUESTO_A_CARGO", valor=Decimal("1000000.00"), fecha_origen=date(2024, 3, 1)
        )
        sancion = _obligacion_tributaria(
            categoria="SANCION_EXTEMPORANEIDAD", base_sancion_tributaria=Decimal("1000000.00"),
            meses_extemporaneidad=1, fecha_origen=date(2024, 3, 1),
        )
        abono = Abono(
            id=1, obligacion_id=1, fecha=date(2024, 3, 1), monto=Decimal("500000.00"),
            referencia="Abono parcial",
        )

        resultado = TributarioStrategy().liquidar(
            obligaciones=[impuesto, sancion], abonos=[abono], fecha_corte=date(2024, 3, 1)
        )

        saldo = resultado.final_balance()
        # El abono de 500,000 paga primero la sancion completa (470,650.00, bucket
        # 'indexation'), y el remanente (500,000 - 470,650 = 29,350) va al impuesto (bucket
        # 'principal', pagado de ultimo): 1,000,000 - 29,350 = 970,650.00. Sin intereses
        # (mismo dia, cero dias transcurridos), asi que el bucket 'interest' no interviene.
        assert saldo.indexation == Decimal("0.00")
        assert saldo.interest == Decimal("0.00")
        assert saldo.principal == Decimal("970650.00")

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
