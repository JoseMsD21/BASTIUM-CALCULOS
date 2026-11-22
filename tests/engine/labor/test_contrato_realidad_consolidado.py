"""Sprint 94: consolidado multi-año de contrato realidad (plantillas L7
privado / L8 publico) con las respuestas del despacho del 16/11/2026:

- Aportes a salud/pension omitidos: el empleador cubre el 100 % de la
  cotizacion omisa (SS_SALUD_PCT / SS_PENSION_PCT, total empleador +
  trabajador), sin descontar el 4 % del trabajador -- o el 100 % del calculo
  actuarial de pension.
- Bonificacion por servicio del Decreto 0320/2026: solo sector publico,
  nunca privado.

Todos los valores esperados se calcularon a mano (ver comentarios).
"""

from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import pytest

import database.session as session_module
from app.engine.labor.calculo_actuarial import ReservaActuarial
from app.engine.labor.contrato_realidad import (
    TOPE_DECRETO_0320_2026,
    AnioContratoRealidadPrivado,
    AnioContratoRealidadPublico,
    SectorContratoRealidad,
    liquidar_contrato_realidad_privado,
    liquidar_contrato_realidad_publico,
    porcentaje_bonificacion_por_servicio,
)
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _parametros_en_memoria():
    # IPC de cierre de año: la plantilla usa como "IPC" del año Y el indice de
    # cierre del año Y-1 (su tabla trae 2019 = 100,00 y 2020 = 103,80, es
    # decir, el cierre de 2019). Con estos indices:
    #   IPC(2020) = cierre 2019 = 100, IPC(2021) = 110, IPC(2022) = 121.
    session = session_module.get_session()
    indices = {
        2019: Decimal("100"),
        2020: Decimal("110"),
        2021: Decimal("121"),
        2025: Decimal("200"),
    }
    for anio, valor in indices.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    for clave, valor in {
        "SS_PENSION_PCT": Decimal("0.16"),
        "SS_SALUD_PCT": Decimal("0.125"),
    }.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=_dt.now(),
        ))
    session.commit()
    session.close()


def _filas_privado():
    return [
        AnioContratoRealidadPrivado(2020, salario_mensual=Decimal("1200000"), meses=Decimal("12")),
        AnioContratoRealidadPrivado(2021, salario_mensual=Decimal("1500000"), meses=Decimal("6")),
        AnioContratoRealidadPrivado(2022, salario_mensual=Decimal("2400000"), meses=Decimal("3")),
    ]


# ---------------------------------------------------------------------------
# Privado (plantilla L7)
# ---------------------------------------------------------------------------


def test_privado_fila_por_fila_patron_l7():
    liq = liquidar_contrato_realidad_privado(_filas_privado(), anio_final=2022)
    f2020, f2021, f2022 = liq.filas

    # 2020: factor 121/100 = 1,21. Salarios 1.200.000 x 12 = 14.400.000.
    assert f2020.factor_ipc == Decimal("1.21")
    assert f2020.total_salarios == Decimal("14400000.00")
    # Cesantias 1.200.000/12 x 12 = 1.200.000; indexadas x 1,21 = 1.452.000.
    assert f2020.cesantias == Decimal("1200000.00")
    assert f2020.cesantias_indexadas == Decimal("1452000.00")
    # Intereses = cesantias indexadas x meses/100 = 1.452.000 x 12 % = 174.240.
    assert f2020.intereses_cesantias == Decimal("174240.00")
    assert f2020.primas_indexadas == Decimal("1452000.00")
    # Vacaciones = primas / 2 = 600.000; indexadas 726.000.
    assert f2020.vacaciones == Decimal("600000.00")
    assert f2020.vacaciones_indexadas == Decimal("726000.00")
    # Aportes sobre salarios indexados 17.424.000: salud 12,5 % = 2.178.000,
    # pension 16 % = 2.787.840.
    assert f2020.aporte_salud == Decimal("2178000.00")
    assert f2020.aporte_pension == Decimal("2787840.00")

    # 2021: factor 121/110 = 1,1. 6 meses de 1.500.000.
    assert f2021.cesantias_indexadas == Decimal("825000.00")
    assert f2021.intereses_cesantias == Decimal("49500.00")  # 825.000 x 6/100
    assert f2021.vacaciones_indexadas == Decimal("412500.00")
    assert f2021.aporte_salud == Decimal("1237500.00")  # 9.900.000 x 12,5 %
    assert f2021.aporte_pension == Decimal("1584000.00")  # 9.900.000 x 16 %

    # 2022 = año final: factor 1.
    assert f2022.factor_ipc == Decimal("1")
    assert f2022.intereses_cesantias == Decimal("18000.00")  # 600.000 x 3/100


