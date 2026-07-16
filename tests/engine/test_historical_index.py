from datetime import date
from decimal import Decimal

import pytest

from app.engine.indexation.historical_index import (
    _IPC_VARIACION_ANUAL,
    get_ipc_for_date,
    get_smlmv_for_year,
)


def test_smlmv_2026_valor_conocido():
    assert get_smlmv_for_year(2026) == Decimal("1750905.00")


def test_smlmv_1984_primer_anio_disponible():
    assert get_smlmv_for_year(1984) == Decimal("11298.00")


def test_smlmv_fuera_de_rango_lanza_value_error():
    with pytest.raises(ValueError):
        get_smlmv_for_year(2027)
    with pytest.raises(ValueError):
        get_smlmv_for_year(1983)


def test_ipc_variacion_2025_valor_conocido():
    assert _IPC_VARIACION_ANUAL[2025] == Decimal("5.10")


def test_ipc_variacion_1967_primer_anio_disponible():
    assert _IPC_VARIACION_ANUAL[1967] == Decimal("7.90")


def test_ipc_ratio_entre_anios_consecutivos_coincide_con_la_variacion_publicada():
    ratio = get_ipc_for_date(date(2025, 12, 31)) / get_ipc_for_date(date(2024, 12, 31))
    assert ratio == Decimal("1") + Decimal("5.10") / Decimal("100")


def test_ipc_indice_acumulado_es_estrictamente_creciente():
    anios = sorted(_IPC_VARIACION_ANUAL)
    valores = [get_ipc_for_date(date(anio, 12, 31)) for anio in anios]
    assert valores == sorted(valores)
    assert len(set(valores)) == len(valores)


def test_ipc_fuera_de_rango_lanza_value_error():
    with pytest.raises(ValueError):
        get_ipc_for_date(date(1966, 12, 31))
    with pytest.raises(ValueError):
        get_ipc_for_date(date(2026, 1, 1))
