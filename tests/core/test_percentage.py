from decimal import Decimal

from app.engine.math.percentage import Percentage


def test_create_percentage():

    p = Percentage.from_percent(5)

    assert p.decimal() == Decimal("0.05")


def test_apply_percentage():

    p = Percentage.from_percent(10)

    assert p.apply_to(500) == Decimal("50.00")