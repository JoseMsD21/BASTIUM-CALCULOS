from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.horas_extra import (
    PORCENTAJE_RECARGO_NOCTURNO,
    LimiteHorasExtraLey2466Error,
    calcular_hora_extra,
    calcular_recargo,
    hora_inicio_jornada_nocturna,
    porcentaje_recargo_dominical_festivo,
    validar_limite_horas_extra_ley_2466,
)


def test_hora_extra_aplica_valor_hora_mas_porcentaje():
    # HED tipico: $10.000/hora x 5 horas x (1 + 25%) = 62.500
    resultado = calcular_hora_extra(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("25"),
    )
    assert resultado == Decimal("62500.00")


def test_hora_extra_con_porcentaje_cero_equivale_al_valor_hora_simple():
    resultado = calcular_hora_extra(
        numero_horas=Decimal("3"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("0"),
    )
    assert resultado == Decimal("30000.00")


def test_hora_extra_acepta_enteros_ademas_de_decimal():
    resultado = calcular_hora_extra(
        numero_horas=2,
        valor_hora_ordinaria=10000,
        porcentaje=75,
    )
    # 2 x 10.000 x 1,75 = 35.000
    assert resultado == Decimal("35000.00")


@pytest.mark.parametrize("horas", [Decimal("0"), Decimal("-1")])
def test_hora_extra_horas_no_positivas_lanza_error(horas):
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=horas,
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("25"),
        )


def test_hora_extra_valor_hora_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("-1"),
            porcentaje=Decimal("25"),
        )


def test_hora_extra_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_hora_extra(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("-1"),
        )


def test_recargo_aplica_solo_el_porcentaje_sin_sumar_el_valor_hora_base():
    # Recargo nocturno tipico: $10.000/hora x 5 horas x 35% = 17.500
    # (no x 1,35, porque la hora ordinaria ya se pago por separado).
    resultado = calcular_recargo(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("35"),
    )
    assert resultado == Decimal("17500.00")


def test_recargo_con_porcentaje_cero_da_cero():
    resultado = calcular_recargo(
        numero_horas=Decimal("5"),
        valor_hora_ordinaria=Decimal("10000"),
        porcentaje=Decimal("0"),
    )
    assert resultado == Decimal("0.00")


def test_recargo_acepta_enteros_ademas_de_decimal():
    resultado = calcular_recargo(
        numero_horas=4,
        valor_hora_ordinaria=10000,
        porcentaje=75,
    )
    # 4 x 10.000 x 0,75 = 30.000
    assert resultado == Decimal("30000.00")


@pytest.mark.parametrize("horas", [Decimal("0"), Decimal("-1")])
def test_recargo_horas_no_positivas_lanza_error(horas):
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=horas,
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("35"),
        )


def test_recargo_valor_hora_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("-1"),
            porcentaje=Decimal("35"),
        )


def test_recargo_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_recargo(
            numero_horas=Decimal("1"),
            valor_hora_ordinaria=Decimal("10000"),
            porcentaje=Decimal("-1"),
        )


class TestHoraInicioJornadaNocturna:
    """Sprint 95 (respuesta del despacho, 22/08/2026): la Ley 2466/2025
    adelanta el inicio de la jornada nocturna de las 21:00 a las 19:00 desde
    el 25/12/2025 -- vigencia inmediata (una sola fecha de corte, sin
    transicion progresiva como el recargo dominical/festivo)."""

    def test_antes_del_corte_la_jornada_nocturna_inicia_a_las_21(self):
        assert hora_inicio_jornada_nocturna(date(2025, 12, 24)) == 21

    def test_en_la_fecha_de_corte_la_jornada_nocturna_inicia_a_las_19(self):
        assert hora_inicio_jornada_nocturna(date(2025, 12, 25)) == 19

    def test_despues_del_corte_la_jornada_nocturna_inicia_a_las_19(self):
        assert hora_inicio_jornada_nocturna(date(2026, 6, 1)) == 19


def test_porcentaje_recargo_nocturno_es_constante_no_afectado_por_la_reforma():
    # Confirmado explicitamente por el despacho ("el horario nocturno
    # (recargo 35%)") -- solo cambia el horario de inicio, no el porcentaje.
    assert PORCENTAJE_RECARGO_NOCTURNO == Decimal("35")


class TestPorcentajeRecargoDominicalFestivo:
    """Sprint 95 (respuesta del despacho, 22/08/2026): tabla de transicion
    progresiva 2025-2027 del recargo dominical/festivo."""

    def test_antes_de_2025_07_01_es_75_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2025, 6, 30)) == Decimal("75")

    def test_en_2025_07_01_es_80_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2025, 7, 1)) == Decimal("80")

    def test_justo_antes_de_2026_07_01_es_80_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2026, 6, 30)) == Decimal("80")

    def test_en_2026_07_01_es_90_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2026, 7, 1)) == Decimal("90")

    def test_justo_antes_de_2027_07_01_es_90_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2027, 6, 30)) == Decimal("90")

    def test_en_2027_07_01_es_100_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2027, 7, 1)) == Decimal("100")

    def test_mucho_despues_de_2027_07_01_sigue_en_100_por_ciento(self):
        assert porcentaje_recargo_dominical_festivo(date(2030, 1, 1)) == Decimal("100")


class TestValidarLimiteHorasExtraLey2466:
    """Sprint 95 (respuesta del despacho, 22/08/2026): topes nuevos de la Ley
    2466/2025 -- maximo 2 horas extra diarias y 12 semanales."""

    def test_dentro_del_limite_no_lanza_error(self):
        validar_limite_horas_extra_ley_2466(
            horas_extra_diarias=Decimal("2"), horas_extra_semanales=Decimal("12")
        )

    def test_supera_el_limite_diario_lanza_error(self):
        with pytest.raises(LimiteHorasExtraLey2466Error):
            validar_limite_horas_extra_ley_2466(
                horas_extra_diarias=Decimal("2.01"), horas_extra_semanales=Decimal("10")
            )

    def test_supera_el_limite_semanal_lanza_error(self):
        with pytest.raises(LimiteHorasExtraLey2466Error):
            validar_limite_horas_extra_ley_2466(
                horas_extra_diarias=Decimal("1"), horas_extra_semanales=Decimal("12.01")
            )
