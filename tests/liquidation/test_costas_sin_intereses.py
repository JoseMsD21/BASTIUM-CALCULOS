"""Sprint 79 -- las costas procesales NUNCA generan interes y se pagan primero.

Respuesta del despacho (16/11/2026, ver Preguntas-Para-Abogado, Sprint 79):
"las costas procesales NO generan intereses ... la regla es general: aplica en
cualquier area del derecho y algoritmo. Las costas se suman 'en seco' al final"
y, en la prelacion de imputacion, "1°) Costas procesales aprobadas y gastos de
cobro". El orden relativo entre indexacion, intereses y capital NO cambia en
este sprint (queda como estaba, ver docstring de AllocationEngine).

Todos los valores esperados estan calculados a mano en el comentario de cada
prueba (tasa de control 1% diario plano para que la aritmetica sea trivial).
"""

import re
from datetime import date
from decimal import Decimal

import pytest

from app.engine.audit.serialization import deserializar_resultado, serializar_resultado
from app.engine.financial.rate import Rate
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.balance import BalanceEngine
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.models import PendingDebt
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.temporal.schedulers.base import Event

_RATE_1PCT = Rate.from_percent(Decimal("1.00"))


def _eventos_capital_y_costas():
    return [
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("1000.00")},
            event_type="INSTALLMENT",
        ),
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("200.00"), "label": "Costas procesales - X"},
            event_type="COSTAS_PROCESALES",
        ),
    ]


# --- Modelo -----------------------------------------------------------------


def test_pending_debt_costas_default_cero_y_entra_al_total():
    assert PendingDebt(Decimal("1"), Decimal("2"), Decimal("3")).costas == Decimal("0.00")
    deuda = PendingDebt(Decimal("1000"), Decimal("10"), Decimal("5"), costas=Decimal("200"))
    # 1000 + 10 + 5 + 200 = 1215 -- Gran_Total suma las costas en seco
    assert deuda.total() == Decimal("1215")


def test_balance_engine_preserva_costas_en_todas_las_transiciones():
    deuda = PendingDebt(Decimal("100"), Decimal("10"), Decimal("5"), costas=Decimal("7"))
    deuda = BalanceEngine.add_costas(deuda, Decimal("3"))
    assert deuda.costas == Decimal("10")
    assert BalanceEngine.add_principal(deuda, Decimal("1")).costas == Decimal("10")
    assert BalanceEngine.add_interest(deuda, Decimal("1")).costas == Decimal("10")
    assert BalanceEngine.add_indexation(deuda, Decimal("1")).costas == Decimal("10")
    capitalizada = BalanceEngine.capitalize_interest(deuda)
    # anatocismo capitaliza solo intereses, nunca costas
    assert capitalizada.principal == Decimal("110")
    assert capitalizada.costas == Decimal("10")


# --- Motor: las costas no generan interes ------------------------------------


@pytest.mark.parametrize("usar_suma_unica", [False, True])
def test_costas_no_generan_interes_en_ningun_algoritmo(usar_suma_unica):
    eventos = _eventos_capital_y_costas()
    core = LiquidationCore(default_daily_rate=_RATE_1PCT, usar_suma_unica=usar_suma_unica)

    resultado = core.process(eventos, cutoff_date=date(2026, 1, 11))

    final = resultado.final_balance()
    assert final.principal == Decimal("1000.00")
    assert final.costas == Decimal("200.00")
    # 10 dias * 1000.00 * 1% = 100.00 -- SOLO sobre el capital. Antes del
    # Sprint 79 era 10 * 1200.00 * 1% = 120.00 (las costas generaban interes).
    assert final.interest == Decimal("100.00")
    # Gran_Total = 1000 + 100 + 0 + 200 (en seco) = 1300.00
    assert final.total() == Decimal("1300.00")
    # La base de interes auditada tampoco incluye las costas
    assert all(item.capital_base == Decimal("1000.00") for item in resultado.items)


def test_costas_no_generan_interes_bajo_suma_unica_con_indexacion():
    eventos = _eventos_capital_y_costas() + [
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("500.00")},
            event_type="INDEXATION",
        )
    ]
    core = LiquidationCore(default_daily_rate=_RATE_1PCT, usar_suma_unica=True)

    final = core.process(eventos, cutoff_date=date(2026, 1, 11)).final_balance()

    # 10 dias * (1000 capital + 500 indexacion) * 1% = 150.00; costas fuera de la base
    assert final.interest == Decimal("150.00")
    # Gran_Total = Capital_Indexado (1500) + Interes (150) + Costas (200) = 1850.00
    assert final.total() == Decimal("1850.00")


# --- Imputacion: costas primero -----------------------------------------------


def test_allocate_paga_costas_primero_abono_parcial():
    deuda = PendingDebt(
        Decimal("1000.00"), Decimal("100.00"), Decimal("50.00"), costas=Decimal("200.00")
    )

    asignacion, nueva, remanente = AllocationEngine.allocate(
        Decimal("150.00"), deuda, date(2026, 1, 11)
    )

    # 150 < 200 de costas -> todo el abono a costas, nada a los demas rubros
    assert asignacion.to_costas == Decimal("150.00")
    assert asignacion.to_indexation == Decimal("0.00")
    assert asignacion.to_interest == Decimal("0.00")
    assert asignacion.to_principal == Decimal("0.00")
    assert nueva == PendingDebt(
        Decimal("1000.00"), Decimal("100.00"), Decimal("50.00"), costas=Decimal("50.00")
    )
    assert remanente == Decimal("0.00")


