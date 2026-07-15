"""
percentage.py

Representa porcentajes matemáticos con precisión Decimal.

Nunca utiliza float.
"""

from decimal import Decimal
from decimal import ROUND_HALF_UP


class Percentage:

    DECIMALS = Decimal("0.000000000001")

    def __init__(self, value):

        self.value = Decimal(str(value)).quantize(
            self.DECIMALS,
            rounding=ROUND_HALF_UP
        )

    @classmethod
    def from_percent(cls, percent):

        return cls(
            Decimal(str(percent))
            / Decimal("100")
        )

    def apply_to(self, amount):

        return (
            Decimal(str(amount))
            * self.value
        ).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP
        )

    def decimal(self):

        return self.value

    def __str__(self):

        return f"{self.value * 100}%"

    def __repr__(self):

        return f"Percentage({self.value})"