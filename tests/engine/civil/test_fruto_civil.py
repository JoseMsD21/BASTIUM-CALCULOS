"""Sprint 100 -- beneficio dejado de percibir como fruto civil (Art. 964 C.C.).

Valores esperados calculados a mano con la serie IPC mensual real del DANE
(`_IPC_MENSUAL`, base Dic-2018 = 100): ene-2019 = 100,60; feb-2019 = 101,18;
mar-2019 = 101,62; abr-2019 = 102,12; dic-2018 = 100,00.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.civil.fruto_civil import GastoConservacion, calcular_fruto_civil

CANON = Decimal("1000000.00")


def test_tres_meses_completos_con_gasto_mensual():
    # Referencia 31/01/2019 (ultimo dia del mes -> IPC ene-2019 = 100,60 sin interpolar).
    # Feb: 1.000.000 x 101,18/100,60 = 1.005.765,4075... -> 1.005.765,41
    # Mar: 1.000.000 x 101,62/100,60 = 1.010.139,1650... -> 1.010.139,17
    # Abr: 1.000.000 x 102,12/100,60 = 1.015.109,3439... -> 1.015.109,34
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 31),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 4, 30),
        gasto_conservacion_mensual=Decimal("100000.00"),
    )

    assert [(m.anio, m.mes) for m in resultado.meses] == [(2019, 2), (2019, 3), (2019, 4)]
    assert resultado.ipc_referencia == Decimal("100.60")
    assert [m.ipc_mes for m in resultado.meses] == [
        Decimal("101.18"),
        Decimal("101.62"),
        Decimal("102.12"),
    ]
    assert [m.canon_indexado_mes for m in resultado.meses] == [
        Decimal("1005765.41"),
        Decimal("1010139.17"),
        Decimal("1015109.34"),
    ]
    # Meses completos: el canon del periodo es el canon indexado del mes entero.
    assert [m.canon_periodo for m in resultado.meses] == [
        Decimal("1005765.41"),
        Decimal("1010139.17"),
        Decimal("1015109.34"),
    ]
    assert all(m.gastos_conservacion == Decimal("100000.00") for m in resultado.meses)
    assert [m.fruto_neto for m in resultado.meses] == [
        Decimal("905765.41"),
        Decimal("910139.17"),
        Decimal("915109.34"),
    ]
    assert resultado.total_canon == Decimal("3031013.92")
    assert resultado.total_gastos_conservacion == Decimal("300000.00")
    assert resultado.total_fruto_civil == Decimal("2731013.92")
    assert resultado.serie_ipc == "MENSUAL"


def test_prorrateo_primer_y_ultimo_mes_por_dias_calendario():
    # 15/02/2019 a 10/03/2019 (ambos inclusive).
    # Feb: 14 de 28 dias -> 1.005.765,41 x 14/28 = 502.882,705 -> 502.882,71;
    #      gasto 100.000 x 14/28 = 50.000,00 -> neto 452.882,71
    # Mar: 10 de 31 dias -> 1.010.139,17 x 10/31 = 325.851,3452 -> 325.851,35;
    #      gasto 100.000 x 10/31 = 32.258,0645 -> 32.258,06 -> neto 293.593,29
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 31),
        fecha_inicial=date(2019, 2, 15),
        fecha_final=date(2019, 3, 10),
        gasto_conservacion_mensual=Decimal("100000.00"),
    )

    feb, mar = resultado.meses
    assert (feb.desde, feb.hasta, feb.dias, feb.dias_mes) == (
        date(2019, 2, 15),
        date(2019, 2, 28),
        14,
        28,
    )
    assert (mar.desde, mar.hasta, mar.dias, mar.dias_mes) == (
        date(2019, 3, 1),
        date(2019, 3, 10),
        10,
        31,
    )
    assert feb.canon_periodo == Decimal("502882.71")
    assert feb.gastos_conservacion == Decimal("50000.00")
    assert feb.fruto_neto == Decimal("452882.71")
    assert mar.canon_periodo == Decimal("325851.35")
    assert mar.gastos_conservacion == Decimal("32258.06")
    assert mar.fruto_neto == Decimal("293593.29")
    assert resultado.total_fruto_civil == Decimal("746476.00")


def test_periodo_dentro_de_un_solo_mes():
    # 01/02/2019 a 07/02/2019: 7 de 28 dias -> 1.005.765,41 / 4 = 251.441,3525 -> 251.441,35
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 31),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 2, 7),
    )
    (feb,) = resultado.meses
    assert feb.dias == 7
    assert feb.canon_periodo == Decimal("251441.35")
    assert feb.gastos_conservacion == Decimal("0.00")
    assert resultado.total_fruto_civil == Decimal("251441.35")


def test_fecha_de_referencia_a_mitad_de_mes_usa_ipc_interpolado_por_dias():
    # IPC al 15/01/2019 = (15 x 100,60 + 16 x 100,00) / 31 = 100,290322...
    # Feb: 1.000.000 x 101,18 / 100,290322... = 1.008.871,02
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 15),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 2, 28),
    )
    assert resultado.ipc_referencia.quantize(Decimal("0.000001")) == Decimal("100.290323")
    assert resultado.meses[0].canon_indexado_mes == Decimal("1008871.02")


def test_referencia_posterior_al_periodo_retrotrae_el_canon_sin_piso():
    # Canon de mercado certificado al 30/04/2019 (IPC 102,12) y privacion en feb-2019:
    # 1.000.000 x 101,18/102,12 = 990.795,14 (razon pura, sin el piso de deflacion de
    # IPCIndexation.calculate: aqui se lleva el canon al nivel de precios de cada mes).
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 4, 30),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 2, 28),
    )
    assert resultado.meses[0].canon_indexado_mes == Decimal("990795.14")


def test_gastos_de_conservacion_por_fecha_se_descuentan_en_su_mes():
    # Gasto puntual de 200.000 el 05/03/2019 -> solo en marzo, sin prorrateo.
    # Mas uno mensual de 100.000 (marzo completo) -> 300.000 en marzo.
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 31),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 3, 31),
        gasto_conservacion_mensual=Decimal("100000.00"),
        gastos_conservacion=[GastoConservacion(fecha=date(2019, 3, 5), monto=Decimal("200000"))],
    )
    feb, mar = resultado.meses
    assert feb.gastos_conservacion == Decimal("100000.00")
    assert mar.gastos_conservacion == Decimal("300000.00")
    assert mar.fruto_neto == Decimal("710139.17")
    assert resultado.total_gastos_conservacion == Decimal("400000.00")
    assert resultado.total_fruto_civil == Decimal("1615904.58")


def test_gastos_mayores_que_el_canon_dan_neto_negativo_sin_ocultarlo():
    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2019, 1, 31),
        fecha_inicial=date(2019, 2, 1),
        fecha_final=date(2019, 2, 28),
        gastos_conservacion=[GastoConservacion(fecha=date(2019, 2, 10), monto=Decimal("1500000"))],
    )
    assert resultado.meses[0].fruto_neto == Decimal("-494234.59")
    assert resultado.total_fruto_civil == Decimal("-494234.59")


@pytest.fixture
def _parametros_legales_en_memoria():
    # La interpolacion anual lee IPC_INDICE_ACUMULADO de parametros_legales.
    from scripts.migrate_parametros_legales import migrar

    migrar()


@pytest.mark.usefixtures("_parametros_legales_en_memoria")
def test_fecha_anterior_a_2003_hace_fallback_anual_para_todas_las_fechas():
    from app.engine.indexation.historical_index import get_ipc_interpolado_for_date

    resultado = calcular_fruto_civil(
        canon_mensual=CANON,
        fecha_referencia=date(2002, 6, 30),
        fecha_inicial=date(2003, 1, 1),
        fecha_final=date(2003, 1, 31),
    )
    assert resultado.serie_ipc == "ANUAL"
    ipc_ref = get_ipc_interpolado_for_date(date(2002, 6, 30))
    ipc_mes = get_ipc_interpolado_for_date(date(2003, 1, 31))
    assert resultado.ipc_referencia == ipc_ref
    esperado = (CANON * ipc_mes / ipc_ref).quantize(Decimal("0.01"))
    assert resultado.meses[0].canon_indexado_mes == esperado


@pytest.mark.parametrize(
    "kwargs",
    [
        {"canon_mensual": Decimal("-1")},
        {"fecha_final": date(2019, 1, 31)},
        {"gasto_conservacion_mensual": Decimal("-1")},
        {"gastos_conservacion": [GastoConservacion(fecha=date(2019, 5, 1), monto=Decimal("1"))]},
        {"gastos_conservacion": [GastoConservacion(fecha=date(2019, 2, 3), monto=Decimal("-1"))]},
    ],
)
def test_validaciones(kwargs):
    base = {
        "canon_mensual": CANON,
        "fecha_referencia": date(2019, 1, 31),
        "fecha_inicial": date(2019, 2, 1),
        "fecha_final": date(2019, 2, 28),
    }
    base.update(kwargs)
    with pytest.raises(ValueError):
        calcular_fruto_civil(**base)
