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
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
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


def test_civil_familia_soporta_indexacion_ipc_es_true():
    assert CivilFamiliaStrategy().soporta_indexacion_ipc is True
