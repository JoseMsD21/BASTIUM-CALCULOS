"""Sprint 70/91 (seguimiento, respuesta del despacho 16/11/2026): router de
regimen pensional por fecha de causacion, con las fechas exactas de entrada
en vigencia confirmadas por el despacho:

- Ley 33 de 1985: 13/02/1985.
- Ley 71 de 1988: 28/01/1989 (mismo regimen de tasa fija 75% que la Ley 33).
- Acuerdo 049 de 1990 (Dec. 758/1990): 18/04/1990.
- Ley 100 de 1993: 01/04/1994 (sector privado/nacional).
- Ley 797 de 2003: 29/01/2003.

Todos los valores esperados se calcularon a mano en los comentarios."""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.vigencia_pensional import (
    RegimenPensional,
    calcular_tasa_reemplazo_por_fecha,
    regimen_por_fecha,
)


@pytest.mark.parametrize(
    ("fecha", "regimen_esperado", "norma_esperada"),
    [
        # Limite inferior exacto de cada regimen (dia de entrada en vigencia).
        (date(1985, 2, 13), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 33 de 1985"),
        (date(1989, 1, 28), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 71 de 1988"),
        (date(1990, 4, 18), RegimenPensional.ISS_ACUERDO_049_1990, "Acuerdo 049 de 1990"),
        (date(1994, 4, 1), RegimenPensional.LEY_100_1993_ORIGINAL, "Ley 100 de 1993"),
        (date(2003, 1, 29), RegimenPensional.LEY_797_2003, "Ley 797 de 2003"),
        # Ultimo dia de cada regimen (el dia anterior a la vigencia del siguiente).
        (date(1989, 1, 27), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 33 de 1985"),
        (date(1990, 4, 17), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 71 de 1988"),
        (date(1994, 3, 31), RegimenPensional.ISS_ACUERDO_049_1990, "Acuerdo 049 de 1990"),
        (date(2003, 1, 28), RegimenPensional.LEY_100_1993_ORIGINAL, "Ley 100 de 1993"),
        # Ejemplos del usuario (Pendientes.md, Sprint 70): 1997 -> Ley 100; 2024 -> Ley 797.
        (date(1997, 6, 15), RegimenPensional.LEY_100_1993_ORIGINAL, "Ley 100 de 1993"),
        (date(2024, 6, 15), RegimenPensional.LEY_797_2003, "Ley 797 de 2003"),
    ],
)
def test_regimen_por_fecha_usa_fechas_exactas(fecha, regimen_esperado, norma_esperada):
    vigencia = regimen_por_fecha(fecha)

    assert vigencia.regimen is regimen_esperado
    assert vigencia.norma == norma_esperada


def test_regimen_por_fecha_devuelve_fecha_desde_de_la_norma():
    assert regimen_por_fecha(date(1997, 6, 15)).fecha_desde == date(1994, 4, 1)
    assert regimen_por_fecha(date(1989, 6, 1)).fecha_desde == date(1989, 1, 28)


def test_regimen_por_fecha_anterior_a_ley_33_de_1985_lanza_error():
    # Ningun regimen confirmado por el despacho cubre causaciones anteriores al 13/02/1985.
    with pytest.raises(ValueError):
        regimen_por_fecha(date(1985, 2, 12))


def test_tasa_por_fecha_ley_33_1985_fija_75():
    assert calcular_tasa_reemplazo_por_fecha(date(1987, 5, 1), semanas_cotizadas=1000) == Decimal(
        "75.00"
    )


def test_tasa_por_fecha_iss_acuerdo_049_700_semanas():
    # 700 - 500 = 200 -> 4 bloques x 3% = 12% -> 45 + 12 = 57%.
    assert calcular_tasa_reemplazo_por_fecha(date(1992, 3, 10), semanas_cotizadas=700) == Decimal(
        "57.00"
    )


def test_tasa_por_fecha_ley_100_original_1997_1300_semanas():
    # 1000-1200: 4 bloques x 2% = 8%; 1200-1300: 2 bloques x 3% = 6% -> 65 + 14 = 79%.
    assert calcular_tasa_reemplazo_por_fecha(date(1997, 6, 15), semanas_cotizadas=1300) == Decimal(
        "79.00"
    )


def test_tasa_por_fecha_ley_797_2024_usa_formula_vigente():
    # IBL = 2 SMLMV -> s = 2 -> r = 65.5 - 1 = 64.5%. 2024 exige 1300 semanas;
    # 1400 cotizadas -> 2 bloques de 50 -> +3% -> 67.5%.
    tasa = calcular_tasa_reemplazo_por_fecha(
        date(2024, 6, 15),
        semanas_cotizadas=1400,
        ibl=Decimal("2600000.00"),
        smlmv_vigente=Decimal("1300000.00"),
    )
    assert tasa == Decimal("67.50")


def test_tasa_por_fecha_ley_797_sin_ibl_o_smlmv_lanza_error():
    # La formula de la Ley 797/2003 depende de s = IBL / SMLMV: sin esos datos no se adivina.
    with pytest.raises(ValueError):
        calcular_tasa_reemplazo_por_fecha(date(2024, 6, 15), semanas_cotizadas=1400)