def test_privado_consolidado_patron_l7():
    liq = liquidar_contrato_realidad_privado(_filas_privado(), anio_final=2022)
    assert liq.total_salarios_sin_percibir == Decimal("30600000.00")  # sin indexar
    assert liq.total_cesantias_indexadas == Decimal("2877000.00")
    assert liq.total_intereses_cesantias == Decimal("241740.00")
    assert liq.total_primas_indexadas == Decimal("2877000.00")
    assert liq.total_vacaciones_indexadas == Decimal("1438500.00")
    assert liq.total_prestaciones_indexadas == Decimal("7434240.00")
    assert liq.total_aportes_salud == Decimal("4315500.00")
    assert liq.total_aportes_pension == Decimal("5523840.00")
    assert liq.total_prestaciones_sociales == Decimal("17273580.00")
    assert liq.total_prestaciones_mas_salarios == Decimal("47873580.00")
    assert liq.pension_por_calculo_actuarial is False


def test_privado_salud_no_descuenta_porcion_del_trabajador():
    # Despacho (16/11/2026): el empleador cubre el 100 % de la cotizacion
    # omisa; no descuenta el 4 % del trabajador. Sobre 17.424.000 la porcion
    # del empleador (8,5 %, la de la plantilla) seria 1.481.040; lo
    # reclamable es 8,5 % + 4 % = 12,5 % = 2.178.000.
    fila = liquidar_contrato_realidad_privado(_filas_privado()[:1], anio_final=2022).filas[0]
    assert fila.aporte_salud != Decimal("1481040.00")
    assert fila.aporte_salud == Decimal("1481040.00") + Decimal("696960.00")
    # Pension: 12 % del empleador (2.090.880) + 4 % del trabajador (696.960).
    assert fila.aporte_pension == Decimal("2090880.00") + Decimal("696960.00")


def test_privado_pension_por_calculo_actuarial_reemplaza_cotizacion():
    reserva = ReservaActuarial(
        vra=Decimal("9950000.00"), ca=Decimal("49750.00"), vr=Decimal("10000000.00")
    )
    liq = liquidar_contrato_realidad_privado(
        _filas_privado(), anio_final=2022, calculo_actuarial_pension=reserva
    )
    assert liq.pension_por_calculo_actuarial is True
    assert all(f.aporte_pension == Decimal("0.00") for f in liq.filas)
    assert liq.total_aportes_pension == Decimal("10000000.00")
    # Salud sigue por cotizacion omisa: 7.434.240 + 4.315.500 + 10.000.000.
    assert liq.total_prestaciones_sociales == Decimal("21749740.00")


def test_privado_calculo_actuarial_acepta_decimal():
    liq = liquidar_contrato_realidad_privado(
        _filas_privado(), anio_final=2022, calculo_actuarial_pension=Decimal("123.45")
    )
    assert liq.total_aportes_pension == Decimal("123.45")


def test_privado_no_tiene_bonificacion_por_servicio():
    # Decreto 0320/2026: exclusivo sector publico, nunca privado.
    liq = liquidar_contrato_realidad_privado(_filas_privado(), anio_final=2022)
    assert not hasattr(liq.filas[0], "bonificacion_servicio")
    with pytest.raises(ValueError):
        porcentaje_bonificacion_por_servicio(
            SectorContratoRealidad.PRIVADO, 2026, Decimal("2000000")
        )


def test_privado_meses_fraccionarios():
    # 1.200.000 x 1,5 meses (fraccion de mes de la plantilla), año final.
    fila = liquidar_contrato_realidad_privado(
        [AnioContratoRealidadPrivado(2022, Decimal("1200000"), Decimal("1.5"))], anio_final=2022
    ).filas[0]
    assert fila.total_salarios == Decimal("1800000.00")
    assert fila.cesantias == Decimal("150000.00")
    assert fila.intereses_cesantias == Decimal("2250.00")  # 150.000 x 1,5/100


