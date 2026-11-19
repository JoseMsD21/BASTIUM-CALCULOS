"""Sprint 85 -- retroactivo pensional mesada por mesada + mora Art. 141 Ley 100.

Valores esperados calculados a mano (ver comentarios de cada test). Las tasas
diarias de usura son la conversion efectiva compuesta del motor
(EffectiveRateConverter.annual_to_daily, cuantizada a 12 decimales por
Rate.decimal()):
  - usura 28,17 % EA (mayo 2026)  -> 0.000680196494 diario
  - usura 28,79 % EA (jun/jul 2026) -> 0.000693426569 diario
La tabla de usura cargada termina el 2026-07-31 (ultimo tramo certificado).
"""

from datetime import date
from decimal import Decimal

import pytest

from app.engine.indexation.historical_index import mensaje_pendiente_certificacion_usura
from app.engine.labor.retroactivo_pensional import (
    RUBRO_MORA_ART_141,
    CriterioMoraPensional,
    ModoReajusteMesada,
    TipoMesada,
    calcular_retroactivo_pensional,
    generar_mesadas,
    indexacion_mesada_ipc,
    interes_mora_pensional,
)
from scripts.migrate_parametros_legales import migrar


@pytest.fixture(autouse=True)
def _parametros_legales_sembrados():
    # SMLMV, IPC e IBC/usura en la base en memoria del conftest.
    migrar()


# ---------------------------------------------------------------------------
# Serie de mesadas
# ---------------------------------------------------------------------------


def test_mesadas_salario_minimo_tres_anios_con_mesada_adicional_de_noviembre():
    # Causacion 01/11/2023, corte 31/01/2025, 13 mesadas (adicional en noviembre).
    # 2023: nov + adicional nov + dic = 3 x 1.160.000 = 3.480.000
    # 2024: 12 + adicional nov = 13 x 1.300.000 = 16.900.000
    # 2025: enero = 1 x 1.423.500
    # Total = 21.803.500
    mesadas = generar_mesadas(
        fecha_causacion=date(2023, 11, 1),
        fecha_corte=date(2025, 1, 31),
        mesadas_por_anio=13,
        modo_reajuste=ModoReajusteMesada.SALARIO_MINIMO,
    )

    assert len(mesadas) == 17
    assert sum(m.valor for m in mesadas) == Decimal("21803500.00")

    primera = mesadas[0]
    assert primera.periodo == date(2023, 11, 1)
    assert primera.tipo == TipoMesada.ORDINARIA
    assert primera.fecha_exigibilidad == date(2023, 11, 30)
    assert primera.valor == Decimal("1160000.00")

    adicional_2023 = mesadas[1]
    assert adicional_2023.tipo == TipoMesada.ADICIONAL
    assert adicional_2023.fecha_exigibilidad == date(2023, 11, 30)

    valores_2024 = {m.valor for m in mesadas if m.periodo.year == 2024}
    assert valores_2024 == {Decimal("1300000.00")}
    assert mesadas[-1].periodo == date(2025, 1, 1)
    assert mesadas[-1].valor == Decimal("1423500.00")


def test_mesadas_por_porcentaje_con_prorrata_del_primer_mes_y_14_mesadas():
    # Mesada inicial 2.000.000, causacion 16/11/2024, corte 31/01/2026,
    # 14 mesadas (adicionales en junio y noviembre), reajuste 2025 = 5,20 %,
    # 2026 = 5,10 % (porcentajes de entrada, no inventados por el motor).
    # nov-2024 ordinaria: 15 dias de 30 (16 al 30) = 1.000.000
    # nov-2024 adicional: 2.000.000 ; dic-2024: 2.000.000
    # 2025: 2.000.000 x 1,052 = 2.104.000 x 14 = 29.456.000
    # 2026: 2.104.000 x 1,051 = 2.211.304 (solo enero)
    # Total = 36.667.304
    mesadas = generar_mesadas(
        fecha_causacion=date(2024, 11, 16),
        fecha_corte=date(2026, 1, 31),
        mesadas_por_anio=14,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("2000000.00"),
        reajustes_pct_por_anio={2025: Decimal("5.20"), 2026: Decimal("5.10")},
    )

    assert mesadas[0].valor == Decimal("1000000.00")
    assert mesadas[0].dias_causados == 15
    assert mesadas[1].tipo == TipoMesada.ADICIONAL
    assert mesadas[1].valor == Decimal("2000000.00")
    adicionales_2025 = [
        m for m in mesadas if m.periodo.year == 2025 and m.tipo == TipoMesada.ADICIONAL
    ]
    assert [m.periodo.month for m in adicionales_2025] == [6, 11]
    assert mesadas[-1].valor == Decimal("2211304.00")
    assert len(mesadas) == 3 + 14 + 1
    assert sum(m.valor for m in mesadas) == Decimal("36667304.00")


