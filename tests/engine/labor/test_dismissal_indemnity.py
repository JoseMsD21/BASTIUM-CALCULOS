from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.dismissal_indemnity import (
    DismissalIndemnityCalculator,
    RegimenNoSoportadoError,
)
from database.models import TipoContratoLaboral

SALARIO = Decimal("3000000.00")
SMLMV_2026 = Decimal("1750905.00")  # 10 SMMLV(2026) = 17.509.050,00 -- SALARIO queda debajo


def _calcular(**overrides):
    base = dict(
        tipo_contrato=TipoContratoLaboral.INDEFINIDO,
        salario_mensual=SALARIO,
        fecha_ingreso=date(2020, 1, 1),
        fecha_terminacion=date(2021, 1, 1),
        despido_injustificado=True,
        smlmv_mensual=SMLMV_2026,
    )
    base.update(overrides)
    return DismissalIndemnityCalculator.calcular(**base)


def test_despido_con_justa_causa_no_genera_indemnizacion():
    resultado = _calcular(despido_injustificado=False)
    assert resultado.total == Decimal("0.00")
    assert resultado.dias_indemnizacion == Decimal("0")
    assert resultado.regimen == "NO_APLICA"


def test_indefinido_post_ley_50_1990_quiebre_exactamente_1_anio():
    # fecha_ingreso posterior al corte (1991-01-01) -> regimen post-Ley 50/1990.
    # antiguedad = 360 dias comerciales exactos (1 anio) -> 30 dias flat, sin
    # dias adicionales (la condicion del articulo es "mayor a un (1) año").
    resultado = _calcular(
        fecha_ingreso=date(2020, 1, 1),
        fecha_terminacion=date(2021, 1, 1),
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"
    assert resultado.dias_indemnizacion == Decimal("30")
    salario_diario = SALARIO / Decimal("30")
    assert resultado.total == (salario_diario * Decimal("30")).quantize(Decimal("0.01"))


def test_indefinido_post_ley_50_1990_justo_despues_del_quiebre_de_1_anio():
    # 361 dias comerciales -> ya "mayor a un (1) año": se suma la fraccion
    # proporcional del segundo año (1/360) a razon de 20 dias/año.
    resultado = _calcular(
        fecha_ingreso=date(2020, 1, 1),
        fecha_terminacion=date(2021, 1, 2),
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"
    dias_esperados = Decimal("30") + Decimal("20") * (Decimal("1") / Decimal("360"))
    assert resultado.dias_indemnizacion == dias_esperados


def test_indefinido_post_ley_50_1990_quiebre_5_anios():
    resultado = _calcular(
        fecha_ingreso=date(2015, 1, 1),
        fecha_terminacion=date(2020, 1, 1),  # exactamente 5 anios (1800 dias)
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"
    # 30 (primer año) + 20 * 4 (cuatro años subsiguientes) = 110
    assert resultado.dias_indemnizacion == Decimal("110")


def test_indefinido_post_ley_50_1990_quiebre_10_anios():
    resultado = _calcular(
        fecha_ingreso=date(2010, 1, 1),
        fecha_terminacion=date(2020, 1, 1),  # exactamente 10 anios (3600 dias)
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"
    # 30 + 20 * 9 = 210
    assert resultado.dias_indemnizacion == Decimal("210")


def test_indefinido_pre_ley_50_1990_quiebre_exactamente_1_anio():
    # fecha_ingreso anterior al corte (1991-01-01) -> regimen pre-Ley 50/1990
    # (45 dias primer año + 15 dias por año subsiguiente).
    resultado = _calcular(
        tipo_contrato=TipoContratoLaboral.INDEFINIDO,
        fecha_ingreso=date(1989, 1, 1),
        fecha_terminacion=date(1990, 1, 1),
    )
    assert resultado.regimen == "INDEFINIDO_PRE_LEY_50_1990"
    assert resultado.dias_indemnizacion == Decimal("45")


def test_indefinido_pre_ley_50_1990_quiebre_5_anios():
    resultado = _calcular(
        fecha_ingreso=date(1984, 1, 1),
        fecha_terminacion=date(1989, 1, 1),  # 5 anios
    )
    assert resultado.regimen == "INDEFINIDO_PRE_LEY_50_1990"
    # 45 + 15 * 4 = 105
    assert resultado.dias_indemnizacion == Decimal("105")


def test_indefinido_ingreso_exactamente_en_la_fecha_de_corte_es_regimen_post():
    resultado = _calcular(
        fecha_ingreso=date(1991, 1, 1),  # exactamente la fecha de corte por defecto
        fecha_terminacion=date(1992, 1, 1),
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"


def test_indefinido_umbral_10_smmlv_no_soportado():
    # Formula para salario >= 10 SMMLV no esta confirmada por el despacho
    # (ver docs/Preguntas-Para-Abogado-Abiertas.md, Sprint 92) -- debe fallar
    # explicitamente en vez de adivinar una cifra.
    with pytest.raises(RegimenNoSoportadoError):
        _calcular(
            salario_mensual=SMLMV_2026 * Decimal("10"),
            smlmv_mensual=SMLMV_2026,
        )


def test_indefinido_salario_justo_debajo_del_umbral_10_smmlv_si_se_soporta():
    resultado = _calcular(
        salario_mensual=SMLMV_2026 * Decimal("10") - Decimal("0.01"),
        smlmv_mensual=SMLMV_2026,
    )
    assert resultado.regimen == "INDEFINIDO_POST_LEY_50_1990"


def test_termino_fijo_usa_tiempo_restante_cuando_supera_el_piso():
    resultado = _calcular(
        tipo_contrato=TipoContratoLaboral.FIJO,
        fecha_ingreso=date(2024, 1, 1),
        fecha_terminacion=date(2024, 6, 1),
        fecha_fin_pactada=date(2025, 1, 1),  # faltan 214 dias, > piso de 15
    )
    assert resultado.regimen == "TERMINO_FIJO_OBRA_LABOR"
    dias_restantes = (date(2025, 1, 1) - date(2024, 6, 1)).days
    assert dias_restantes > 15
    assert resultado.dias_indemnizacion == Decimal(dias_restantes)


def test_termino_fijo_aplica_piso_de_15_dias():
    resultado = _calcular(
        tipo_contrato=TipoContratoLaboral.FIJO,
        fecha_ingreso=date(2024, 1, 1),
        fecha_terminacion=date(2024, 12, 25),
        fecha_fin_pactada=date(2025, 1, 1),  # faltan 7 dias, < piso de 15
    )
    assert resultado.regimen == "TERMINO_FIJO_OBRA_LABOR"
    assert resultado.dias_indemnizacion == Decimal("15")
    salario_diario = SALARIO / Decimal("30")
    assert resultado.total == (salario_diario * Decimal("15")).quantize(Decimal("0.01"))


def test_obra_labor_usa_la_misma_formula_que_termino_fijo():
    resultado = _calcular(
        tipo_contrato=TipoContratoLaboral.OBRA_LABOR,
        fecha_ingreso=date(2024, 1, 1),
        fecha_terminacion=date(2024, 12, 25),
        fecha_fin_pactada=date(2025, 1, 1),
    )
    assert resultado.regimen == "TERMINO_FIJO_OBRA_LABOR"
    assert resultado.dias_indemnizacion == Decimal("15")


def test_termino_fijo_sin_fecha_fin_pactada_lanza_error():
    with pytest.raises(ValueError, match="fecha_fin_pactada"):
        _calcular(
            tipo_contrato=TipoContratoLaboral.FIJO,
            fecha_ingreso=date(2024, 1, 1),
            fecha_terminacion=date(2024, 6, 1),
            fecha_fin_pactada=None,
        )


def test_termino_fijo_pactada_no_posterior_a_terminacion_lanza_error():
    with pytest.raises(ValueError, match="posterior"):
        _calcular(
            tipo_contrato=TipoContratoLaboral.FIJO,
            fecha_ingreso=date(2024, 1, 1),
            fecha_terminacion=date(2024, 6, 1),
            fecha_fin_pactada=date(2024, 6, 1),
        )


def test_indefinido_fecha_terminacion_no_posterior_a_ingreso_lanza_error():
    with pytest.raises(ValueError, match="posterior"):
        _calcular(
            fecha_ingreso=date(2020, 1, 1),
            fecha_terminacion=date(2020, 1, 1),
        )
