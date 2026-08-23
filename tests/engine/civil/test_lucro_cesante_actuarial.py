from decimal import Decimal

import pytest

from app.engine.civil.lucro_cesante_actuarial import (
    calcular_lucro_cesante_consolidado,
    calcular_lucro_cesante_futuro,
    interpolar_expectativa_vida_rentista,
)

TASA_MENSUAL_6_EA = Decimal("0.0048676")


def test_lucro_cesante_consolidado_caso_de_ejemplo():
    # Ra=1.000.000, i=0.0048676, n=12 -> factor = ((1+i)^12 - 1) / i
    resultado = calcular_lucro_cesante_consolidado(
        renta_actualizada_mensual=Decimal("1000000.00"),
        tasa_mensual=TASA_MENSUAL_6_EA,
        n_meses=Decimal("12"),
    )
    factor_esperado = (
        (Decimal("1") + TASA_MENSUAL_6_EA) ** Decimal("12") - Decimal("1")
    ) / TASA_MENSUAL_6_EA
    esperado = (Decimal("1000000.00") * factor_esperado).quantize(Decimal("0.01"))
    assert resultado == esperado
    # Sanity: para n=12 meses a una tasa baja, el consolidado debe superar
    # ligeramente 12 rentas simples (capitalizacion compuesta positiva).
    assert resultado > Decimal("1000000.00") * Decimal("12")


def test_lucro_cesante_futuro_caso_de_ejemplo():
    resultado = calcular_lucro_cesante_futuro(
        renta_actualizada_mensual=Decimal("1000000.00"),
        tasa_mensual=TASA_MENSUAL_6_EA,
        n_meses=Decimal("12"),
    )
    base = (Decimal("1") + TASA_MENSUAL_6_EA) ** Decimal("12")
    factor_esperado = (base - Decimal("1")) / (TASA_MENSUAL_6_EA * base)
    esperado = (Decimal("1000000.00") * factor_esperado).quantize(Decimal("0.01"))
    assert resultado == esperado
    # Sanity: el valor presente de una anualidad futura es menor que la suma
    # simple de las rentas (descuento por el valor del dinero en el tiempo).
    assert resultado < Decimal("1000000.00") * Decimal("12")


def test_lucro_cesante_futuro_es_siempre_menor_o_igual_al_consolidado_misma_renta_tasa_n():
    # Propiedad matematica: LCF = LCC / (1+i)^n -- el futuro descuenta el
    # consolidado al valor presente.
    consolidado = calcular_lucro_cesante_consolidado(
        renta_actualizada_mensual=Decimal("500000.00"),
        tasa_mensual=TASA_MENSUAL_6_EA,
        n_meses=Decimal("36"),
    )
    futuro = calcular_lucro_cesante_futuro(
        renta_actualizada_mensual=Decimal("500000.00"),
        tasa_mensual=TASA_MENSUAL_6_EA,
        n_meses=Decimal("36"),
    )
    assert futuro < consolidado


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "renta_actualizada_mensual": Decimal("-1"),
            "tasa_mensual": TASA_MENSUAL_6_EA,
            "n_meses": Decimal("12"),
        },
        {
            "renta_actualizada_mensual": Decimal("1000000"),
            "tasa_mensual": Decimal("0"),
            "n_meses": Decimal("12"),
        },
        {
            "renta_actualizada_mensual": Decimal("1000000"),
            "tasa_mensual": TASA_MENSUAL_6_EA,
            "n_meses": Decimal("0"),
        },
    ],
)
def test_lucro_cesante_consolidado_rechaza_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        calcular_lucro_cesante_consolidado(**kwargs)


@pytest.mark.parametrize(
    "kwargs",
    [
        {
            "renta_actualizada_mensual": Decimal("-1"),
            "tasa_mensual": TASA_MENSUAL_6_EA,
            "n_meses": Decimal("12"),
        },
        {
            "renta_actualizada_mensual": Decimal("1000000"),
            "tasa_mensual": Decimal("-1"),
            "n_meses": Decimal("12"),
        },
        {
            "renta_actualizada_mensual": Decimal("1000000"),
            "tasa_mensual": TASA_MENSUAL_6_EA,
            "n_meses": Decimal("-1"),
        },
    ],
)
def test_lucro_cesante_futuro_rechaza_parametros_invalidos(kwargs):
    with pytest.raises(ValueError):
        calcular_lucro_cesante_futuro(**kwargs)


class TestInterpolarExpectativaVidaRentista:
    """Sprint 97 (respuesta del despacho, 22/08/2026): interpolacion lineal
    entre las dos edades enteras que rodean la edad real, segun los meses."""

    TABLA = {33: Decimal("50.3"), 34: Decimal("49.5"), 60: Decimal("23.0")}

    def test_edad_exacta_sin_meses_retorna_el_valor_de_la_tabla(self):
        assert interpolar_expectativa_vida_rentista(self.TABLA, 60) == Decimal("23.0")

    def test_interpola_entre_dos_edades_segun_los_meses(self):
        # 33 años y 6 meses -> punto medio entre 50.3 y 49.5 -> 49.9
        resultado = interpolar_expectativa_vida_rentista(self.TABLA, 33, 6)
        assert resultado == Decimal("49.9")

    def test_interpola_con_fraccion_de_meses_no_entera(self):
        # 33 años y 3 meses -> 50.3 + (49.5-50.3)*3/12 = 50.3 - 0.2 = 50.1
        resultado = interpolar_expectativa_vida_rentista(self.TABLA, 33, 3)
        assert resultado == Decimal("50.1")

    def test_edad_sin_meses_fuera_de_la_tabla_lanza_error(self):
        with pytest.raises(ValueError):
            interpolar_expectativa_vida_rentista(self.TABLA, 45)

    def test_edad_con_meses_faltando_la_edad_siguiente_en_la_tabla_lanza_error(self):
        with pytest.raises(ValueError):
            interpolar_expectativa_vida_rentista(self.TABLA, 60, 6)

    def test_meses_fuera_de_rango_lanza_error(self):
        with pytest.raises(ValueError):
            interpolar_expectativa_vida_rentista(self.TABLA, 33, 12)