@pytest.mark.parametrize(
    "filas, anio_final",
    [
        ([], 2022),
        ([AnioContratoRealidadPrivado(2023, Decimal("1"), Decimal("1"))], 2022),
        ([AnioContratoRealidadPrivado(2022, Decimal("-1"), Decimal("1"))], 2022),
        ([AnioContratoRealidadPrivado(2022, Decimal("1"), Decimal("-1"))], 2022),
        ([AnioContratoRealidadPrivado(2022, Decimal("1"), Decimal("13"))], 2022),
    ],
)
def test_privado_entradas_invalidas(filas, anio_final):
    with pytest.raises(ValueError):
        liquidar_contrato_realidad_privado(filas, anio_final=anio_final)


# ---------------------------------------------------------------------------
# Bonificacion por servicio (Decreto 0320/2026 / porcentaje de la plantilla L8)
# ---------------------------------------------------------------------------

_PUB = SectorContratoRealidad.PUBLICO


def test_decreto_0320_2026_hasta_el_tope_53():
    assert TOPE_DECRETO_0320_2026 == Decimal("2968262")
    assert porcentaje_bonificacion_por_servicio(_PUB, 2026, Decimal("2000000")) == Decimal("53")
    # Igual al tope: "<=" -> 53 %.
    assert porcentaje_bonificacion_por_servicio(_PUB, 2026, Decimal("2968262")) == Decimal("53")


def test_decreto_0320_2026_sobre_el_tope_38_sumando_gastos_representacion():
    # 2.500.000 + 500.000 = 3.000.000 > 2.968.262 -> 38 %.
    assert porcentaje_bonificacion_por_servicio(
        _PUB, 2026, Decimal("2500000"), gastos_representacion=Decimal("500000")
    ) == Decimal("38")


def test_decreto_0320_desde_2027_54_39_con_tope_explicito():
    assert porcentaje_bonificacion_por_servicio(
        _PUB, 2027, Decimal("3000000"), tope_decreto_0320=Decimal("3100000")
    ) == Decimal("54")
    assert porcentaje_bonificacion_por_servicio(
        _PUB, 2028, Decimal("3200000"), tope_decreto_0320=Decimal("3100000")
    ) == Decimal("39")


def test_decreto_0320_desde_2027_sin_tope_lanza_error():
    # El despacho solo dio el tope de 2026; no se supone para 2027+.
    with pytest.raises(ValueError):
        porcentaje_bonificacion_por_servicio(_PUB, 2027, Decimal("1000000"))


def test_bonificacion_antes_de_2026_usa_porcentaje_de_la_plantilla():
    assert porcentaje_bonificacion_por_servicio(
        _PUB, 2025, Decimal("1000000"), porcentaje_usuario=Decimal("35")
    ) == Decimal("35")
    with pytest.raises(ValueError):
        porcentaje_bonificacion_por_servicio(_PUB, 2025, Decimal("1000000"))


def test_desde_2026_el_decreto_prevalece_sobre_el_porcentaje_del_usuario():
    assert porcentaje_bonificacion_por_servicio(
        _PUB, 2026, Decimal("2000000"), porcentaje_usuario=Decimal("35")
    ) == Decimal("53")


# ---------------------------------------------------------------------------
# Publico (plantilla L8)
# ---------------------------------------------------------------------------


def _fila_publico_2021():
    return AnioContratoRealidadPublico(
        anio=2021,
        dias=Decimal("360"),
        meses=Decimal("12"),
        salario_mensual=Decimal("3000000"),
        auxilio_transporte=Decimal("100000"),
        auxilio_alimentacion=Decimal("200000"),
    )


