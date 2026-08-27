from datetime import date
from decimal import Decimal

import pytest

from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.suma_unica_con_abonos import (
    liquidar_obligacion_con_abonos_tramo_por_tramo,
)
from app.engine.time.calendar import CalendarUtils

TASA_MENSUAL_6_EA = Decimal("0.0048676")


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria():
    from scripts.migrate_parametros_legales import migrar

    migrar()


def test_sin_abonos_indexa_y_causa_interes_en_un_unico_tramo():
    fecha_origen = date(2024, 7, 1)
    fecha_corte = date(2025, 12, 31)
    capital = Decimal("1000000.00")

    resultado = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=capital,
        fecha_origen=fecha_origen,
        abonos=[],
        fecha_liquidacion_final=fecha_corte,
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )

    ipc_origen = get_ipc_interpolado_for_date(fecha_origen)
    ipc_corte = get_ipc_interpolado_for_date(fecha_corte)
    capital_indexado_esperado = capital * (ipc_corte / ipc_origen)
    dias = Decimal(CalendarUtils.dias_comerciales_360(fecha_origen, fecha_corte))
    meses = dias / Decimal("30")
    intereses_esperados = capital_indexado_esperado * (
        (Decimal("1") + TASA_MENSUAL_6_EA) ** meses - Decimal("1")
    )

    assert resultado.capital_insoluto_indexado == capital_indexado_esperado.quantize(
        Decimal("0.01")
    )
    assert resultado.intereses_pendientes_cobro == intereses_esperados.quantize(Decimal("0.01"))
    assert resultado.gran_total_adeudado == (
        resultado.capital_insoluto_indexado + resultado.intereses_pendientes_cobro
    )


def test_un_abono_que_cubre_todos_los_intereses_reduce_el_capital():
    fecha_origen = date(2024, 7, 1)
    fecha_abono = date(2025, 1, 1)
    fecha_corte = date(2025, 12, 31)
    capital = Decimal("1000000.00")

    # El abono debe superar los intereses del primer tramo para reducir capital
    # -- se calcula el tramo aparte para elegir un monto de abono que
    # garantice la rama "cubre los intereses" sin adivinar la cifra.
    ipc_origen = get_ipc_interpolado_for_date(fecha_origen)
    ipc_abono = get_ipc_interpolado_for_date(fecha_abono)
    capital_indexado_tramo1 = capital * (ipc_abono / ipc_origen)
    dias_tramo1 = Decimal(CalendarUtils.dias_comerciales_360(fecha_origen, fecha_abono))
    meses_tramo1 = dias_tramo1 / Decimal("30")
    intereses_tramo1 = capital_indexado_tramo1 * (
        (Decimal("1") + TASA_MENSUAL_6_EA) ** meses_tramo1 - Decimal("1")
    )
    monto_abono = (intereses_tramo1 + Decimal("500000.00")).quantize(Decimal("0.01"))

    resultado = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=capital,
        fecha_origen=fecha_origen,
        abonos=[(fecha_abono, monto_abono)],
        fecha_liquidacion_final=fecha_corte,
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )

    capital_indexado_tramo1_redondeado = capital_indexado_tramo1.quantize(Decimal("0.01"))
    remanente_para_capital = monto_abono - intereses_tramo1.quantize(Decimal("0.01"))
    capital_base_esperado = capital_indexado_tramo1_redondeado - remanente_para_capital
    assert capital_base_esperado < capital_indexado_tramo1_redondeado

    # El capital final indexado debe ser menor que si nunca se hubiera
    # abonado nada (verifica que el abono si redujo la base del tramo
    # siguiente, no solo que se resto del total al final).
    sin_abono = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=capital,
        fecha_origen=fecha_origen,
        abonos=[],
        fecha_liquidacion_final=fecha_corte,
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )
    assert resultado.capital_insoluto_indexado < sin_abono.capital_insoluto_indexado


