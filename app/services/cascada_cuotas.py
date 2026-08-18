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

from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.models import PendingDebt

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
