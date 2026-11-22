"""Sprint 104 -- LiquidationCore con causacion tramo a tramo (patron X9 del
despacho, Suma Unica + abonos). Serie IPC ficticia para que cada cifra se pueda
verificar a mano:

    IPC(2024-01-01) = 100, IPC(2024-07-01) = 103, IPC(2025-01-01) = 105
    capital = 1.000.000 el 2024-01-01; corte 2025-01-01; i = 0,0048676 mensual.
    Cada tramo (2024-01-01 -> 2024-07-01 y 2024-07-01 -> 2025-01-01) mide 180
    dias 30/360 = 6 meses comerciales; (1,0048676)^6 - 1 = 0,0295633179960683...

Tramo 1: indexacion = 1.000.000 x (103/100 - 1) = 30.000,00; capital indexado
1.030.000,00; interes = 1.030.000 x 0,02956331799... = 30.450,22.
"""

from datetime import date
from decimal import Decimal

from app.engine.indexation.ipc import IPCIndexation
from app.engine.indexation.suma_unica_con_abonos import CausacionTramoATramo
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.engine import LiquidationCore
from app.engine.temporal.schedulers.base import Event

ORIGEN = date(2024, 1, 1)
ABONO = date(2024, 7, 1)
CORTE = date(2025, 1, 1)
IPC_FICTICIO = {ORIGEN: Decimal("100"), ABONO: Decimal("103"), CORTE: Decimal("105")}


def _indexacion_ficticia(capital: Decimal, desde: date, hasta: date) -> Decimal:
    return IPCIndexation.calculate(capital, IPC_FICTICIO[desde], IPC_FICTICIO[hasta])


def _core() -> LiquidationCore:
    return LiquidationCore(
        usar_suma_unica=True,
        estrategia_imputacion=AllocationEngine.allocate_intereses_primero,
        causacion_tramo_a_tramo=CausacionTramoATramo(indexacion_fn=_indexacion_ficticia),
    )


def _eventos(abono: Decimal, costas: Decimal | None = None) -> list[Event]:
    eventos = [
        Event(
            date=ORIGEN,
            payload={"amount": Decimal("1000000.00"), "label": "Capital"},
            event_type="DANO_EMERGENTE",
        ),
        Event(date=ABONO, payload={"amount": abono, "label": "Abono"}, event_type="PAYMENT"),
    ]
    if costas is not None:
        eventos.append(
            Event(
                date=ORIGEN,
                payload={"amount": costas, "label": "Costas"},
                event_type="COSTAS_PROCESALES",
            )
        )
    return eventos


def test_abono_que_cubre_intereses_reduce_el_capital_indexado_y_reindexa_el_saldo():
    resultado = _core().process(_eventos(Decimal("100000.00")), CORTE)

    fila_abono = next(item for item in resultado.items if item.balance.event_type == "PAYMENT")
    assert fila_abono.indexation_amount == Decimal("30000.00")
    assert fila_abono.interest_amount == Decimal("30450.22")
    assert fila_abono.payment_amount == Decimal("100000.00")
    # Art. 1653: 30.450,22 a intereses; 69.549,78 al capital indexado
    # -> nueva base 1.030.000,00 - 69.549,78 = 960.450,22.
    assert fila_abono.balance.debt.interest == Decimal("0.00")
    assert fila_abono.capital_base == Decimal("960450.22")

    # Tramo 2: 960.450,22 x 2/103 = 18.649,52 de indexacion; interes sobre
    # 979.099,74 x 0,02956331799... = 28.945,44.
    cierre = resultado.items[-1]
    assert cierre.balance.event_type == "LIQUIDATION_CUTOFF"
    assert cierre.indexation_amount == Decimal("18649.52")
    assert cierre.interest_amount == Decimal("28945.44")
    final = resultado.final_balance()
    assert final.principal + final.indexation == Decimal("979099.74")
    assert final.interest == Decimal("28945.44")
    assert final.total() == Decimal("1008045.18")
    assert cierre.interest_rate == Decimal("0.486760000000")


def test_abono_que_no_cubre_intereses_deja_pendiente_sin_reducir_capital():
    resultado = _core().process(_eventos(Decimal("10000.00")), CORTE)

    # 10.000 < 30.450,22: todo a intereses, quedan 20.450,22 pendientes (no
    # generan interes); el capital indexado 1.030.000 sigue intacto como base.
    # Tramo 2: 1.030.000 x 2/103 = 20.000,00; 1.050.000 x 0,0295633... = 31.041,48.
    final = resultado.final_balance()
    assert final.principal + final.indexation == Decimal("1050000.00")
    assert final.interest == Decimal("20450.22") + Decimal("31041.48")
    assert final.total() == Decimal("1101491.70")


def test_costas_se_pagan_primero_y_no_generan_interes_ni_se_indexan():
    resultado = _core().process(_eventos(Decimal("100000.00"), costas=Decimal("50000.00")), CORTE)

    # Abono 100.000: 50.000 costas, 30.450,22 intereses, 19.549,78 capital ->
    # base 1.010.450,22; tramo 2: +19.620,39 indexacion, 30.452,31 interes.
    final = resultado.final_balance()
    assert final.costas == Decimal("0.00")
    assert final.principal + final.indexation == Decimal("1030070.61")
    assert final.interest == Decimal("30452.31")
    assert final.total() == Decimal("1060522.92")


def test_sin_causacion_tramo_a_tramo_el_core_no_cambia():
    # Control: sin la configuracion, el mismo core no indexa ni causa interes
    # (tasa 0 por defecto) -- la indexacion solo entra por eventos INDEXATION.
    core = LiquidationCore(usar_suma_unica=True)
    resultado = core.process(_eventos(Decimal("100000.00")), CORTE)
    assert resultado.final_balance().total() == Decimal("900000.00")
    assert all(item.indexation_amount == Decimal("0.00") for item in resultado.items)


def test_allocate_intereses_primero_orden_costas_intereses_indexacion_capital():
    from app.engine.liquidation.models import PendingDebt

    deuda = PendingDebt(
        principal=Decimal("1000.00"),
        interest=Decimal("100.00"),
        indexation=Decimal("50.00"),
        costas=Decimal("20.00"),
    )
    asignacion, nueva, remanente = AllocationEngine.allocate_intereses_primero(
        Decimal("150.00"), deuda, ABONO
    )
    assert asignacion.to_costas == Decimal("20.00")
    assert asignacion.to_interest == Decimal("100.00")
    assert asignacion.to_indexation == Decimal("30.00")
    assert asignacion.to_principal == Decimal("0.00")
    assert nueva == PendingDebt(Decimal("1000.00"), Decimal("0.00"), Decimal("20.00"))
    assert remanente == Decimal("0.00")
