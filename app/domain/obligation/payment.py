from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Payment:

    date: date

    amount: Decimal

    reference: str