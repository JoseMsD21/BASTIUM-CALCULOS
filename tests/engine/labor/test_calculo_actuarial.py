"""Sprints 86/87: motor de calculo actuarial del Decreto 1296 de 2022.

Datos y formulas de la respuesta del despacho del 16/11/2026
(docs/Preguntas-Para-Abogado-Respondidas.md, "Sprint 86/87 (seguimiento)").
Los dias entre fechas se contaron a mano (en comentarios); los valores
esperados se recalculan aqui en una linea con Decimal reproduciendo la
formula del decreto, nunca copiados de la salida del motor.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.calculo_actuarial import (
    Sexo,
    actualizar_reserva_dtf_pensional,
    calcular_auxilio_funerario_referencia,
    calcular_fac3,
    calcular_fac3_con_tiempo_previo,
    calcular_fac3_estandar,
    calcular_reserva_actuarial,
    calcular_salario_referencia,
    factor_dtf_pensional,
    factores_fac1_fac2,
    interpolar_por_dias,
    salario_medio_nacional,
)
from app.engine.labor.tablas_actuariales import (
    FAC1_FAC2_POR_EDAD,
    SALARIO_MEDIO_NACIONAL_POR_EDAD,
)

D = Decimal
Q15 = D("0.000000000000001")


def _q(valor: Decimal) -> Decimal:
    return valor.quantize(Q15)


# --------------------------------------------------------------------------
# Tablas transcritas
# --------------------------------------------------------------------------


def test_tabla_2_cubre_55_a_90_y_trae_los_valores_de_la_fuente():
    assert sorted(FAC1_FAC2_POR_EDAD) == list(range(55, 91))
    f55 = FAC1_FAC2_POR_EDAD[55]
    assert (f55.fac1_hombres, f55.fac1_mujeres) == (D("258.712212"), D("243.005182"))
    assert (f55.fac2_hombres, f55.fac2_mujeres) == (D("0.369543"), D("0.311687"))
    f90 = FAC1_FAC2_POR_EDAD[90]
    assert (f90.fac1_hombres, f90.fac1_mujeres) == (D("100.661169"), D("75.516659"))
    assert (f90.fac2_hombres, f90.fac2_mujeres) == (D("0.811453"), D("0.789343"))
    f72 = FAC1_FAC2_POR_EDAD[72]
    assert (f72.fac1_hombres, f72.fac2_mujeres) == (D("194.283137"), D("0.528734"))


def test_tabla_1_smn_cubre_12_a_71_y_trae_los_valores_de_la_fuente():
    assert sorted(SALARIO_MEDIO_NACIONAL_POR_EDAD) == list(range(12, 72))
    assert SALARIO_MEDIO_NACIONAL_POR_EDAD[12] == D("1.000000")
    assert SALARIO_MEDIO_NACIONAL_POR_EDAD[14] == D("1.135599")
    assert SALARIO_MEDIO_NACIONAL_POR_EDAD[46] == D("3.073323")
    assert SALARIO_MEDIO_NACIONAL_POR_EDAD[71] == D("1.715798")


# --------------------------------------------------------------------------
# Interpolacion por dias entre cumpleaños: v0 = (d1*v2 + d2*v1)/(d1+d2)
# --------------------------------------------------------------------------


def test_interpolar_por_dias_formula_del_despacho():
    assert interpolar_por_dias(D("10"), D("20"), 1, 3) == (1 * D("20") + 3 * D("10")) / 4


def test_fac1_fac2_hombre_entre_cumpleanos():
    # Nacido 15/03/1970; fecha 10/09/2026 -> 56 años cumplidos el 15/03/2026.
    # d1 = 15/03/2026 -> 10/09/2026 = 16+30+31+30+31+31+10 = 179 dias.
    # d2 = 10/09/2026 -> 15/03/2027 = 365 - 179 = 186 dias.
    fac1, fac2 = factores_fac1_fac2(date(1970, 3, 15), date(2026, 9, 10), Sexo.HOMBRE)
    assert fac1 == (179 * D("252.738260") + 186 * D("255.775386")) / 365
    assert fac2 == (179 * D("0.393132") + 186 * D("0.381199")) / 365


def test_fac1_fac2_mujer_en_el_cumpleanos_es_el_valor_exacto_de_la_tabla():
    fac1, fac2 = factores_fac1_fac2(date(1966, 6, 1), date(2026, 6, 1), Sexo.MUJER)
    assert (fac1, fac2) == (D("224.606020"), D("0.367403"))  # 60 años, mujeres


def test_fac1_fac2_edad_90_exacta_permitida():
    fac1, fac2 = factores_fac1_fac2(date(1936, 1, 10), date(2026, 1, 10), Sexo.HOMBRE)
    assert (fac1, fac2) == (D("100.661169"), D("0.811453"))


@pytest.mark.parametrize(
    "fecha_calculo",
    [
        date(2026, 1, 9),  # 54 años y 364 dias
        date(2026, 1, 11),  # 90 años y 1 dia: necesitaria la edad 91
    ],
)
def test_fac1_fac2_fuera_de_55_a_90_es_error_explicito(fecha_calculo):
    nacimiento = date(1971, 1, 10) if fecha_calculo == date(2026, 1, 9) else date(1936, 1, 10)
    with pytest.raises(ValueError, match="55"):
        factores_fac1_fac2(nacimiento, fecha_calculo, Sexo.HOMBRE)


def test_nacido_29_de_febrero_cumple_el_28_en_año_no_bisiesto():
    # Nacido 29/02/1968; fecha 01/03/2026 -> ultimo cumpleaños 28/02/2026 (58 años).
    # d1 = 1 dia; d2 = 01/03/2026 -> 28/02/2027 = 364 dias.
    fac1, _ = factores_fac1_fac2(date(1968, 2, 29), date(2026, 3, 1), Sexo.HOMBRE)
    assert fac1 == (1 * D("246.355000") + 364 * D("249.598775")) / 365


def test_smn_entre_cumpleanos():
    # Nacido 01/07/1986; fecha 01/10/2026 -> 40 años (01/07/2026).
    # d1 = 31+31+30 = 92; d2 = 01/10/2026 -> 01/07/2027 = 92+181 = 273.
    smn = salario_medio_nacional(date(1986, 7, 1), date(2026, 10, 1))
    assert smn == (92 * D("2.992482") + 273 * D("2.959570")) / 365


def test_smn_70_años_interpola_con_la_fila_71_mas():
    # Nacido 01/01/1956; fecha 02/01/2026 -> 70 años, d1 = 1, d2 = 364.
    smn = salario_medio_nacional(date(1956, 1, 1), date(2026, 1, 2))
    assert smn == (1 * D("1.715798") + 364 * D("1.796985")) / 365


def test_smn_desde_71_años_es_constante():
    assert salario_medio_nacional(date(1940, 5, 5), date(2026, 8, 20)) == D("1.715798")


def test_smn_menor_de_12_años_es_error():
    with pytest.raises(ValueError, match="12"):
        salario_medio_nacional(date(2015, 1, 1), date(2026, 1, 1))


def test_fecha_de_calculo_anterior_al_nacimiento_es_error():
    with pytest.raises(ValueError):
        salario_medio_nacional(date(2000, 1, 1), date(1999, 1, 1))


# --------------------------------------------------------------------------
# FAC3
# --------------------------------------------------------------------------


def test_fac3_estandar():
    esperado = (D("1.03") ** D("10") - 1) / (D("1.03") ** D("15") - 1)
    assert _q(calcular_fac3_estandar(D("10"), D("5"))) == _q(esperado)


def test_fac3_estandar_redondea_t_a_6_decimales():
    t = D("10.123457")  # 10.1234567 redondeado a 6 decimales
    esperado = (D("1.03") ** t - 1) / (D("1.03") ** (t + D("4.5")) - 1)
    assert _q(calcular_fac3_estandar(D("10.1234567"), D("4.5"))) == _q(esperado)


def test_fac3_con_tiempo_previo():
    esperado = ((D("1.03") ** D("12") - 1) / D("12")) / ((D("1.03") ** D("17") - 1) / D("17"))
    assert _q(calcular_fac3_con_tiempo_previo(D("12"), D("5"))) == _q(esperado)


def test_fac3_selector_sin_previos_usa_estandar_y_con_previos_usa_t1():
    assert calcular_fac3(D("10"), D("5")) == calcular_fac3_estandar(D("10"), D("5"))
    assert calcular_fac3(D("10"), D("5"), tiempos_previos=D("2")) == (
        calcular_fac3_con_tiempo_previo(D("12"), D("5"))
    )


@pytest.mark.parametrize(
    ("t", "n"), [(D("-1"), D("5")), (D("1"), D("-5")), (D("0"), D("0"))]
)
def test_fac3_estandar_rechaza_tiempos_invalidos(t, n):
    with pytest.raises(ValueError):
        calcular_fac3_estandar(t, n)


def test_fac3_con_tiempo_previo_rechaza_t1_cero():
    with pytest.raises(ValueError):
        calcular_fac3_con_tiempo_previo(D("0"), D("5"))


# --------------------------------------------------------------------------
# Auxilio funerario, salario de referencia, VRA / CA / VR
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("pr", "esperado"),
    [
        (D("3000000"), D("5000000.00")),  # PR < 5 SMLV -> 5 SMLV
        (D("5000000"), D("5000000.00")),  # PR = 5 SMLV -> PR
        (D("7000000"), D("7000000.00")),  # entre 5 y 10 SMLV -> PR
        (D("10000000"), D("10000000.00")),  # PR = 10 SMLV -> PR
        (D("12000000"), D("10000000.00")),  # PR > 10 SMLV -> 10 SMLV
    ],
)
def test_auxilio_funerario_de_referencia(pr, esperado):
    assert calcular_auxilio_funerario_referencia(pr, D("1000000")) == esperado


def test_salario_de_referencia():
    sr = calcular_salario_referencia(D("2000000"), D("2.568691"), D("2.809030"))
    # 2.000.000 * 2,568691 = 5.137.382; / 2,809030 = 1.828.881,14 (a mano)
    assert sr == (D("2000000") * D("2.568691") / D("2.809030")).quantize(D("0.01"))
    assert sr == D("1828881.14")


def test_reserva_actuarial_vra_ca_vr():
    fac3 = D("0.5")
    resultado = calcular_reserva_actuarial(
        fac1=D("258.712212"), fac2=D("0.369543"), pr=D("1500000"), ar=D("7117500"), fac3=fac3
    )
    vra = (D("258.712212") * 1500000 + D("0.369543") * 7117500) * fac3
    # 258.712212*1.500.000 = 388.068.318; 0,369543*7.117.500 = 2.630.222,3025
    # suma 390.698.540,3025 * 0,5 = 195.349.270,15125
    assert vra == D("195349270.15125")
    assert resultado.vra == D("195349270.15")
    assert resultado.ca == (D("0.005") * vra).quantize(D("0.01"))  # 976.746,35
    # VR = VRA + VRA*0,005/0,995 = 195.349.270,15125 + 981.654,62 = 196.330.924,775
    assert resultado.vr == (vra / D("0.995")).quantize(D("0.01"))
    assert resultado.vr == D("196330924.78")


def test_reserva_actuarial_rechaza_pr_negativa():
    with pytest.raises(ValueError):
        calcular_reserva_actuarial(
            fac1=D("1"), fac2=D("1"), pr=D("-1"), ar=D("1"), fac3=D("1")
        )


# --------------------------------------------------------------------------
# DTF pensional: 1.03 * (1 + INF_{año-1}/100), prorrateado por dias
# --------------------------------------------------------------------------


def test_dtf_pensional_año_completo():
    # 2025 completo (365 dias) usa el IPC 2024 = 5,20 %.
    factor = factor_dtf_pensional(date(2025, 1, 1), date(2026, 1, 1))
    assert _q(factor) == _q(D("1.03") * (1 + D("5.20") / 100))


def test_dtf_pensional_prorrateado_entre_dos_años():
    # 01/07/2024 -> 01/01/2025: 31+31+30+31+30+31 = 184 dias de 366 (IPC 2023 = 9,28 %).
    # 01/01/2025 -> 01/07/2025: 31+28+31+30+31+30 = 181 dias de 365 (IPC 2024 = 5,20 %).
    esperado = (D("1.03") * D("1.0928")) ** (D(184) / D(366)) * (
        (D("1.03") * D("1.052")) ** (D(181) / D(365))
    )
    factor = factor_dtf_pensional(date(2024, 7, 1), date(2025, 7, 1))
    assert _q(factor) == _q(esperado)


def test_dtf_pensional_con_serie_de_inflacion_propia():
    factor = factor_dtf_pensional(
        date(2030, 1, 1), date(2031, 1, 1), inflacion_anual={2029: D("4")}
    )
    assert _q(factor) == _q(D("1.03") * D("1.04"))


def test_dtf_pensional_misma_fecha_es_uno():
    assert factor_dtf_pensional(date(2025, 3, 3), date(2025, 3, 3)) == D("1")


def test_dtf_pensional_errores():
    with pytest.raises(ValueError, match="1994"):
        factor_dtf_pensional(date(1993, 12, 31), date(1995, 1, 1))
    with pytest.raises(ValueError):
        factor_dtf_pensional(date(2025, 1, 2), date(2025, 1, 1))
    with pytest.raises(ValueError, match="2030"):
        factor_dtf_pensional(date(2031, 1, 1), date(2031, 6, 1))


def test_actualizar_reserva_con_dtf_pensional():
    valor = actualizar_reserva_dtf_pensional(D("100000000"), date(2025, 1, 1), date(2026, 1, 1))
    # 100.000.000 * 1,03 * 1,052 = 108.356.000
    assert valor == D("108356000.00")