def test_mesada_cuyo_mes_no_ha_terminado_al_corte_no_es_exigible():
    # Corte 15/02/2025: la mesada de febrero se hace exigible el 28/02 -> no entra.
    mesadas = generar_mesadas(
        fecha_causacion=date(2025, 1, 1),
        fecha_corte=date(2025, 2, 15),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.SALARIO_MINIMO,
    )
    assert [m.periodo for m in mesadas] == [date(2025, 1, 1)]


def test_porcentaje_sin_reajuste_de_un_anio_lanza_error():
    with pytest.raises(ValueError, match="2026"):
        generar_mesadas(
            fecha_causacion=date(2025, 1, 1),
            fecha_corte=date(2026, 3, 31),
            mesadas_por_anio=12,
            modo_reajuste=ModoReajusteMesada.PORCENTAJE,
            mesada_inicial=Decimal("2000000.00"),
            reajustes_pct_por_anio={},
        )


def test_corte_a_mitad_de_enero_no_exige_reajuste_del_anio_sin_mesadas_exigibles():
    # Corte 15/01/2026: la ultima mesada exigible es la de dic-2025, asi que el
    # reajuste de 2026 no hace falta.
    mesadas = generar_mesadas(
        fecha_causacion=date(2025, 11, 1),
        fecha_corte=date(2026, 1, 15),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("2000000.00"),
        reajustes_pct_por_anio={},
    )
    assert [m.periodo for m in mesadas] == [date(2025, 11, 1), date(2025, 12, 1)]


@pytest.mark.parametrize("mesadas_por_anio", [11, 15])
def test_numero_de_mesadas_invalido_lanza_error(mesadas_por_anio):
    with pytest.raises(ValueError):
        generar_mesadas(
            fecha_causacion=date(2025, 1, 1),
            fecha_corte=date(2025, 3, 31),
            mesadas_por_anio=mesadas_por_anio,
            modo_reajuste=ModoReajusteMesada.SALARIO_MINIMO,
        )


def test_corte_anterior_a_causacion_lanza_error():
    with pytest.raises(ValueError):
        generar_mesadas(
            fecha_causacion=date(2025, 5, 1),
            fecha_corte=date(2025, 3, 31),
            mesadas_por_anio=12,
            modo_reajuste=ModoReajusteMesada.SALARIO_MINIMO,
        )


# ---------------------------------------------------------------------------
# Interes moratorio Art. 141 Ley 100 (tasa de usura certificada)
# ---------------------------------------------------------------------------


def test_mora_art_141_un_tramo_de_usura():
    # 1.000.000 x 0.000693426569 x 31 dias (1-31 jul 2026) = 21.496,223639
    resultado = interes_mora_pensional(
        Decimal("1000000.00"), date(2026, 6, 30), date(2026, 7, 31)
    )
    assert resultado.interes == Decimal("21496.22")
    assert resultado.dias_mora == 31
    assert resultado.dias_pendientes_certificacion == 0


def test_mora_art_141_cruza_dos_tramos_de_usura():
    # mayo: 1.000.000 x 0.000680196494 x 31 = 21.086,091314
    # junio: 1.000.000 x 0.000693426569 x 30 = 20.802,797070
    # total = 41.888,888384 -> 41.888,89
    resultado = interes_mora_pensional(
        Decimal("1000000.00"), date(2026, 4, 30), date(2026, 6, 30)
    )
    assert resultado.interes == Decimal("41888.89")
    assert resultado.dias_mora == 61


def test_mora_art_141_posterior_al_ultimo_tramo_certificado_se_suspende():
    # Sprint 110: corte 25/08/2026, tabla certificada hasta 31/07/2026. Solo
    # causa julio (21.496,22); los 25 dias de agosto quedan pendientes.
    resultado = interes_mora_pensional(
        Decimal("1000000.00"), date(2026, 6, 30), date(2026, 8, 25)
    )
    assert resultado.interes == Decimal("21496.22")
    assert resultado.dias_mora == 56
    assert resultado.dias_pendientes_certificacion == 25
    assert resultado.ultima_fecha_usura_certificada == date(2026, 7, 31)


def test_mora_art_141_exigible_en_el_ultimo_dia_certificado_no_causa_interes():
    resultado = interes_mora_pensional(
        Decimal("1000000.00"), date(2026, 7, 31), date(2026, 8, 25)
    )
    assert resultado.interes == Decimal("0.00")
    assert resultado.dias_pendientes_certificacion == 25


def test_mora_sin_dias_de_mora_es_cero():
    resultado = interes_mora_pensional(
        Decimal("1000000.00"), date(2026, 6, 30), date(2026, 6, 30)
    )
    assert resultado.interes == Decimal("0.00")
    assert resultado.dias_mora == 0


# ---------------------------------------------------------------------------
# Excepcion de buena fe / cambio jurisprudencial: solo indexacion IPC
# ---------------------------------------------------------------------------


def test_indexacion_ipc_de_una_mesada():
    # IPC dic-2025 = 152,27 (ultimo dia del mes -> indice directo);
    # IPC mar-2026 = 156,94. 1.000.000 x (156,94/152,27 - 1) = 30.669,206 -> 30.669,21
    assert indexacion_mesada_ipc(
        Decimal("1000000.00"), date(2025, 12, 31), date(2026, 3, 31)
    ) == Decimal("30669.21")


