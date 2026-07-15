from decimal import Decimal

from app.domain.obligation.base import Obligation

from app.domain.obligation.payment import Payment


class AllocationEngine:

    def allocate(

        self,

        payment: Payment,

        obligations: list[Obligation],

    ):

        raise NotImplementedError