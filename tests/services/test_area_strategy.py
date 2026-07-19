import pytest

from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.registry import AreaRegistry
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
)


def test_registry_expone_las_5_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
    }


def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("LABORAL", LaboralStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
    strategy = AreaRegistry.get_strategy(area_name)
    assert isinstance(strategy, strategy_cls)
    with pytest.raises(AreaNoImplementadaError):
        strategy.liquidar(obligaciones=[], abonos=[], fecha_corte=None)


from datetime import date
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


from app.core.exceptions import UVTNoDisponibleError


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

    def test_liquida_multa_posterior_a_2020_lanza_uvt_no_disponible_error(self):
        obligacion = _obligacion_sancionatoria(fecha_origen=date(2021, 1, 1))

        with pytest.raises(UVTNoDisponibleError):
            SancionatorioStrategy().liquidar(
                obligaciones=[obligacion], abonos=[], fecha_corte=date(2021, 6, 1)
            )

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
