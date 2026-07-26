from decimal import Decimal

from app.engine.costs.agencias_en_derecho import (
    CuantiaTier,
    Instancia,
    RangoTarifa,
    TipoProceso,
    TOPE_MAXIMO_SMLMV,
    UMBRAL_MENOR_CUANTIA_SMLMV,
    UMBRAL_MINIMA_CUANTIA_SMLMV,
    UnidadTarifa,
    TARIFAS_AGENCIAS_EN_DERECHO,
    _interpolar_dentro_de_rango,
    resolver_cuantia_tier,
)

_SMLMV_2024 = Decimal("1300000.00")  # historical_index._SMLMV_POR_ANIO[2024]


def test_umbrales_cgp_articulo_25():
    # Verificados contra Ley 1564 de 2012 art. 25 (ver spec, "Fuentes externas").
    assert UMBRAL_MINIMA_CUANTIA_SMLMV == Decimal("40")
    assert UMBRAL_MENOR_CUANTIA_SMLMV == Decimal("150")


def test_tope_maximo_paragrafo_3_articulo_3():
    assert TOPE_MAXIMO_SMLMV == Decimal("20")


def test_declarativo_general_unica_instancia_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, CuantiaTier.MINIMA, True)
    ]
    assert rango == RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_unica_instancia_no_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, None, False)
    ]
    assert rango == RangoTarifa(Decimal("1"), Decimal("8"), UnidadTarifa.SMLMV)


def test_declarativo_general_primera_instancia_menor_cuantia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MENOR, True)
    ]
    assert rango == RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_primera_instancia_mayor_cuantia():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MAYOR, True)
    ]
    assert rango == RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE)


def test_declarativo_general_primera_instancia_no_pecuniaria():
    rango = TARIFAS_AGENCIAS_EN_DERECHO[
        (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, None, False)
    ]
    assert rango == RangoTarifa(Decimal("1"), Decimal("10"), UnidadTarifa.SMLMV)


def test_declarativo_general_segunda_instancia():
    for pecuniaria in (True, False):
        rango = TARIFAS_AGENCIAS_EN_DERECHO[
            (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, pecuniaria)
        ]
        assert rango == RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV)


def test_resolver_cuantia_tier_minima_dentro_del_limite():
    # 40 SMLMV exactos = limite superior de minima cuantia (CGP art. 25: "no exceda").
    assert resolver_cuantia_tier(Decimal("52000000.00"), _SMLMV_2024) == CuantiaTier.MINIMA


def test_resolver_cuantia_tier_menor_justo_sobre_el_limite_de_minima():
    assert resolver_cuantia_tier(Decimal("52000001.00"), _SMLMV_2024) == CuantiaTier.MENOR


def test_resolver_cuantia_tier_menor_en_su_limite_superior():
    # 150 SMLMV exactos = limite superior de menor cuantia.
    assert resolver_cuantia_tier(Decimal("195000000.00"), _SMLMV_2024) == CuantiaTier.MENOR


def test_resolver_cuantia_tier_mayor_justo_sobre_el_limite_de_menor():
    assert resolver_cuantia_tier(Decimal("195000001.00"), _SMLMV_2024) == CuantiaTier.MAYOR


def test_resolver_cuantia_tier_mayor_valor_grande():
    assert resolver_cuantia_tier(Decimal("5000000000.00"), _SMLMV_2024) == CuantiaTier.MAYOR


def test_interpolar_en_el_piso_del_tier_da_el_porcentaje_maximo():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("0"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("7.5")


def test_interpolar_en_el_techo_del_tier_da_el_porcentaje_minimo():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("100"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("3")


def test_interpolar_en_el_punto_medio():
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("50"), floor=Decimal("0"), ceiling=Decimal("100"),
    )
    assert resultado == Decimal("5.25")


def test_interpolar_sin_techo_devuelve_siempre_el_minimo():
    # Tier "mayor cuantia" no tiene limite superior (CGP art. 25) -- no hay
    # base matematica para interpolar contra el infinito, se usa el minimo
    # del rango (el extremo de "a mayor valor, menor porcentaje" llevado al
    # limite). Documentado en el design spec como aproximacion explicita.
    resultado = _interpolar_dentro_de_rango(
        minimo=Decimal("3"), maximo=Decimal("7.5"),
        valor=Decimal("999999999"), floor=Decimal("100"), ceiling=None,
    )
    assert resultado == Decimal("3")
