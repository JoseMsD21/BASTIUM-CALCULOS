from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import PaymentAllocation, PendingDebt


def _imputar(remainder: Decimal, saldo: Decimal) -> tuple[Decimal, Decimal, Decimal]:
    """Aplica `remainder` a un rubro con saldo `saldo`.
    Retorna (lo imputado al rubro, nuevo saldo del rubro, remanente del pago)."""
    if remainder >= saldo:
        return saldo, Decimal("0.00"), remainder - saldo
    return remainder, saldo - remainder, Decimal("0.00")


class AllocationEngine:
    """
    Motor de imputación de pagos basado en la prelación legal estricta:
    0. Costas procesales aprobadas (Sprint 79)
    1. Gastos/Indexación
    2. Intereses
    3. Capital
    Retorna la asignación del pago, el nuevo estado de la deuda y el remanente (si aplica).

    Sprint 79: el despacho (16/11/2026) fijó que las costas procesales aprobadas y
    gastos de cobro se pagan PRIMERO (Arts. 1629, 1653, 2495 C.C. y 446 CGP), en
    cualquier área y algoritmo -- incluida la cascada capital-primero del Sprint 75.
    La misma respuesta ubica los intereses ANTES de la indexación; eso contradice el
    orden vigente (indexación -> intereses -> capital) y queda deliberadamente sin
    cambiar en este sprint hasta que el despacho lo confirme por separado.
    """

    @staticmethod
    def allocate(
        payment_amount: Decimal, current_debt: PendingDebt, payment_date: date
    ) -> tuple[PaymentAllocation, PendingDebt, Decimal]:
        remainder = payment_amount

        # 0. Imputación a Costas procesales (Sprint 79)
        to_costas, new_costas, remainder = _imputar(remainder, current_debt.costas)
        # 1. Imputación a Indexación
        to_indexation, new_indexation, remainder = _imputar(remainder, current_debt.indexation)
        # 2. Imputación a Intereses
        to_interest, new_interest, remainder = _imputar(remainder, current_debt.interest)
        # 3. Imputación a Capital
        to_principal, new_principal, remainder = _imputar(remainder, current_debt.principal)

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal,
            to_costas=to_costas,
        )

        new_debt = PendingDebt(
            principal=new_principal,
            interest=new_interest,
            indexation=new_indexation,
            costas=new_costas,
        )

        return allocation, new_debt, remainder

    @staticmethod
    def allocate_intereses_primero(
        payment_amount: Decimal, current_debt: PendingDebt, payment_date: date
    ) -> tuple[PaymentAllocation, PendingDebt, Decimal]:
        """Imputacion del Art. 1653 C.C. para la liquidacion tramo a tramo de Suma
        Unica con abonos (Sprint 104, algoritmo del despacho 22/08/2026): costas
        primero (Sprint 79), luego intereses, y el remanente al capital indexado
        (indexacion y despues principal: ambos son "capital indexado" en ese
        algoritmo, el orden entre ellos no cambia la base del tramo siguiente).
        Solo la usa `CivilFamiliaStrategy` en ese modo; `allocate()` conserva su
        orden de siempre para todo lo demas."""
        remainder = payment_amount

        to_costas, new_costas, remainder = _imputar(remainder, current_debt.costas)
        to_interest, new_interest, remainder = _imputar(remainder, current_debt.interest)
        to_indexation, new_indexation, remainder = _imputar(remainder, current_debt.indexation)
        to_principal, new_principal, remainder = _imputar(remainder, current_debt.principal)

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal,
            to_costas=to_costas,
        )

        new_debt = PendingDebt(
            principal=new_principal,
            interest=new_interest,
            indexation=new_indexation,
            costas=new_costas,
        )

        return allocation, new_debt, remainder

    @staticmethod
    def allocate_capital_primero(
        payment_amount: Decimal, current_debt: PendingDebt, payment_date: date
    ) -> tuple[PaymentAllocation, PendingDebt, Decimal]:
        """Cascada especial para cuotas-hija generadas por recurrencia (Sprint 75):
        capital primero, luego interes, luego indexacion -- orden inverso al de
        allocate() de arriba. Los intereses no cubiertos quedan "congelados" (no
        se les aplica el pago, pero tampoco se les suma nada nuevo aqui -- eso lo
        decide quien acumula interes despues, no este metodo). Ver
        docs/superpowers/specs/2026-08-14-sprint75-cuotas-recurrentes-cascada-design.md,
        decisiones 2 y 5.

        Sprint 79: aun en esta cascada, las costas procesales se pagan antes que
        cualquier otro rubro (regla general del despacho, ver docstring de la clase)."""
        remainder = payment_amount

        to_costas, new_costas, remainder = _imputar(remainder, current_debt.costas)
        to_principal, new_principal, remainder = _imputar(remainder, current_debt.principal)
        to_interest, new_interest, remainder = _imputar(remainder, current_debt.interest)
        to_indexation, new_indexation, remainder = _imputar(remainder, current_debt.indexation)

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal,
            to_costas=to_costas,
        )

        new_debt = PendingDebt(
            principal=new_principal,
            interest=new_interest,
            indexation=new_indexation,
            costas=new_costas,
        )

        return allocation, new_debt, remainder
