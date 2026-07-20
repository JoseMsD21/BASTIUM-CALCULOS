from decimal import Decimal

from app.engine.tax.renta_liquida import depurar_renta_liquida_gravable


def test_flujo_base_sin_perdida_calcula_cada_paso_intermedio():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("1000000.00"),
        devoluciones_rebajas_descuentos=Decimal("50000.00"),
        costos=Decimal("300000.00"),
        deducciones=Decimal("200000.00"),
        rentas_exentas=Decimal("100000.00"),
    )
    assert resultado.ingresos_netos == Decimal("950000.00")
    assert resultado.renta_bruta == Decimal("650000.00")
    assert resultado.renta_liquida == Decimal("450000.00")
    assert resultado.hubo_perdida_liquida is False
    assert resultado.renta_liquida_gravable == Decimal("350000.00")


def test_perdida_liquida_fija_renta_gravable_en_cero_sin_restar_exentas():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("100000.00"),
        devoluciones_rebajas_descuentos=Decimal("0.00"),
        costos=Decimal("50000.00"),
        deducciones=Decimal("80000.00"),
        rentas_exentas=Decimal("10000.00"),
    )
    assert resultado.renta_liquida == Decimal("-30000.00")
    assert resultado.hubo_perdida_liquida is True
    assert resultado.renta_liquida_gravable == Decimal("0.00")


def test_rentas_exentas_mayores_a_renta_liquida_topa_en_cero_sin_quedar_negativa():
    resultado = depurar_renta_liquida_gravable(
        ingresos_brutos=Decimal("500000.00"),
        devoluciones_rebajas_descuentos=Decimal("0.00"),
        costos=Decimal("100000.00"),
        deducciones=Decimal("100000.00"),
        rentas_exentas=Decimal("400000.00"),
    )
    assert resultado.renta_liquida == Decimal("300000.00")
    assert resultado.hubo_perdida_liquida is False
    assert resultado.renta_liquida_gravable == Decimal("0.00")