# ---------------------------------------------------------------------------
# Liquidacion completa
# ---------------------------------------------------------------------------


def test_retroactivo_con_mora_art_141_suma_mesadas_e_intereses():
    # Mesada 1.000.000 constante (reajuste 0 % en 2026 como dato de entrada),
    # causacion 01/05/2026, corte 31/07/2026, 12 mesadas:
    #   mayo (exig 31/05): jun 30 d x 0.000693426569 + jul 31 d x 0.000693426569
    #       = 1.000.000 x 0.000693426569 x 61 = 42.299,020709 -> 42.299,02
    #   junio (exig 30/06): 31 d -> 21.496,22
    #   julio (exig 31/07): 0 dias de mora -> 0
    # Intereses = 63.795,24 ; mesadas = 3.000.000 ; total = 3.063.795,24
    resultado = calcular_retroactivo_pensional(
        fecha_causacion=date(2026, 5, 1),
        fecha_corte=date(2026, 7, 31),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("1000000.00"),
        reajustes_pct_por_anio={},
    )

    assert resultado.criterio == CriterioMoraPensional.INTERES_MORATORIO_ART_141
    assert [m.interes_moratorio for m in resultado.mesadas] == [
        Decimal("42299.02"), Decimal("21496.22"), Decimal("0.00")
    ]
    assert all(m.indexacion == Decimal("0.00") for m in resultado.mesadas)
    assert resultado.total_mesadas == Decimal("3000000.00")
    assert resultado.total_intereses_moratorios == Decimal("63795.24")
    assert resultado.total_indexacion == Decimal("0.00")
    assert resultado.total == Decimal("3063795.24")
    assert resultado.alertas == ()
    assert resultado.ultima_fecha_usura_certificada is None


def test_retroactivo_con_mora_pendiente_de_certificacion_emite_alerta():
    resultado = calcular_retroactivo_pensional(
        fecha_causacion=date(2026, 6, 1),
        fecha_corte=date(2026, 8, 25),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("1000000.00"),
        reajustes_pct_por_anio={},
    )

    # junio (exig 30/06): 21.496,22 ; julio (exig 31/07): 0 ; agosto no exigible.
    assert len(resultado.mesadas) == 2
    assert resultado.total_intereses_moratorios == Decimal("21496.22")
    assert resultado.ultima_fecha_usura_certificada == date(2026, 7, 31)
    assert resultado.alertas == (
        mensaje_pendiente_certificacion_usura(RUBRO_MORA_ART_141, date(2026, 7, 31)),
    )


def test_retroactivo_con_buena_fe_solo_indexa_y_no_liquida_usura():
    # Causacion 01/12/2025, corte 31/03/2026, mesada 1.000.000, 12 mesadas,
    # reajuste 2026 = 0 % (dato de entrada). IPC al corte (mar-2026) = 156,94.
    #   dic-2025 (exig 31/12, IPC 152,27): 1.000.000 x (156,94/152,27 - 1) = 30.669,21
    #   ene-2026 (exig 31/01, IPC 154,07): 1.000.000 x (156,94/154,07 - 1) = 18.627,90
    #   feb-2026 (exig 28/02, IPC 155,73): 1.000.000 x (156,94/155,73 - 1) =  7.769,86
    #   mar-2026 (exig 31/03, IPC 156,94): 0
    # Indexacion total = 57.066,97 ; total = 4.057.066,97
    resultado = calcular_retroactivo_pensional(
        fecha_causacion=date(2025, 12, 1),
        fecha_corte=date(2026, 3, 31),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("1000000.00"),
        reajustes_pct_por_anio={2026: Decimal("0")},
        buena_fe_o_cambio_jurisprudencial=True,
    )

    assert resultado.criterio == CriterioMoraPensional.INDEXACION_IPC_BUENA_FE
    assert [m.indexacion for m in resultado.mesadas] == [
        Decimal("30669.21"), Decimal("18627.90"), Decimal("7769.86"), Decimal("0.00")
    ]
    assert resultado.total_intereses_moratorios == Decimal("0.00")
    assert resultado.total_indexacion == Decimal("57066.97")
    assert resultado.total == Decimal("4057066.97")


def test_buena_fe_no_emite_alerta_de_usura_aunque_el_corte_pase_la_certificacion():
    resultado = calcular_retroactivo_pensional(
        fecha_causacion=date(2026, 6, 1),
        fecha_corte=date(2026, 8, 25),
        mesadas_por_anio=12,
        modo_reajuste=ModoReajusteMesada.PORCENTAJE,
        mesada_inicial=Decimal("1000000.00"),
        reajustes_pct_por_anio={},
        buena_fe_o_cambio_jurisprudencial=True,
    )
    assert resultado.alertas == ()
    assert resultado.total_intereses_moratorios == Decimal("0.00")
