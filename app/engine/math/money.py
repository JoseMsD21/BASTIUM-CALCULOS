"""
LEXIA
Motor Matemático Universal

money.py

Clase base para representar cantidades monetarias con precisión
financiera absoluta utilizando Decimal.

Nunca utilizar float.

Autor:
Proyecto LEXIA
"""

from decimal import Decimal
from decimal import ROUND_HALF_UP


class Money:

    DECIMALS = Decimal("0.01")

    def __init__(self, value):

        if isinstance(value, Money):
            self.amount = value.amount

        else:
            self.amount = Decimal(str(value)).quantize(
                self.DECIMALS,
                rounding=ROUND_HALF_UP
            )

    def __repr__(self):

        return f"Money({self.amount})"

    def __str__(self):

        return f"${self.amount:,.2f}"

    def __add__(self, other):

        other = Money(other)

        return Money(self.amount + other.amount)

    def __sub__(self, other):

        other = Money(other)

        return Money(self.amount - other.amount)

    def __mul__(self, other):

        return Money(self.amount * Decimal(str(other)))

    def __truediv__(self, other):

        return Money(self.amount / Decimal(str(other)))

    def __lt__(self, other):

        return self.amount < Money(other).amount

    def __le__(self, other):

        return self.amount <= Money(other).amount

    def __gt__(self, other):

        return self.amount > Money(other).amount

    def __ge__(self, other):

        return self.amount >= Money(other).amount

    def __eq__(self, other):

        return self.amount == Money(other).amount

    def is_zero(self):

        return self.amount == Decimal("0.00")

    def to_decimal(self):

        return self.amount

    def round(self):

        return Money(self.amount.quantize(
            self.DECIMALS,
            rounding=ROUND_HALF_UP
        ))