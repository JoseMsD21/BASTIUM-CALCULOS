from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import PendingDebt
from app.services.cascada_cuotas import distribuir_pago_en_cascada


def _deuda(principal: str, interest: str) -> PendingDebt:
    return PendingDebt(
        principal=Decimal(principal), interest=Decimal(interest), indexation=Decimal("0.00")
    )


def test_ejemplo_del_usuario_abril_marzo_febrero():
    # Reproduce la mecanica del ejemplo del usuario (capital de la cuota mas
    # reciente primero, luego capital+interes de las anteriores, y solo una
    # parte de los intereses de la cuota mas antigua si el pago no alcanza
    # para todo) con montos elegidos a mano para que la aritmetica cierre
    # exacto -- no se derivan de una tasa anual real, eso se prueba aparte en
    # el test de integracion (Task 6).
    cuotas_y_deuda = [
        ("abril", _deuda("150000.00", "0.00")),
        ("marzo", _deuda("150000.00", "20000.00")),
        ("febrero", _deuda("150000.00", "45000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("500000.00"), date(2024, 4, 1)
    )

    # abril: 150.000 de capital, interes 0 (recien nace ese dia).
    # marzo: 150.000 capital + 20.000 interes completo = 170.000.
    # febrero: 150.000 capital + solo 30.000 de sus 45.000 de interes = 180.000
    #          (los 15.000 restantes de interes de febrero quedan debidos, pero
    #          su capital ya esta pagado y no genera intereses nuevos).
    assert asignaciones[0][1] == Decimal("150000.00")  # abril
    assert asignaciones[1][1] == Decimal("170000.00")  # marzo
    assert asignaciones[2][1] == Decimal("180000.00")  # febrero
    assert sum(monto for _, monto in asignaciones) == Decimal("500000.00")
    assert remanente == Decimal("0.00")


def test_pago_exacto_para_una_sola_cuota_no_toca_la_siguiente():
    cuotas_y_deuda = [
        ("marzo", _deuda("150000.00", "0.00")),
        ("febrero", _deuda("150000.00", "3000.00")),
    ]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("150000.00"), date(2024, 3, 1)
    )
    assert len(asignaciones) == 1
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("0.00")


def test_remanente_sobrante_cuando_el_pago_excede_todas_las_cuotas():
    cuotas_y_deuda = [("marzo", _deuda("150000.00", "0.00"))]
    asignaciones, remanente = distribuir_pago_en_cascada(
        cuotas_y_deuda, Decimal("200000.00"), date(2024, 3, 1)
    )
    assert asignaciones[0][1] == Decimal("150000.00")
    assert remanente == Decimal("50000.00")
