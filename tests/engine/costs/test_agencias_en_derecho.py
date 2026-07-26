from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.exceptions import TarifaNoDisponibleError
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
    calcular_agencias_en_derecho,
    resolver_cuantia_tier,
)
from database.models import Base, ParametroLegal

_SMLMV_2024 = Decimal("1300000.00")  # historical_index._SMLMV_POR_ANIO[2024]


@pytest.fixture(autouse=True)
def _db_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=_SMLMV_2024, vigente_desde=date(2024, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


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


def test_calcular_minima_cuantia_declarativo_unica_instancia():
    # Punto medio del tier minima (0 a 52.000.000): 26.000.000 -> posicion=0.5
    # -> pct = 15 - 0.5*10 = 10% -> 2.600.000
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.UNICA,
        pretensiones_reconocidas=Decimal("26000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("2600000.00")


def test_calcular_menor_cuantia_cerca_del_piso_del_tier_da_un_porcentaje_alto():
    # 87.750.000 esta al 25% del recorrido del tier menor cuantia (52.000.000
    # a 195.000.000): posicion=0.25 -> pct = 10 - 0.25*6 = 8.5%. No se usa
    # exactamente el piso (52.000.000 = 40 SMLMV) porque ese valor cae en el
    # limite inclusivo de minima cuantia (resolver_cuantia_tier usa "<="), no
    # en menor cuantia -- la matematica exacta del piso/techo ya esta cubierta
    # por los tests puros de _interpolar_dentro_de_rango (Task 3).
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("87750000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("7458750.00")  # 87.750.000 * 8.5%


def test_calcular_menor_cuantia_en_el_techo_del_tier_da_el_porcentaje_minimo():
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("195000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("7800000.00")  # 195.000.000 * 4%


def test_calcular_mayor_cuantia_usa_siempre_el_porcentaje_minimo():
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("300000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("9000000.00")  # 300.000.000 * 3%


def test_calcular_aplica_tope_de_20_smlmv():
    # 3% de 1.000.000.000 = 30.000.000, pero el tope es 20 * 1.300.000 = 26.000.000.
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("1000000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    assert resultado == Decimal("26000000.00")


def test_calcular_no_pecuniaria_usa_punto_medio_en_smlmv():
    # Primera instancia, sin pretension pecuniaria: 1-10 SMLMV -> punto medio 5.5 SMLMV.
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.PRIMERA,
        pretensiones_reconocidas=Decimal("1.00"), fecha_radicacion=date(2024, 6, 1),
        tiene_pretension_pecuniaria=False,
    )
    assert resultado == Decimal("7150000.00")  # 5.5 * 1.300.000


def test_calcular_pretensiones_no_positivas_lanza_value_error():
    with pytest.raises(ValueError):
        calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso.DECLARATIVO_GENERAL, instancia=Instancia.UNICA,
            pretensiones_reconocidas=Decimal("0.00"), fecha_radicacion=date(2024, 6, 1),
        )


def test_calcular_combinacion_no_registrada_lanza_tarifa_no_disponible():
    with pytest.raises(TarifaNoDisponibleError):
        calcular_agencias_en_derecho(
            tipo_proceso=TipoProceso.EXPROPIACION, instancia=Instancia.UNICA,
            pretensiones_reconocidas=Decimal("10000000.00"), fecha_radicacion=date(2024, 6, 1),
        )


def test_calcular_tarifa_tier_agnostica_no_interpola_incluso_con_pretension_grande(monkeypatch):
    # Regresion: una tarifa que no distingue por cuantia (ej. MONITORIO, "hasta
    # el 5%") no debe interpolarse usando los limites del tier resuelto -- debe
    # usar el punto medio del rango sin importar que tan grande sea la pretension.
    clave = (TipoProceso.MONITORIO, Instancia.UNICA, None, True)
    monkeypatch.setitem(
        TARIFAS_AGENCIAS_EN_DERECHO, clave,
        RangoTarifa(Decimal("0"), Decimal("5"), UnidadTarifa.PORCENTAJE),
    )
    resultado = calcular_agencias_en_derecho(
        tipo_proceso=TipoProceso.MONITORIO, instancia=Instancia.UNICA,
        pretensiones_reconocidas=Decimal("300000000.00"), fecha_radicacion=date(2024, 6, 1),
    )
    # punto medio del rango (2.5%) * 300.000.000 = 7.500.000,00 -- NO cero.
    assert resultado == Decimal("7500000.00")
