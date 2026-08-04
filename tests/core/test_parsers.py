from decimal import Decimal

import pytest

from app.engine.math.parsers import FinancialParser


def test_parse_money_formato_colombiano_con_miles_y_decimales():
    assert FinancialParser.parse_money("$ 5.000.000,00") == Decimal("5000000.00")


def test_parse_money_formato_us_con_miles_y_decimales():
    assert FinancialParser.parse_money("$5,000,000.00") == Decimal("5000000.00")


def test_parse_money_formato_colombiano_solo_coma_decimal():
    assert FinancialParser.parse_money("5000000,50") == Decimal("5000000.50")


def test_parse_money_formato_us_solo_punto_decimal_no_se_infla_100x():
    # Bug real corregido en el Sprint 27: antes se interpretaba como
    # 500000000.00 (100x mas grande) al asumir formato colombiano siempre
    # y remover el punto como si fuera separador de miles.
    assert FinancialParser.parse_money("5000000.00") == Decimal("5000000.00")


def test_parse_money_formato_colombiano_solo_puntos_de_miles_sin_decimales():
    assert FinancialParser.parse_money("5.000.000") == Decimal("5000000")


def test_parse_money_un_solo_punto_de_miles_colombiano_tres_digitos():
    assert FinancialParser.parse_money("5.000") == Decimal("5000")


def test_parse_money_sin_separadores():
    assert FinancialParser.parse_money("5000000") == Decimal("5000000")


def test_parse_money_texto_invalido_lanza_value_error():
    with pytest.raises(ValueError):
        FinancialParser.parse_money("no es un monto")
