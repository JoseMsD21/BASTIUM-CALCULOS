from app.engine.math.money import Money


def test_addition():

    assert Money("10")+Money("20")==Money("30")


def test_subtraction():

    assert Money("50")-Money("10")==Money("40")


def test_multiplication():

    assert Money("25")*2==Money("50")


def test_division():

    assert Money("100")/2==Money("50")