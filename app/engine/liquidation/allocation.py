from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import PaymentAllocation, PendingDebt
from app.engine.math.rounding import Rounding


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

    @staticmethod
    def allocate_proporcional_art_804(
        payment_amount: Decimal, current_debt: PendingDebt, payment_date: date
    ) -> tuple[PaymentAllocation, PendingDebt, Decimal]:
        """Imputacion proporcional del Art. 804 E.T. -- EXCLUSIVA del area
        Tributario (Sprint 84; las demas areas siguen con allocate()/
        allocate_capital_primero()). Respuesta del despacho (16/11/2026): "la
        imputacion proporcional es imperativa (no se imputa primero a intereses
        como en lo civil)". Contexto de la pregunta (Respondidas, Sprint 84
        seguimiento): "el abono se reparte proporcionalmente entre
        capital/sancion/interes segun el peso de cada uno en la deuda total".

        Formula (sobre el saldo de la obligacion EN LA FECHA DEL ABONO, ya con
        el interes causado hasta ese dia):
            disponible = abono - costas pagadas
            imputado_i = disponible x saldo_i / (impuesto + sanciones + intereses)
        con saldo_i en {indexation (sanciones/actualizacion 867-1), interest,
        principal (impuesto)}.

        - Costas procesales (Sprint 79) se pagan PRIMERO, antes del reparto
          proporcional -- regla general del despacho para toda area.
        - Redondeo: cada parte se redondea al centavo (ROUND_HALF_UP) y el
          centavo residual del redondeo va al impuesto (principal), de modo que
          la suma de las partes cuadra exactamente con el abono.
        - Si el disponible cubre toda la deuda, se paga todo y el exceso queda
          como remanente (saldo a favor), igual que en allocate().
        """
        remainder = payment_amount
        to_costas, new_costas, remainder = _imputar(remainder, current_debt.costas)

        total_conceptos = (
            current_debt.indexation + current_debt.interest + current_debt.principal
        )
        if remainder >= total_conceptos:
            to_indexation = current_debt.indexation
            to_interest = current_debt.interest
            to_principal = current_debt.principal
            remainder = remainder - total_conceptos
        else:
            to_indexation = min(
                Rounding.money(remainder * current_debt.indexation / total_conceptos),
                current_debt.indexation,
                remainder,
            )
            to_interest = min(
                Rounding.money(remainder * current_debt.interest / total_conceptos),
                current_debt.interest,
                remainder - to_indexation,
            )
            to_principal = remainder - to_indexation - to_interest
            # Caso limite de redondeo (centavos): si el residuo excede el saldo del
            # impuesto, el excedente se devuelve a intereses y luego a sanciones
            # (siempre hay capacidad, porque remainder < total_conceptos).
            exceso = max(to_principal - current_debt.principal, Decimal("0.00"))
            to_principal -= exceso
            sube_interes = min(exceso, current_debt.interest - to_interest)
            to_interest += sube_interes
            to_indexation += exceso - sube_interes
            remainder = Decimal("0.00")

        allocation = PaymentAllocation(
            payment_date=payment_date,
            total_payment=payment_amount - remainder,
            to_interest=to_interest,
            to_indexation=to_indexation,
            to_principal=to_principal,
            to_costas=to_costas,
        )

        new_debt = PendingDebt(
            principal=current_debt.principal - to_principal,
            interest=current_debt.interest - to_interest,
            indexation=current_debt.indexation - to_indexation,
            costas=new_costas,
        )

        return allocation, new_debt, remainder
