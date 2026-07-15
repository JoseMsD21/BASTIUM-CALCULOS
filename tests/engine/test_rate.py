from decimal import Decimal

from app.engine.financial.rate import Rate


def test_rate_creation():

    rate = Rate.from_percent(5)

    assert rate.decimal() == Decimal("0.050000000000")


def test_rate_apply():

    rate = Rate.from_percent(10)

    assert rate.apply(1000) == Decimal("100.00")