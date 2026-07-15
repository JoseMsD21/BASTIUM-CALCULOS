from decimal import Decimal

from datetime import date

from app.engine.financial.entry import FinancialEntry


def test_create_entry():

    entry = FinancialEntry(

        date=date(2025, 1, 1),

        concept="Cuota enero",

        amount=Decimal("300000")

    )

    assert entry.amount == Decimal("300000")