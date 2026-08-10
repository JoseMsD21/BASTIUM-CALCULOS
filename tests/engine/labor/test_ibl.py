from datetime import date, timedelta
from datetime import datetime as _dt
from decimal import Decimal

import pytest

import database.session as session_module
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _ipc_en_memoria():
    # calcular_ibl usa get_ipc_interpolado_for_date, que lee IPC_INDICE_ACUMULADO
    # via parametro_service en cada llamada -- misma fixture aislada de disco
    # que tests/engine/labor/test_seguridad_social.py.
    session = session_module.get_session()
    indices = {
        2017: Decimal("100"),
        2018: Decimal("105"),
        2019: Decimal("110"),
        2020: Decimal("115"),
        2021: Decimal("120"),
        2022: Decimal("125"),
        2023: Decimal("130"),
        2024: Decimal("135"),
        2025: Decimal("140"),
        2026: Decimal("145"),
    }
    for anio, valor in indices.items():
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=valor,
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=_dt.now(),
            )
        )
    session.commit()
    session.close()


def test_calcular_ibl_historial_10_anios_con_ipc_variable():
    from app.engine.labor.ibl import calcular_ibl

    historial = [(date(anio, 12, 31), Decimal("1000000.00")) for anio in range(2017, 2027)]

    resultado = calcular_ibl(historial, fecha_calculo=date(2026, 12, 31))

    assert resultado == Decimal("1200351.01")


def test_calcular_ibl_historial_vacio_lanza_error():
    from app.engine.labor.ibl import calcular_ibl

    with pytest.raises(ValueError):
        calcular_ibl([], fecha_calculo=date(2026, 12, 31))


def test_tasa_reemplazo_s_uno_sin_bono_da_65_5_menos_medio_por_ciento():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1300,
        anio_causacion=2020,
    )

    assert resultado == Decimal(
        "65.00"
    )  # s=1 -> r = 65.5 - 0.5*1 = 65.0 (dentro del rango, sin recorte)


def test_tasa_reemplazo_s_uno_con_bono_de_dos_bloques():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1400,
        anio_causacion=2020,
    )

    assert resultado == Decimal("68.00")


def test_tasa_reemplazo_s_alto_baja_del_65_pero_no_del_piso_55():
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 17): el piso legal de la
    # tasa inicial es 55%, NO 65% -- 65.5% es el TECHO (para quien gana 1 SMMLV). Antes de
    # esta correccion, s=10 (alguien que gana 10 SMMLV) quedaba mal floreado a 65% en vez
    # de dejarse en su valor real de la formula, 60.5%.
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("10000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1300,
        anio_causacion=2020,
    )

    assert resultado == Decimal("60.50")  # s=10 -> r = 65.5 - 0.5*10 = 60.5


def test_tasa_reemplazo_s_muy_alto_si_toca_el_piso_legal_de_55():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("25000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1300,
        anio_causacion=2020,
    )

    assert resultado == Decimal("55.00")  # s=25 -> raw r = 65.5 - 12.5 = 53.0 -> se topa a 55


def test_tasa_reemplazo_bono_grande_no_sube_del_techo_80():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("2000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=3800,
        anio_causacion=2020,
    )

    assert resultado == Decimal("80.00")


def test_tasa_reemplazo_semanas_minimas_varian_por_anio_no_estan_fijas_en_1300():
    # Caso de prueba exacto del despacho (Sprint 17): IBL $800.000, SMMLV $400.000 (s=2),
    # 1.664 semanas cotizadas, causado en 2006 (minimo de ese año: 1.075 semanas, no 1.300).
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("800000.00"),
        smlmv_vigente=Decimal("400000.00"),
        semanas_cotizadas=1664,
        anio_causacion=2006,
    )

    # r_inicial = 65.5 - 0.5*2 = 64.5%. Exceso = 1664 - 1075 = 589. Bloques de 50 = 11.
    # Bono = 11 x 1.5 = 16.5%. Total = 81% -> techo 80% aplica.
    assert resultado == Decimal("80.00")


