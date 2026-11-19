from datetime import date
from decimal import Decimal

import pytest

from app.engine.labor.horas_extra import (
    PORCENTAJE_RECARGO_NOCTURNO,
    ConceptoHoraExtra,
    HoraExtraFestivaSinFactorConfirmadoError,
    LimiteHorasExtraLey2466Error,
    calcular_hora_extra,
    calcular_recargo,
    factor_hora_extra,
    hora_inicio_jornada_nocturna,
    liquidar_hora_extra,
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


class TestFactorHoraExtra:
    """Sprint 95 (seguimiento, respuesta del despacho): HED 1.25 y HEN 1.75
    constantes; HEFD/HEFN incorporan la tabla progresiva del recargo
    dominical/festivo de la Ley 2466/2025 por tramos desde el 01/07/2025."""

    @pytest.mark.parametrize(
        "fecha", [date(2024, 1, 15), date(2025, 7, 1), date(2026, 7, 1), date(2030, 1, 1)]
    )
    def test_hed_es_1_25_en_cualquier_fecha(self, fecha):
        assert factor_hora_extra(ConceptoHoraExtra.HED, fecha) == Decimal("1.25")

    @pytest.mark.parametrize(
        "fecha", [date(2024, 1, 15), date(2025, 7, 1), date(2026, 7, 1), date(2030, 1, 1)]
    )
    def test_hen_es_1_75_en_cualquier_fecha(self, fecha):
        assert factor_hora_extra(ConceptoHoraExtra.HEN, fecha) == Decimal("1.75")

    @pytest.mark.parametrize(
        "fecha, hefd, hefn",
        [
            # Tramo 1: jul 2025 - jun 2026 (recargo festivo 80%)
            (date(2025, 7, 1), "2.05", "2.55"),
            (date(2026, 6, 30), "2.05", "2.55"),
            # Tramo 2: jul 2026 - jun 2027 (recargo festivo 90%)
            (date(2026, 7, 1), "2.15", "2.65"),
            (date(2027, 6, 30), "2.15", "2.65"),
            # Tramo 3: jul 2027 en adelante (recargo festivo 100%)
            (date(2027, 7, 1), "2.25", "2.75"),
            (date(2035, 12, 31), "2.25", "2.75"),
        ],
    )
    def test_hefd_y_hefn_por_tramo(self, fecha, hefd, hefn):
        assert factor_hora_extra(ConceptoHoraExtra.HEFD, fecha) == Decimal(hefd)
        assert factor_hora_extra(ConceptoHoraExtra.HEFN, fecha) == Decimal(hefn)

    @pytest.mark.parametrize("fecha", [date(2025, 7, 1), date(2026, 7, 1), date(2027, 7, 1)])
    def test_hef_es_coherente_con_el_recargo_festivo_del_tramo(self, fecha):
        # La respuesta del despacho: HEFD = 25% + recargo festivo; HEFN = 75% + recargo festivo.
        festivo = porcentaje_recargo_dominical_festivo(fecha) / Decimal("100")
        assert factor_hora_extra(ConceptoHoraExtra.HEFD, fecha) == Decimal("1.25") + festivo
        assert factor_hora_extra(ConceptoHoraExtra.HEFN, fecha) == Decimal("1.75") + festivo

    @pytest.mark.parametrize("concepto", [ConceptoHoraExtra.HEFD, ConceptoHoraExtra.HEFN])
    def test_hef_antes_de_2025_07_01_no_tiene_factor_confirmado(self, concepto):
        # La respuesta solo fija HEFD/HEFN desde el Tramo 1 (jul 2025): antes
        # de esa fecha el codigo conserva el comportamiento previo (el
        # llamador pasa el porcentaje a `calcular_hora_extra`).
        with pytest.raises(HoraExtraFestivaSinFactorConfirmadoError):
            factor_hora_extra(concepto, date(2025, 6, 30))

    def test_acepta_el_codigo_del_concepto_como_texto(self):
        assert factor_hora_extra("HEFN", date(2026, 7, 1)) == Decimal("2.65")

    def test_concepto_desconocido_lanza_error(self):
        with pytest.raises(ValueError):
            factor_hora_extra("XYZ", date(2026, 7, 1))


class TestLiquidarHoraExtra:
    """Valor = valor hora x horas x factor del concepto vigente en la fecha de
    causacion. Valor hora de ejemplo: $6.250 (salario $1.500.000 / 240 h)."""

    def test_hed_valor_a_mano(self):
        # 6.250 x 4 x 1,25 = 31.250
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HED, Decimal("4"), Decimal("6250"), date(2026, 3, 10)
        ) == Decimal("31250.00")

    def test_hen_valor_a_mano(self):
        # 6.250 x 4 x 1,75 = 43.750
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEN, Decimal("4"), Decimal("6250"), date(2026, 3, 10)
        ) == Decimal("43750.00")

    def test_tramo_1_valores_a_mano(self):
        # HEFD: 6.250 x 2 x 2,05 = 25.625 ; HEFN: 6.250 x 2 x 2,55 = 31.875
        fecha = date(2025, 12, 8)
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFD, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("25625.00")
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFN, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("31875.00")

    def test_tramo_2_valores_a_mano(self):
        # HEFD: 6.250 x 2 x 2,15 = 26.875 ; HEFN: 6.250 x 2 x 2,65 = 33.125
        fecha = date(2026, 12, 8)
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFD, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("26875.00")
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFN, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("33125.00")

    def test_tramo_3_valores_a_mano(self):
        # HEFD: 6.250 x 2 x 2,25 = 28.125 ; HEFN: 6.250 x 2 x 2,75 = 34.375
        fecha = date(2027, 12, 8)
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFD, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("28125.00")
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFN, Decimal("2"), Decimal("6250"), fecha
        ) == Decimal("34375.00")

    def test_redondea_a_centavos(self):
        # 4.583,33 x 3 x 2,05 = 28.187,4795 -> 28.187,48
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFD, Decimal("3"), Decimal("4583.33"), date(2026, 1, 1)
        ) == Decimal("28187.48")

    def test_coincide_con_calcular_hora_extra_y_el_porcentaje_del_despacho(self):
        # HEFN tramo 2 = 165% -> calcular_hora_extra(horas, valor, 165)
        assert liquidar_hora_extra(
            ConceptoHoraExtra.HEFN, Decimal("3"), Decimal("7000"), date(2026, 8, 1)
        ) == calcular_hora_extra(Decimal("3"), Decimal("7000"), Decimal("165"))

    def test_horas_no_positivas_lanza_error(self):
        with pytest.raises(ValueError):
            liquidar_hora_extra(
                ConceptoHoraExtra.HED, Decimal("0"), Decimal("6250"), date(2026, 1, 1)
            )

    def test_valor_hora_negativo_lanza_error(self):
        with pytest.raises(ValueError):
            liquidar_hora_extra(
                ConceptoHoraExtra.HED, Decimal("1"), Decimal("-1"), date(2026, 1, 1)
            )

    def test_hef_antes_de_2025_07_01_lanza_error(self):
        with pytest.raises(HoraExtraFestivaSinFactorConfirmadoError):
            liquidar_hora_extra(
                ConceptoHoraExtra.HEFD, Decimal("1"), Decimal("6250"), date(2025, 1, 1)
            )
