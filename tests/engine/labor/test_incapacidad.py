from decimal import Decimal

from app.engine.labor.incapacidad import IncapacidadCalculator
from database.models import TipoEventoLaboral


def test_incapacidad_comun_un_dia_solo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=1,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("66670.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "EMPLEADOR"
    assert resultado.tramos[0].dias == 1


def test_incapacidad_comun_dos_dias_solo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=2,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "EMPLEADOR"


def test_incapacidad_comun_tres_dias_cruza_a_eps():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=3,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")  # solo dias 1-2
    assert len(resultado.tramos) == 2
    assert resultado.tramos[1].pagador == "EPS"
    assert resultado.tramos[1].dias == 1
    assert resultado.tramos[1].monto == Decimal("66670.00")


def test_incapacidad_comun_dia_90_ultimo_dia_del_tramo_eps_66pct():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=90,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 2
    assert resultado.tramos[1].dias == 88
    assert resultado.tramos[1].monto == Decimal("5866960.00")


def test_incapacidad_comun_dia_91_entra_tramo_eps_50pct():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=91,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 3
    assert resultado.tramos[2].pagador == "EPS"
    assert resultado.tramos[2].dias == 1
    assert resultado.tramos[2].porcentaje == Decimal("0.50")
    assert resultado.tramos[2].monto == Decimal("50000.00")


def test_incapacidad_comun_dia_180_ultimo_dia_modelado():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=180,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("133340.00")
    assert len(resultado.tramos) == 3
    assert resultado.tramos[2].dias == 90
    assert resultado.tramos[2].monto == Decimal("4500000.00")


def test_incapacidad_laboral_arl_paga_100pct_desde_dia_1_nada_a_cargo_empleador():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=10,
    )

    assert resultado.monto_a_cargo_empleador == Decimal("0.00")
    assert len(resultado.tramos) == 1
    assert resultado.tramos[0].pagador == "ARL"
    assert resultado.tramos[0].porcentaje == Decimal("1.00")
    assert resultado.tramos[0].monto == Decimal("1000000.00")


def test_incapacidad_comun_cero_dias_no_genera_tramos():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=0,
    )

    assert resultado.tramos == []
    assert resultado.monto_a_cargo_empleador == Decimal("0.00")


def test_incapacidad_laboral_cero_dias_no_genera_tramos():
    resultado = IncapacidadCalculator.calcular(
        tipo=TipoEventoLaboral.INCAPACIDAD_LABORAL,
        ibc_mensual=Decimal("3000000.00"),
        dias_incapacidad=0,
    )

    assert resultado.tramos == []
    assert resultado.monto_a_cargo_empleador == Decimal("0.00")
