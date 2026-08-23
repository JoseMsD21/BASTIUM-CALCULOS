from decimal import Decimal

import pytest

from app.engine.labor.salario_domestico import (
    calcular_ibc_seguridad_social_domestico,
    salario_diario_a_mensual,
)


def test_jornada_parcial_tres_dias_por_semana():
    # $50.000/dia x 3 dias/semana / 7 x 30 = 4.500.000 / 7 = 642.857,142857...
    resultado = salario_diario_a_mensual(Decimal("50000"), Decimal("3"))
    assert resultado == Decimal("642857.14")


def test_jornada_completa_siete_dias_equivale_a_treinta_salarios_diarios():
    # $50.000/dia x 7 dias/semana / 7 x 30 = 50.000 x 30 = 1.500.000
    resultado = salario_diario_a_mensual(Decimal("50000"), Decimal("7"))
    assert resultado == Decimal("1500000.00")


def test_un_dia_por_semana():
    # $80.000/dia x 1 dia/semana / 7 x 30 = 2.400.000 / 7 = 342.857,142857...
    resultado = salario_diario_a_mensual(Decimal("80000"), Decimal("1"))
    assert resultado == Decimal("342857.14")


def test_salario_diario_cero_da_cero():
    assert salario_diario_a_mensual(Decimal("0"), Decimal("5")) == Decimal("0.00")


def test_acepta_enteros_ademas_de_decimal():
    assert salario_diario_a_mensual(50000, 7) == Decimal("1500000.00")


@pytest.mark.parametrize("dias", [Decimal("0"), Decimal("8"), Decimal("-1")])
def test_dias_fuera_de_rango_lanza_error(dias):
    with pytest.raises(ValueError):
        salario_diario_a_mensual(Decimal("50000"), dias)


def test_salario_diario_negativo_lanza_error():
    with pytest.raises(ValueError):
        salario_diario_a_mensual(Decimal("-1"), Decimal("3"))


class TestCalcularIbcSeguridadSocialDomestico:
    """Sprint 96 (respuesta del despacho, 22/08/2026):
    IBC_Seguridad_Social = max(Salario_Proporcional, 1_SMMLV)."""

    def test_salario_proporcional_por_debajo_del_smmlv_usa_el_smmlv(self):
        resultado = calcular_ibc_seguridad_social_domestico(
            salario_proporcional=Decimal("642857.14"), smmlv_mensual=Decimal("1300000.00")
        )
        assert resultado == Decimal("1300000.00")

    def test_salario_proporcional_por_encima_del_smmlv_usa_el_salario(self):
        resultado = calcular_ibc_seguridad_social_domestico(
            salario_proporcional=Decimal("1500000.00"), smmlv_mensual=Decimal("1300000.00")
        )
        assert resultado == Decimal("1500000.00")

    def test_salario_proporcional_igual_al_smmlv_usa_ese_valor(self):
        resultado = calcular_ibc_seguridad_social_domestico(
            salario_proporcional=Decimal("1300000.00"), smmlv_mensual=Decimal("1300000.00")
        )
        assert resultado == Decimal("1300000.00")

    def test_salario_proporcional_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            calcular_ibc_seguridad_social_domestico(
                salario_proporcional=Decimal("-1"), smmlv_mensual=Decimal("1300000.00")
            )

    def test_smmlv_cero_o_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            calcular_ibc_seguridad_social_domestico(
                salario_proporcional=Decimal("1000000.00"), smmlv_mensual=Decimal("0")
            )
