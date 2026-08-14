from datetime import date
from decimal import Decimal

import pytest

from app.engine.tax.actualizacion_867_1 import (
    aplica_actualizacion_867_1,
    calcular_indexacion_867_1,
    calcular_indexacion_867_1_topada,
    calcular_interes_usura_plena,
)
from app.engine.tax.moratory_interest import calcular_interes_moratorio_tributario


@pytest.fixture(autouse=True)
def _parametros_legales_reales_en_memoria():
    # Usa la siembra real (scripts/migrate_parametros_legales.migrar()) en vez
    # de una fixture con datos de prueba: el caso de ejemplo del despacho
    # (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 15) cae dentro del rango historico
    # real de IPC/IBC-usura (1997-2026 / 1967-2025), asi que se verifica
    # contra los datos reales del sistema, no contra datos inventados. El
    # engine en memoria y los parches de database_module.engine /
    # session_module.SessionLocal ya los deja listos el conftest.py raiz
    # (Sprint 28) antes de que esta fixture arranque.
    from scripts.migrate_parametros_legales import migrar

    migrar()


def test_aplica_867_1_mora_mayor_a_3_anios():
    assert aplica_actualizacion_867_1(date(2018, 5, 10), date(2023, 5, 10)) is True


def test_no_aplica_867_1_mora_exactamente_3_anios():
    # 3 anios exactos (1095 dias): el umbral es estrictamente "mas de 3 anios".
    assert aplica_actualizacion_867_1(date(2020, 5, 10), date(2023, 5, 10)) is False


def test_no_aplica_867_1_mora_menor_a_3_anios():
    assert aplica_actualizacion_867_1(date(2022, 1, 1), date(2023, 1, 1)) is False


def test_caso_de_ejemplo_del_despacho_indexacion_topada_al_limite_de_usura():
    # Caso real del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 15): impuesto de
    # $100.000.000 vencido el 2018-05-10, pagado el 2023-05-10 (5 anios de mora).
    capital = Decimal("100000000.00")
    fecha_origen = date(2018, 5, 10)
    fecha_corte = date(2023, 5, 10)

    interes_et635 = calcular_interes_moratorio_tributario(capital, fecha_origen, fecha_corte)
    usura_plena = calcular_interes_usura_plena(capital, fecha_origen, fecha_corte)
    indexacion_sin_topar = calcular_indexacion_867_1(capital, fecha_origen, fecha_corte)

    # El interes E.T. 635 (usura - 2 puntos) siempre es menor que la usura
    # plena (el techo), y la indexacion sin topar es grande porque son 5 anios
    # de inflacion acumulada -- juntos superan el techo, asi que debe recortarse.
    assert interes_et635 < usura_plena
    assert interes_et635 + indexacion_sin_topar > usura_plena

    indexacion_topada = calcular_indexacion_867_1_topada(
        capital, fecha_origen, fecha_corte, interes_et635
    )

    assert indexacion_topada < indexacion_sin_topar
    assert interes_et635 + indexacion_topada == usura_plena


def test_indexacion_topada_no_es_negativa_si_el_interes_ya_supera_el_techo():
    # Caso artificial: si el interes "ya liquidado" que se pasa como referencia
    # ya excede el techo de usura plena por si solo, la indexacion topada debe
    # ser 0, nunca un numero negativo.
    capital = Decimal("100000000.00")
    fecha_origen = date(2018, 5, 10)
    fecha_corte = date(2023, 5, 10)
    usura_plena = calcular_interes_usura_plena(capital, fecha_origen, fecha_corte)

    topada = calcular_indexacion_867_1_topada(
        capital, fecha_origen, fecha_corte, interes_ya_liquidado=usura_plena * 2
    )

    assert topada == Decimal("0.00")


def test_indexacion_topada_no_recorta_si_el_interes_ya_liquidado_es_cero():
    # Aislando la logica de tope (sin mezclar el interes E.T. 635 real, que en
    # la practica siempre esta muy cerca del techo -- ver el caso del despacho
    # arriba): con interes_ya_liquidado=0, la indexacion topada es la
    # indexacion completa, mientras ella sola no supere el techo.
    capital = Decimal("1000.00")
    fecha_origen = date(2018, 5, 10)
    fecha_corte = date(2021, 6, 1)  # justo pasado el umbral de 3 anios
    indexacion_sin_topar = calcular_indexacion_867_1(capital, fecha_origen, fecha_corte)
    usura_plena = calcular_interes_usura_plena(capital, fecha_origen, fecha_corte)
    assert indexacion_sin_topar < usura_plena

    topada = calcular_indexacion_867_1_topada(
        capital, fecha_origen, fecha_corte, interes_ya_liquidado=Decimal("0.00")
    )

    assert topada == indexacion_sin_topar