def test_publico_fila_patron_l8():
    liq = liquidar_contrato_realidad_publico(
        [_fila_publico_2021()], anio_final=2022, dias_vacaciones=Decimal("15"),
        porcentaje_bonificacion_servicio=Decimal("50"),
    )
    f = liq.filas[0]
    assert f.factor_ipc == Decimal("1.1")
    assert f.auxilio_transporte_indexado == Decimal("110000.00")
    assert f.auxilio_alimentacion_indexado == Decimal("220000.00")
    # M = 3.000.000/30 x 360
    assert f.total_salarios == Decimal("36000000.00")
    # Y = 3.000.000 x 50 % / 12 x 12
    assert f.porcentaje_bonificacion_servicio == Decimal("50")
    assert f.bonificacion_servicio == Decimal("1500000.00")
    assert f.bonificacion_servicio_indexada == Decimal("1650000.00")
    # Q = (3.000.000 + 1.500.000)/12 x 12/2
    assert f.prima_servicio == Decimal("2250000.00")
    assert f.prima_servicio_indexada == Decimal("2475000.00")
    # W = ((Q+Y)/12 + (H+I+K))/30 x 15 x 360/360 = (312.500 + 3.300.000)/2
    assert f.prima_vacaciones == Decimal("1806250.00")
    assert f.prima_vacaciones_indexada == Decimal("1986875.00")
    # S = ((Q+Y+W)/12 + H)/12 x 12 = 5.556.250/12 + 3.000.000
    assert f.prima_navidad == Decimal("3463020.83")
    assert f.prima_navidad_indexada == Decimal("3809322.92")
    # N = ((Q+S+W+Y)/12 + H)/360 x 360
    assert f.cesantias == Decimal("3751605.90")
    assert f.cesantias_indexadas == Decimal("4126766.49")
    # P = O x 12 % / 360 x 360
    assert f.intereses_cesantias == Decimal("495211.98")
    # U = ((Q+Y)/12 + (H+I+K))/30 x 15 dias x 360/360 (igual a W con 15 dias)
    assert f.vacaciones == Decimal("1806250.00")
    assert f.vacaciones_indexadas == Decimal("1986875.00")
    # AA = 3.000.000/30 x 2
    assert f.bonificacion_recreacion == Decimal("200000.00")
    assert f.bonificacion_recreacion_indexada == Decimal("220000.00")
    # Aportes 100 % sobre 36.000.000 x 1,1 = 39.600.000.
    assert f.aporte_salud == Decimal("4950000.00")
    assert f.aporte_pension == Decimal("6336000.00")


def test_publico_consolidado_patron_l8():
    liq = liquidar_contrato_realidad_publico(
        [_fila_publico_2021()], anio_final=2022, dias_vacaciones=Decimal("15"),
        porcentaje_bonificacion_servicio=Decimal("50"),
    )
    # 110.000 + 220.000 + 4.126.766,49 + 495.211,98 + 2.475.000 + 3.809.322,92
    # + 1.986.875 + 1.986.875 + 1.650.000 + 220.000
    assert liq.total_prestaciones_indexadas == Decimal("17080051.39")
    assert liq.total_aportes_salud == Decimal("4950000.00")
    assert liq.total_aportes_pension == Decimal("6336000.00")
    assert liq.gran_total == Decimal("28366051.39")


def test_publico_2026_aplica_decreto_0320():
    # Año final 2026 (factor 1). 2.000.000 <= tope -> 53 %:
    # Y = 2.000.000 x 53 % / 12 x 12 = 1.060.000.
    fila = AnioContratoRealidadPublico(
        anio=2026, dias=Decimal("360"), meses=Decimal("12"), salario_mensual=Decimal("2000000")
    )
    f = liquidar_contrato_realidad_publico(
        [fila], anio_final=2026, dias_vacaciones=Decimal("15")
    ).filas[0]
    assert f.factor_ipc == Decimal("1")
    assert f.porcentaje_bonificacion_servicio == Decimal("53")
    assert f.bonificacion_servicio == Decimal("1060000.00")


def test_publico_2026_bonificacion_sobre_asignacion_mas_gastos_representacion():
    # 2.500.000 + 500.000 = 3.000.000 > tope -> 38 % x 3.000.000 = 1.140.000.
    fila = AnioContratoRealidadPublico(
        anio=2026, dias=Decimal("360"), meses=Decimal("12"), salario_mensual=Decimal("2500000"),
        gastos_representacion=Decimal("500000"),
    )
    f = liquidar_contrato_realidad_publico(
        [fila], anio_final=2026, dias_vacaciones=Decimal("15")
    ).filas[0]
    assert f.porcentaje_bonificacion_servicio == Decimal("38")
    assert f.bonificacion_servicio == Decimal("1140000.00")


def test_publico_antes_de_2026_sin_porcentaje_lanza_error():
    with pytest.raises(ValueError):
        liquidar_contrato_realidad_publico(
            [_fila_publico_2021()], anio_final=2022, dias_vacaciones=Decimal("15")
        )


def test_publico_pension_por_calculo_actuarial():
    liq = liquidar_contrato_realidad_publico(
        [_fila_publico_2021()], anio_final=2022, dias_vacaciones=Decimal("15"),
        porcentaje_bonificacion_servicio=Decimal("50"),
        calculo_actuarial_pension=Decimal("20000000"),
    )
    assert liq.filas[0].aporte_pension == Decimal("0.00")
    assert liq.total_aportes_pension == Decimal("20000000.00")
    assert liq.gran_total == (
        Decimal("17080051.39") + Decimal("4950000.00") + Decimal("20000000.00")
    )
