from decimal import Decimal
from decimal import ROUND_HALF_UP


class Rounding:

    MONEY = Decimal("0.01")

    SIX = Decimal("0.000001")

    TWELVE = Decimal("0.000000000001")

    @staticmethod
    def money(value):

        return Decimal(
            str(value)
        ).quantize(
            Rounding.MONEY,
            rounding=ROUND_HALF_UP
        )

    @staticmethod
    def six(value):

        return Decimal(
            str(value)
        ).quantize(
            Rounding.SIX,
            rounding=ROUND_HALF_UP
        )

    @staticmethod
    def twelve(value):

        return Decimal(
            str(value)
        ).quantize(
            Rounding.TWELVE,
            rounding=ROUND_HALF_UP
        )