from decimal import Decimal
from datetime import date

from app.engine.financial.entry import FinancialEntry
from app.engine.financial.ledger import Ledger


def test_running_balance():

    ledger = Ledger()

    ledger.add(
        FinancialEntry(
            date=date(2024, 1, 1),
            concept="Capital",
            amount=Decimal("100")
        )
    )

    ledger.add(
        FinancialEntry(
            date=date(2024, 1, 2),
            concept="Interés",
            amount=Decimal("20")
        )
    )

    assert ledger.total() == Decimal("120")