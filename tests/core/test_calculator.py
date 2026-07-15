from app.engine.math.calculator import Calculator


def test_sum():

    assert Calculator.add(2, 3) == 5


def test_sub():

    assert Calculator.subtract(8, 2) == 6


def test_mul():

    assert Calculator.multiply(5, 4) == 20


def test_div():

    assert Calculator.divide(20, 4) == 5