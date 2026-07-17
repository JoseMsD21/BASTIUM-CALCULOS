from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.engine.indexation.historical_index import (
    _IPC_VARIACION_ANUAL,
    _TRAMOS_IBC_USURA,
    get_ibc_usura_for_date,
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


def test_smlmv_2010_valor_conocido_interior_del_rango():
    # Chequeo puntual en la mitad de la serie (no solo en los extremos 1984/2026),
    # para detectar un error de transcripcion en un año intermedio.
    assert get_smlmv_for_year(2010) == Decimal("515000.00")


def test_ipc_variacion_2025_valor_conocido():
    assert _IPC_VARIACION_ANUAL[2025] == Decimal("5.10")


def test_ipc_variacion_1967_primer_anio_disponible():
    assert _IPC_VARIACION_ANUAL[1967] == Decimal("7.90")


def test_ipc_variacion_valores_conocidos_en_anios_interiores():
    # test_ipc_ratio_entre_anios_consecutivos... solo confirma el ultimo eslabon
    # de la cadena (2024->2025), y una entrada intermedia con un digito
    # transpuesto (pero aun positiva) no rompe la monotonicidad -- ninguna de
    # las dos pruebas existentes detectaria un error de transcripcion en, por
    # ejemplo, 1990 o 2008. Estos tres valores se verificaron independientemente
    # contra el PDF (paginas 55-62), repartidos en distintas decadas de la serie.
    assert _IPC_VARIACION_ANUAL[1990] == Decimal("32.36")
    assert _IPC_VARIACION_ANUAL[2008] == Decimal("7.67")
    assert _IPC_VARIACION_ANUAL[2015] == Decimal("6.77")


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


def test_ibc_usura_primer_tramo_1997():
    ibc, usura = get_ibc_usura_for_date(date(1997, 7, 1))
    assert ibc == Decimal("36.50")
    assert usura == Decimal("54.75")


def test_ibc_usura_ultimo_tramo_2026():
    ibc, usura = get_ibc_usura_for_date(date(2026, 7, 31))
    assert ibc == Decimal("19.19")
    assert usura == Decimal("28.79")


def test_ibc_usura_limite_tramo_ordinario_fin_de_2016():
    # Frontera comun entre dos tramos con tasas distintas, sin ninguna
    # anomalia de fuente involucrada -- complementa el test del solape de
    # septiembre 2017 (que si es un caso especial) con el caso base.
    ibc_2016, _ = get_ibc_usura_for_date(date(2016, 12, 31))
    assert ibc_2016 == Decimal("21.99")

    ibc_2017, _ = get_ibc_usura_for_date(date(2017, 1, 1))
    assert ibc_2017 == Decimal("22.34")


def test_ibc_usura_limite_solape_septiembre_2017():
    # La SFC transiciono de certificacion trimestral a mensual en sep-2017; la
    # fuente trae un tramo trimestral (jul-sep, 21.98%) y uno mensual nuevo
    # (solo sep, 21.48%) que se solapan en la tabla original. Se resolvio
    # truncando el tramo trimestral al 31-ago y dejando el mensual como
    # autoritativo para septiembre (ver spec, seccion "Hallazgo relevante").
    ibc_agosto, _ = get_ibc_usura_for_date(date(2017, 8, 31))
    assert ibc_agosto == Decimal("21.98")

    ibc_septiembre, _ = get_ibc_usura_for_date(date(2017, 9, 1))
    assert ibc_septiembre == Decimal("21.48")


def test_ibc_usura_fuera_de_rango_lanza_value_error():
    with pytest.raises(ValueError):
        get_ibc_usura_for_date(date(1997, 6, 30))
    with pytest.raises(ValueError):
        get_ibc_usura_for_date(date(2026, 8, 1))


def test_tramos_ibc_usura_sin_vacios_ni_solapes():
    tramos = sorted(_TRAMOS_IBC_USURA, key=lambda t: t.inicio)
    for anterior, actual in zip(tramos, tramos[1:]):
        assert actual.inicio == anterior.fin + timedelta(days=1), (
            f"Vacio o solape entre {anterior} y {actual}"
        )


def test_usura_es_1_5_veces_ibc_en_todos_los_tramos():
    for tramo in _TRAMOS_IBC_USURA:
        esperado = tramo.ibc_anual * Decimal("1.5")
        assert abs(tramo.usura_anual - esperado) <= Decimal("0.01"), (
            f"{tramo}: usura {tramo.usura_anual} no es ~1.5x ibc {tramo.ibc_anual} "
            f"(esperado {esperado})"
        )