def test_allocate_costas_luego_orden_vigente_indexacion_interes_capital():
    deuda = PendingDebt(
        Decimal("1000.00"), Decimal("100.00"), Decimal("50.00"), costas=Decimal("200.00")
    )

    asignacion, nueva, remanente = AllocationEngine.allocate(
        Decimal("300.00"), deuda, date(2026, 1, 11)
    )

    # 300 -> 200 costas, 50 indexacion, 50 interes (de 100), 0 capital
    assert asignacion.to_costas == Decimal("200.00")
    assert asignacion.to_indexation == Decimal("50.00")
    assert asignacion.to_interest == Decimal("50.00")
    assert asignacion.to_principal == Decimal("0.00")
    assert asignacion.total_payment == Decimal("300.00")
    assert nueva == PendingDebt(Decimal("1000.00"), Decimal("50.00"), Decimal("0.00"))
    assert remanente == Decimal("0.00")


def test_allocate_sobrepago_con_costas_devuelve_remanente():
    deuda = PendingDebt(Decimal("10.00"), Decimal("0.00"), Decimal("0.00"), costas=Decimal("5.00"))

    asignacion, nueva, remanente = AllocationEngine.allocate(
        Decimal("20.00"), deuda, date(2026, 1, 11)
    )

    assert asignacion.to_costas == Decimal("5.00")
    assert asignacion.to_principal == Decimal("10.00")
    assert asignacion.total_payment == Decimal("15.00")
    assert nueva.total() == Decimal("0.00")
    assert remanente == Decimal("5.00")


def test_allocate_capital_primero_tambien_paga_costas_primero():
    deuda = PendingDebt(
        Decimal("1000.00"), Decimal("100.00"), Decimal("50.00"), costas=Decimal("200.00")
    )

    asignacion, nueva, remanente = AllocationEngine.allocate_capital_primero(
        Decimal("500.00"), deuda, date(2026, 1, 11)
    )

    # 500 -> 200 costas, luego capital-primero (Sprint 75): 300 a capital
    assert asignacion.to_costas == Decimal("200.00")
    assert asignacion.to_principal == Decimal("300.00")
    assert asignacion.to_interest == Decimal("0.00")
    assert asignacion.to_indexation == Decimal("0.00")
    assert nueva == PendingDebt(Decimal("700.00"), Decimal("100.00"), Decimal("50.00"))
    assert remanente == Decimal("0.00")


def test_motor_abono_parcial_cubre_costas_antes_que_intereses_y_capital():
    eventos = _eventos_capital_y_costas() + [
        Event(
            date=date(2026, 1, 11),
            payload={"amount": Decimal("250.00")},
            event_type="PAYMENT",
        )
    ]
    core = LiquidationCore(default_daily_rate=_RATE_1PCT)

    resultado = core.process(eventos, cutoff_date=date(2026, 1, 21))

    # Al 11/01: capital 1000, interes 10*1000*1% = 100, costas 200.
    # Abono 250 -> 200 costas, 50 interes -> interes 50, capital 1000, costas 0.
    fila_abono = resultado.items[-2]
    assert fila_abono.balance.event_type == "PAYMENT"
    assert fila_abono.balance.debt == PendingDebt(
        Decimal("1000.00"), Decimal("50.00"), Decimal("0.00")
    )
    # 11/01 -> 21/01: 10 dias * 1000 * 1% = 100 mas -> interes 150.00
    final = resultado.final_balance()
    assert final.interest == Decimal("150.00")
    assert final.costas == Decimal("0.00")
    assert final.total() == Decimal("1150.00")


# --- Reportes y auditoria ---------------------------------------------------


def test_summary_muestra_costas_como_rubro_propio_solo_si_existen():
    core = LiquidationCore(default_daily_rate=_RATE_1PCT)
    resultado = core.process(_eventos_capital_y_costas(), cutoff_date=date(2026, 1, 11))

    summary = ReportSummaryBuilder().build_summary(resultado)

    assert summary["saldo_final_capital"] == "$1,000.00"
    assert summary["saldo_final_costas"] == "$200.00"
    assert summary["gran_total_adeudado"] == "$1,300.00"

    sin_costas = LiquidationCore(default_daily_rate=_RATE_1PCT).process(
        _eventos_capital_y_costas()[:1], cutoff_date=date(2026, 1, 11)
    )
    assert "saldo_final_costas" not in ReportSummaryBuilder().build_summary(sin_costas)


def test_serializacion_conserva_costas_y_acepta_snapshots_viejos():
    core = LiquidationCore(default_daily_rate=_RATE_1PCT)
    resultado = core.process(_eventos_capital_y_costas(), cutoff_date=date(2026, 1, 11))

    reconstruido = deserializar_resultado(serializar_resultado(resultado))
    assert reconstruido.final_balance().costas == Decimal("200.00")

    # Snapshot anterior al Sprint 79: sin la clave "costas" -> 0.00, sin KeyError
    viejo = re.sub(r',\s*"costas":\s*"[^"]*"', "", serializar_resultado(resultado))
    assert '"costas"' not in viejo
    assert deserializar_resultado(viejo).final_balance().costas == Decimal("0.00")
