from decimal import Decimal

from app.engine.math.rounding import Rounding


def test_money_round():

    assert Rounding.money("25.458") == Decimal("25.46")


def test_six_round():

    assert Rounding.six("1.123456789") == Decimal("1.123457")