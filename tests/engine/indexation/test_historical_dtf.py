"""Tests de la serie historica semanal de DTF (Sprint 82).

Los valores puntuales se verificaron a mano contra
docs/Archivos de referencia abogado/_markdown/historicodtf.md (columna DTF a
90 dias), no solo contra el propio modulo bajo prueba -- ver
app/engine/indexation/historical_dtf.py para el detalle de como se extrajo
y verifico la serie completa.

Este modulo NO esta conectado a ningun motor de liquidacion: solo prueba
que la serie este cargada y sea consultable por fecha, tal como pide la
Definicion de Hecho del Sprint 82.
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.indexation.historical_dtf import _DTF_SEMANAL, get_dtf_for_date


def test_dtf_primera_fecha_disponible_1984_01_20():
    # Primera fila de la fuente: 1984/01/20 | 36.45
    assert get_dtf_for_date(date(1984, 1, 20)) == Decimal("36.45")


def test_dtf_fecha_mas_reciente_disponible_2026_02_27():
    # Ultima fila de la fuente: 2026/02/27 | 9.59
    assert get_dtf_for_date(date(2026, 2, 27)) == Decimal("9.59")


def test_dtf_valor_puntual_1985_12_20():
    # Fuente: 1985/12/20 | 36.62
    assert get_dtf_for_date(date(1985, 12, 20)) == Decimal("36.62")


def test_dtf_valor_puntual_1993_08_20():
    # Fuente: 1993/08/20 | 24.6
    assert get_dtf_for_date(date(1993, 8, 20)) == Decimal("24.6")


def test_dtf_valor_puntual_2003_03_21():
    # Fuente: 2003/03/21 | 7.75
    assert get_dtf_for_date(date(2003, 3, 21)) == Decimal("7.75")


def test_dtf_valor_puntual_2012_10_19():
    # Fuente: 2012/10/19 | 5.23
    assert get_dtf_for_date(date(2012, 10, 19)) == Decimal("5.23")


def test_dtf_fecha_anterior_a_la_primera_disponible_lanza_value_error():
    with pytest.raises(ValueError):
        get_dtf_for_date(date(1983, 12, 31))
    with pytest.raises(ValueError):
        get_dtf_for_date(date(1984, 1, 19))


def test_dtf_fecha_intermedia_usa_la_certificacion_anterior_no_la_siguiente():
    # Entre 1984/01/20 (36.45) y 1984/01/27 (36.21): una fecha intermedia
    # debe seguir "vigente" con la tasa de la certificacion ANTERIOR hasta
    # que llegue la siguiente (mismo criterio que MemoryRateProvider), no
    # adelantarse a la certificacion que todavia no ha llegado.
    assert get_dtf_for_date(date(1984, 1, 22)) == Decimal("36.45")
    assert get_dtf_for_date(date(1984, 1, 26)) == Decimal("36.45")
    # El dia exacto de la siguiente certificacion ya usa el valor nuevo.
    assert get_dtf_for_date(date(1984, 1, 27)) == Decimal("36.21")


def test_dtf_serie_cargada_sin_huecos_semanales():
    # Definicion de Hecho: "serie cargada y consultable" -- verifica que la
    # tabla en memoria efectivamente tiene las 2198 fechas semanales
    # esperadas entre el primer y el ultimo dato de la fuente, sin huecos.
    assert len(_DTF_SEMANAL) == 2198
    assert min(_DTF_SEMANAL) == date(1984, 1, 20)
    assert max(_DTF_SEMANAL) == date(2026, 2, 27)
