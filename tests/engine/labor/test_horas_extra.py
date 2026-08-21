from decimal import Decimal

import pytest

from app.engine.labor.horas_extra import calcular_hora_extra, calcular_recargo


def test_hora_extra_aplica_valor_hora_mas_porcentaje():
    # HED tipico: $10.000/hora x 5 horas x (1 + 25%) = 62.500
    resultado = calcular_hora_extra(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("25"),
    )
    assert resultado == Decimal("62500.00")


def test_hora_extra_con_porcentaje_cero_equivale_al_valor_hora_simple():
    resultado = calcular_hora_extra(
        numero_horas=Decimal("3"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("0"),
    )
    assert resultado == Decimal("30000.00")


def test_hora_extra_acepta_enteros_ademas_de_decimal():
    resultado = calcular_hora_extra(
        numero_horas=2,
        valor_hora_ordinaria=10000,
        porcentaje=75,
    )
    # 2 x 10.000 x 1,75 = 35.000
    assert resultado == Decimal("35000.00")


@pytest.mark.parametrize("horas", [Decimal("0"), Decimal("-1")])
def test_hora_extra_horas_no_positivas_lanza_error(horas):
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=horas,
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("25"),
        )


def test_hora_extra_valor_hora_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("-1"),
            porcentaje=Decimal("25"),
        )


def test_hora_extra_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("-1"),
        )


def test_recargo_aplica_solo_el_porcentaje_sin_sumar_el_valor_hora_base():
    # Recargo nocturno tipico: $10.000/hora x 5 horas x 35% = 17.500
    # (no x 1,35, porque la hora ordinaria ya se pago por separado).
    resultado = calcular_recargo(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("35"),
    )
    assert resultado == Decimal("17500.00")


def test_recargo_con_porcentaje_cero_da_cero():
    resultado = calcular_recargo(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("0"),
    )
    assert resultado == Decimal("0.00")


def test_recargo_acepta_enteros_ademas_de_decimal():
    resultado = calcular_recargo(
        numero_horas=4,
        valor_hora_ordinaria=10000,
        porcentaje=75,
    )
    # 4 x 10.000 x 0,75 = 30.000
    assert resultado == Decimal("30000.00")


@pytest.mark.parametrize("horas", [Decimal("0"), Decimal("-1")])
def test_recargo_horas_no_positivas_lanza_error(horas):
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=horas,
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("35"),
        )


def test_recargo_valor_hora_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("-1"),
            porcentaje=Decimal("35"),
        )


def test_recargo_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("-1"),
        )
