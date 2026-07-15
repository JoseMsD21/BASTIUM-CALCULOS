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
        ("COMERCIAL", ComercialStrategy),
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