def test_un_abono_que_no_cubre_los_intereses_no_reduce_el_capital_y_acumula_pendiente():
    fecha_origen = date(2024, 7, 1)
    fecha_abono = date(2025, 1, 1)
    fecha_corte = date(2025, 12, 31)
    capital = Decimal("1000000.00")

    resultado = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=capital,
        fecha_origen=fecha_origen,
        abonos=[(fecha_abono, Decimal("1.00"))],  # abono minimo, no cubre ni los intereses
        fecha_liquidacion_final=fecha_corte,
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )

    ipc_origen = get_ipc_interpolado_for_date(fecha_origen)
    ipc_abono = get_ipc_interpolado_for_date(fecha_abono)
    capital_indexado_tramo1 = (capital * (ipc_abono / ipc_origen)).quantize(Decimal("0.01"))

    # El capital base del tramo siguiente debe ser el capital YA indexado
    # (sin restar el abono, que se fue integro a intereses pendientes) --
    # verificado indirectamente: el capital final debe coincidir con
    # continuar indexando ese mismo capital_indexado_tramo1 hasta el corte,
    # sin abonos de por medio.
    continuacion = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=capital_indexado_tramo1,
        fecha_origen=fecha_abono,
        abonos=[],
        fecha_liquidacion_final=fecha_corte,
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )
    assert resultado.capital_insoluto_indexado == continuacion.capital_insoluto_indexado
    # Los intereses pendientes de cobro deben ser mayores que si no hubiera
    # habido ningun tramo previo con interes sin pagar (el pendiente se
    # acarrea y se suma al del tramo final).
    assert resultado.intereses_pendientes_cobro > continuacion.intereses_pendientes_cobro


def test_capital_historico_inicial_cero_o_negativo_lanza_error():
    with pytest.raises(ValueError):
        liquidar_obligacion_con_abonos_tramo_por_tramo(
            capital_historico_inicial=Decimal("0.00"),
            fecha_origen=date(2024, 1, 1),
            abonos=[],
            fecha_liquidacion_final=date(2024, 12, 31),
            tasa_interes_mensual=TASA_MENSUAL_6_EA,
        )


def test_fecha_liquidacion_final_no_posterior_a_origen_lanza_error():
    with pytest.raises(ValueError):
        liquidar_obligacion_con_abonos_tramo_por_tramo(
            capital_historico_inicial=Decimal("1000000.00"),
            fecha_origen=date(2024, 1, 1),
            abonos=[],
            fecha_liquidacion_final=date(2024, 1, 1),
            tasa_interes_mensual=TASA_MENSUAL_6_EA,
        )


def test_tasa_interes_negativa_lanza_error():
    with pytest.raises(ValueError):
        liquidar_obligacion_con_abonos_tramo_por_tramo(
            capital_historico_inicial=Decimal("1000000.00"),
            fecha_origen=date(2024, 1, 1),
            abonos=[],
            fecha_liquidacion_final=date(2024, 12, 31),
            tasa_interes_mensual=Decimal("-0.01"),
        )


def test_abono_fuera_de_rango_lanza_error():
    with pytest.raises(ValueError, match="fuera del rango"):
        liquidar_obligacion_con_abonos_tramo_por_tramo(
            capital_historico_inicial=Decimal("1000000.00"),
            fecha_origen=date(2024, 1, 1),
            abonos=[(date(2025, 6, 1), Decimal("100000.00"))],
            fecha_liquidacion_final=date(2024, 12, 31),
            tasa_interes_mensual=TASA_MENSUAL_6_EA,
        )


def test_abono_mayor_a_la_deuda_del_tramo_no_deja_gran_total_negativo():
    # Sprint 110, hallazgo 4: un abono que supera la deuda (intereses +
    # capital) de un tramo dejaba capital_base negativo, arrastrado a los
    # tramos siguientes -- reproducido con el caso exacto del sprint (capital
    # $1.000.000, abono de $50.000.000 el 2024-06-01, corte 2025-01-01)
    # producia gran_total_adeudado == -54.034.338,13 antes de este fix.
    resultado = liquidar_obligacion_con_abonos_tramo_por_tramo(
        capital_historico_inicial=Decimal("1000000.00"),
        fecha_origen=date(2024, 1, 1),
        abonos=[(date(2024, 6, 1), Decimal("50000000.00"))],
        fecha_liquidacion_final=date(2025, 1, 1),
        tasa_interes_mensual=TASA_MENSUAL_6_EA,
    )

    assert resultado.gran_total_adeudado >= Decimal("0.00")
    assert resultado.capital_insoluto_indexado >= Decimal("0.00")


def test_abono_cero_o_negativo_lanza_error():
    with pytest.raises(ValueError):
        liquidar_obligacion_con_abonos_tramo_por_tramo(
            capital_historico_inicial=Decimal("1000000.00"),
            fecha_origen=date(2024, 1, 1),
            abonos=[(date(2024, 6, 1), Decimal("0.00"))],
            fecha_liquidacion_final=date(2024, 12, 31),
            tasa_interes_mensual=TASA_MENSUAL_6_EA,
        )