def test_tasa_reemplazo_semanas_minimas_2005_es_1050():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    # s=1 -> r_inicial = 65.5 - 0.5 = 65.0. Semanas = minimo exacto de 2005 (1050) -> sin bono.
    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1050,
        anio_causacion=2005,
    )

    assert resultado == Decimal("65.00")


def test_tasa_reemplazo_semanas_minimas_antes_de_2005_es_1000():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1050,
        anio_causacion=2000,
    )

    # Minimo de 2000 = 1000 (antes de la Ley 797/2003). Exceso = 50 -> 1 bloque de 50 -> +1.5%.
    assert resultado == Decimal("66.50")


def test_tasa_reemplazo_semanas_minimas_desde_2015_se_queda_fija_en_1300():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    resultado_2015 = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1350,
        anio_causacion=2015,
    )
    resultado_2026 = calcular_tasa_reemplazo(
        ibl=Decimal("1000000.00"),
        smlmv_vigente=Decimal("1000000.00"),
        semanas_cotizadas=1350,
        anio_causacion=2026,
    )

    # Ambos años exigen 1300 semanas minimas -> mismo bono (1 bloque de 50 -> +1.5%).
    assert resultado_2015 == resultado_2026 == Decimal("66.50")


def test_tasa_reemplazo_smlmv_cero_lanza_error():
    from app.engine.labor.ibl import calcular_tasa_reemplazo

    with pytest.raises(ValueError):
        calcular_tasa_reemplazo(
            ibl=Decimal("1000000.00"),
            smlmv_vigente=Decimal("0.00"),
            semanas_cotizadas=1300,
            anio_causacion=2020,
        )


def test_densidad_semanas_calendario_real_vs_ano_comercial_360():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodo = [(date(2024, 1, 1), date(2025, 2, 1))]  # 13 meses cruzando un ano bisiesto (2024)

    semanas_calendario_real = calcular_densidad_semanas(periodo)

    # Metodo pre-SL138-2024 (ano comercial de 360, mes de 30 dias): 13*30=390 dias.
    dias_ano_comercial_360 = 13 * 30
    semanas_ano_comercial_360 = round(dias_ano_comercial_360 / 7)

    assert (
        semanas_calendario_real == 57
    )  # (2025-02-01 - 2024-01-01).days == 397; 397/7 = 56.71 -> 57
    assert semanas_ano_comercial_360 == 56
    assert (
        semanas_calendario_real != semanas_ano_comercial_360
    )  # documenta la diferencia real de 1 semana


def test_densidad_semanas_caso_real_sentencia_sl138_2024():
    from app.engine.labor.ibl import calcular_densidad_semanas

    inicio = date(2020, 1, 1)
    fin = inicio + timedelta(days=348)  # caso citado en la Sentencia SL138-2024

    resultado = calcular_densidad_semanas([(inicio, fin)])

    assert resultado == 50  # 348/7 = 49.71 -> redondea a 50 (segun la sentencia)


def test_densidad_semanas_periodos_solapados_no_se_cuentan_doble():
    from app.engine.labor.ibl import calcular_densidad_semanas

    periodos = [
        (date(2023, 1, 1), date(2023, 1, 31)),
        (date(2023, 1, 15), date(2023, 2, 15)),  # se solapa 17 dias con el anterior
    ]

    resultado = calcular_densidad_semanas(periodos)

    assert resultado == 6  # union (2023-01-01, 2023-02-15) = 45 dias -> 45/7 = 6.43 -> 6, no 9


def test_densidad_semanas_lista_vacia_retorna_cero():
    from app.engine.labor.ibl import calcular_densidad_semanas

    assert calcular_densidad_semanas([]) == 0


def test_densidad_semanas_periodo_invalido_lanza_error():
    from app.engine.labor.ibl import calcular_densidad_semanas

    with pytest.raises(ValueError):
        calcular_densidad_semanas([(date(2023, 2, 1), date(2023, 1, 1))])
