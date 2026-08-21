from decimal import Decimal

import pytest

from app.engine.labor.contrato_realidad import (
    calcular_aporte_contrato_realidad,
    calcular_bonificacion_por_servicio_escalonada,
)


def test_aporte_aplica_base_por_porcentaje():
    # $2.000.000 x 12% = 240.000
    resultado = calcular_aporte_contrato_realidad(Decimal("2000000"), Decimal("12"))
    assert resultado == Decimal("240000.00")


def test_aporte_con_porcentaje_cero_da_cero():
    resultado = calcular_aporte_contrato_realidad(Decimal("2000000"), Decimal("0"))
    assert resultado == Decimal("0.00")


def test_aporte_acepta_enteros_ademas_de_decimal():
    resultado = calcular_aporte_contrato_realidad(2000000, 8)
    assert resultado == Decimal("160000.00")


def test_aporte_base_negativa_lanza_error():
    with pytest.raises(ValueError):
        calcular_aporte_contrato_realidad(Decimal("-1"), Decimal("12"))


def test_aporte_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_aporte_contrato_realidad(Decimal("2000000"), Decimal("-1"))


def test_bonificacion_usa_porcentaje_estandar_cuando_no_aplica_elevado():
    # $3.000.000 x 35% = 1.050.000
    resultado = calcular_bonificacion_por_servicio_escalonada(
        base=Decimal("3000000"),
        aplica_porcentaje_elevado=False,
        porcentaje_estandar=Decimal("35"),
        porcentaje_elevado=Decimal("50"),
    )
    assert resultado == Decimal("1050000.00")


def test_bonificacion_usa_porcentaje_elevado_cuando_aplica():
    # $1.500.000 x 50% = 750.000
    resultado = calcular_bonificacion_por_servicio_escalonada(
        base=Decimal("1500000"),
        aplica_porcentaje_elevado=True,
        porcentaje_estandar=Decimal("35"),
        porcentaje_elevado=Decimal("50"),
    )
    assert resultado == Decimal("750000.00")


def test_bonificacion_acepta_enteros_ademas_de_decimal():
    resultado = calcular_bonificacion_por_servicio_escalonada(
        base=1000000,
        aplica_porcentaje_elevado=False,
        porcentaje_estandar=35,
        porcentaje_elevado=50,
    )
    assert resultado == Decimal("350000.00")


def test_bonificacion_base_negativa_lanza_error():
    with pytest.raises(ValueError):
        calcular_bonificacion_por_servicio_escalonada(
            base=Decimal("-1"),
            aplica_porcentaje_elevado=False,
            porcentaje_estandar=Decimal("35"),
            porcentaje_elevado=Decimal("50"),
        )


def test_bonificacion_porcentaje_negativo_lanza_error():
    with pytest.raises(ValueError):
        calcular_bonificacion_por_servicio_escalonada(
            base=Decimal("1000000"),
            aplica_porcentaje_elevado=False,
            porcentaje_estandar=Decimal("-1"),
            porcentaje_elevado=Decimal("50"),
        )
