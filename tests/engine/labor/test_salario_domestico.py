from decimal import Decimal

import pytest

from app.engine.labor.salario_domestico import (
    auxilio_transporte_domestico,
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


class TestAuxilioTransporteDomestico:
    """Sprint 96 (seguimiento), respuesta del despacho (23/08/2026): el auxilio
    de transporte se liquida "estricta y proporcionalmente a los dias
    efectivamente laborados en el mes (Auxilio_Mensual / 30) * Dias_Trabajados",
    solo para salarios de hasta 2 SMMLV. Dias trabajados en el mes = la misma
    conversion de la plantilla L2A: dias_laborados_semana / 7 x 30."""

    def test_tres_dias_por_semana_auxilio_2025(self):
        # Dias del mes = 3 / 7 x 30 = 12,857142...
        # (200.000 / 30) x 12,857142... = 200.000 x 3 / 7 = 85.714,2857... -> 85.714,29
        resultado = auxilio_transporte_domestico(
            auxilio_mensual=Decimal("200000"),
            dias_laborados_semana=3,
            salario_mensual_equivalente=Decimal("642857.14"),
            smmlv_mensual=Decimal("1423500"),
        )
        assert resultado == Decimal("85714.29")

    def test_tres_dias_por_semana_auxilio_2020(self):
        # 102.854 x 3 / 7 = 44.080,2857... -> 44.080,29
        resultado = auxilio_transporte_domestico(
            auxilio_mensual=Decimal("102854"),
            dias_laborados_semana=3,
            salario_mensual_equivalente=Decimal("642857.14"),
            smmlv_mensual=Decimal("877803"),
        )
        assert resultado == Decimal("44080.29")

    def test_siete_dias_por_semana_es_el_auxilio_mensual_completo(self):
        # 30 dias en el mes -> (200.000 / 30) x 30 = 200.000
        resultado = auxilio_transporte_domestico(
            auxilio_mensual=Decimal("200000"),
            dias_laborados_semana=7,
            salario_mensual_equivalente=Decimal("1500000.00"),
            smmlv_mensual=Decimal("1423500"),
        )
        assert resultado == Decimal("200000.00")

    def test_salario_igual_a_2_smmlv_si_causa_auxilio(self):
        # "hasta 2 SMMLV" incluye el limite: 2 x 1.423.500 = 2.847.000.
        # 200.000 x 5 / 7 = 142.857,1428... -> 142.857,14
        resultado = auxilio_transporte_domestico(
            auxilio_mensual=Decimal("200000"),
            dias_laborados_semana=5,
            salario_mensual_equivalente=Decimal("2847000.00"),
            smmlv_mensual=Decimal("1423500"),
        )
        assert resultado == Decimal("142857.14")

    def test_salario_mayor_a_2_smmlv_no_causa_auxilio(self):
        resultado = auxilio_transporte_domestico(
            auxilio_mensual=Decimal("200000"),
            dias_laborados_semana=5,
            salario_mensual_equivalente=Decimal("2847000.01"),
            smmlv_mensual=Decimal("1423500"),
        )
        assert resultado == Decimal("0.00")

    def test_dias_fuera_de_rango_lanza_error(self):
        with pytest.raises(ValueError):
            auxilio_transporte_domestico(
                auxilio_mensual=Decimal("200000"),
                dias_laborados_semana=0,
                salario_mensual_equivalente=Decimal("600000"),
                smmlv_mensual=Decimal("1423500"),
            )

    def test_auxilio_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            auxilio_transporte_domestico(
                auxilio_mensual=Decimal("-1"),
                dias_laborados_semana=3,
                salario_mensual_equivalente=Decimal("600000"),
                smmlv_mensual=Decimal("1423500"),
            )

    def test_smmlv_cero_lanza_error(self):
        with pytest.raises(ValueError):
            auxilio_transporte_domestico(
                auxilio_mensual=Decimal("200000"),
                dias_laborados_semana=3,
                salario_mensual_equivalente=Decimal("600000"),
                smmlv_mensual=Decimal("0"),
            )
