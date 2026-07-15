"""
rate.py

Representa una tasa matemática universal.

No representa únicamente intereses.

Puede representar:

- IPC
- SMMLV
- Interés diario
- Interés mensual
- UVR
- DTF
- IBR
- Inflación
- Rentabilidad
"""

from dataclasses import dataclass
from decimal import Decimal
from decimal import ROUND_HALF_UP


@dataclass(frozen=True)
class Rate:

    value: Decimal

    @classmethod
    def from_percent(cls, percent):

        return cls(

            Decimal(str(percent))

            / Decimal("100")

        )

    def decimal(self):

        return self.value.quantize(

            Decimal("0.000000000001"),

            rounding=ROUND_HALF_UP

        )

    def percent(self):

        return self.decimal() * Decimal("100")

    def apply(self, amount):

        amount = Decimal(str(amount))

        return (

            amount

            * self.decimal()

        ).quantize(

            Decimal("0.01"),

            rounding=ROUND_HALF_UP

        )

    def __str__(self):

        return f"{self.percent()}%"