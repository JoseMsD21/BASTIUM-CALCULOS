from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class FinancialEntry:

    date: date

    concept: str

    amount: Decimal