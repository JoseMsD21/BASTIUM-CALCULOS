from decimal import Decimal
from typing import List

from .entry import FinancialEntry


class Ledger:

    def __init__(self):

        self.entries: List[FinancialEntry] = []

    def add(self, entry: FinancialEntry):

        self.entries.append(entry)

    def sort(self):

        self.entries.sort(key=lambda e: e.date)

    def total(self):

        total = Decimal("0")

        for e in self.entries:

            total += e.amount

        return total