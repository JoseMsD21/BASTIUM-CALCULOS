from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass
class Obligation:

    id: str

    concept: str

    due_date: date

    principal: Decimal

    remaining: Decimal

    priority: int

    category: str