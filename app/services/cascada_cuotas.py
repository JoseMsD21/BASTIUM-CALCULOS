"""Sprint 75: motor de cascada para repartir un pago entre varias cuotas-hija
seleccionadas por rango. Ver docs/superpowers/specs/
2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md, seccion "Alcance",
punto 4.

distribuir_pago_en_cascada es una funcion pura (sin sesion de base de datos):
el caller (dialogo de UI) es responsable de calcular la deuda pendiente real
de cada cuota ANTES de llamar esta funcion, reutilizando
UniversalLiquidationService + AllocationEngine.allocate_capital_primero (el
mismo motor y la misma estrategia que se usara despues al liquidar de verdad
los Abono creados) -- asi la proyeccion de aqui y la liquidacion real
coinciden siempre, sin un numero precalculado aparte (decision 5 de la spec).
"""

from datetime import date
from decimal import Decimal
from typing import TypeVar

from app.domain.obligation.payment import Payment
from app.engine.interest.provider import RateProvider
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.models import PendingDebt
from app.engine.temporal.schedulers.base import Event
from app.services.motor_universal import UniversalLiquidationService

_T = TypeVar("_T")


def distribuir_pago_en_cascada(
    cuotas_y_deuda: list[tuple[_T, PendingDebt]],
    monto_total: Decimal,
    fecha_pago: date,
) -> tuple[list[tuple[_T, Decimal]], Decimal]:
    """`cuotas_y_deuda` debe venir ordenada de la cuota mas reciente a la mas
    antigua (lo decide el caller, segun el rango/seleccion del usuario en la
    UI). Retorna (asignaciones, remanente_sin_cubrir): asignaciones es una
    lista de (cuota, monto_asignado) solo para las cuotas que recibieron algo
    (> 0); remanente_sin_cubrir es lo que sobro despues de recorrer todas las
    cuotas de la lista (0 si el monto se reparte exacto)."""
    remanente = monto_total
    asignaciones: list[tuple[_T, Decimal]] = []
    for cuota, deuda in cuotas_y_deuda:
        if remanente <= Decimal("0.00"):
            break
        _, _, sobra = AllocationEngine.allocate_capital_primero(remanente, deuda, fecha_pago)
        monto_asignado = remanente - sobra
        if monto_asignado > Decimal("0.00"):
            asignaciones.append((cuota, monto_asignado))
        remanente = sobra
    return asignaciones, remanente


def deuda_pendiente_cuota(
    cuota,
    abonos_existentes: list,
    fecha_pago: date,
    rate_provider: RateProvider,
) -> PendingDebt:
    """Deuda pendiente real de una cuota-hija a `fecha_pago`, corriendo el
    mismo motor (UniversalLiquidationService) y la misma estrategia
    (allocate_capital_primero) que se usara despues al liquidar de verdad los
    Abono que cree la cascada -- no persiste nada (pagos=[] o los abonos ya
    existentes de esa cuota, nunca los que la cascada esta a punto de crear)."""
    evento = Event(
        date=cuota.fecha_origen,
        payload={"amount": cuota.valor, "label": cuota.concepto},
        event_type=cuota.categoria,
    )
    pagos = [
        Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
        for abono in abonos_existentes
        if abono.obligacion_id == cuota.id
    ]
    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=[evento],
        pagos=pagos,
        fecha_corte=fecha_pago,
        rate_provider=rate_provider,
        estrategia_imputacion=AllocationEngine.allocate_capital_primero,
    )
    return resultado.final_balance()
