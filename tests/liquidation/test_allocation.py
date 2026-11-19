from datetime import date
from decimal import Decimal

from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.models import PendingDebt


def test_full_payment_allocation():
    debt = PendingDebt(Decimal("1000.00"), Decimal("200.00"), Decimal("50.00"))
    payment_amount = Decimal("1250.00")

    allocation, new_debt, remainder = AllocationEngine.allocate(
        payment_amount, debt, date(2026, 7, 12)
    )

    assert allocation.to_indexation == Decimal("50.00")
    assert allocation.to_interest == Decimal("200.00")
    assert allocation.to_principal == Decimal("1000.00")
    assert new_debt.total() == Decimal("0.00")
    assert remainder == Decimal("0.00")


def test_partial_payment_interest_only():
    debt = PendingDebt(Decimal("1000.00"), Decimal("200.00"), Decimal("50.00"))
    payment_amount = Decimal("150.00")

    allocation, new_debt, remainder = AllocationEngine.allocate(
        payment_amount, debt, date(2026, 7, 12)
    )

    assert allocation.to_indexation == Decimal("50.00")
    assert allocation.to_interest == Decimal("100.00")
    assert allocation.to_principal == Decimal("0.00")

    # El capital sigue intacto, los intereses bajaron a 100
    assert new_debt.principal == Decimal("1000.00")
    assert new_debt.interest == Decimal("100.00")
    assert new_debt.indexation == Decimal("0.00")
    assert remainder == Decimal("0.00")


def test_overpayment_generates_remainder():
    debt = PendingDebt(Decimal("500.00"), Decimal("0.00"), Decimal("0.00"))
    payment_amount = Decimal("600.00")

    allocation, new_debt, remainder = AllocationEngine.allocate(
        payment_amount, debt, date(2026, 7, 12)
    )

    assert allocation.to_principal == Decimal("500.00")
    assert new_debt.total() == Decimal("0.00")
    assert remainder == Decimal("100.00")  # Saldo a favor


def test_allocate_capital_primero_paga_capital_antes_que_interes():
    deuda = PendingDebt(
        principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00")
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_capital_primero(
        Decimal("100000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_principal == Decimal("100000.00")
    assert allocation.to_interest == Decimal("0.00")
    assert nueva_deuda.principal == Decimal("0.00")
    assert nueva_deuda.interest == Decimal("30000.00")  # intereses quedan intactos, "congelados"
    assert remanente == Decimal("0.00")


def test_allocate_capital_primero_cubre_capital_y_parte_del_interes():
    deuda = PendingDebt(
        principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00")
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_capital_primero(
        Decimal("120000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_principal == Decimal("100000.00")
    assert allocation.to_interest == Decimal("20000.00")
    assert nueva_deuda.principal == Decimal("0.00")
    assert nueva_deuda.interest == Decimal("10000.00")
    assert remanente == Decimal("0.00")


def test_allocate_capital_primero_no_cambia_el_orden_de_allocate_por_defecto():
    deuda = PendingDebt(
        principal=Decimal("100000.00"), interest=Decimal("30000.00"), indexation=Decimal("0.00")
    )
    allocation, _, _ = AllocationEngine.allocate(Decimal("50000.00"), deuda, date(2024, 4, 1))
    assert allocation.to_interest == Decimal("30000.00")
    assert allocation.to_principal == Decimal("20000.00")


# --- Sprint 84: imputacion proporcional (Art. 804 E.T.), solo Tributario ---


def test_allocate_proporcional_reparte_el_abono_segun_el_peso_de_cada_concepto():
    # Deuda total 1.500.000: impuesto 1.000.000 (2/3), intereses 200.000 (2/15),
    # sanciones 300.000 (1/5). Abono 300.000:
    #   sanciones  = 300.000 x 300.000 / 1.500.000 = 60.000
    #   intereses  = 300.000 x 200.000 / 1.500.000 = 40.000
    #   impuesto   = 300.000 x 1.000.000 / 1.500.000 = 200.000
    deuda = PendingDebt(
        principal=Decimal("1000000.00"),
        interest=Decimal("200000.00"),
        indexation=Decimal("300000.00"),
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("300000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_indexation == Decimal("60000.00")
    assert allocation.to_interest == Decimal("40000.00")
    assert allocation.to_principal == Decimal("200000.00")
    assert allocation.total_payment == Decimal("300000.00")
    assert nueva_deuda.principal == Decimal("800000.00")
    assert nueva_deuda.interest == Decimal("160000.00")
    assert nueva_deuda.indexation == Decimal("240000.00")
    assert remanente == Decimal("0.00")


def test_allocate_proporcional_paga_costas_primero_y_reparte_el_resto():
    # Sprint 79: costas siempre primero. Abono 350.000 - costas 50.000 = 300.000
    # que se reparte igual que en el test anterior.
    deuda = PendingDebt(
        principal=Decimal("1000000.00"),
        interest=Decimal("200000.00"),
        indexation=Decimal("300000.00"),
        costas=Decimal("50000.00"),
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("350000.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_costas == Decimal("50000.00")
    assert allocation.to_indexation == Decimal("60000.00")
    assert allocation.to_interest == Decimal("40000.00")
    assert allocation.to_principal == Decimal("200000.00")
    assert nueva_deuda.costas == Decimal("0.00")
    assert remanente == Decimal("0.00")


def test_allocate_proporcional_abono_menor_que_las_costas_solo_paga_costas():
    deuda = PendingDebt(
        principal=Decimal("1000.00"),
        interest=Decimal("100.00"),
        indexation=Decimal("0.00"),
        costas=Decimal("500.00"),
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("200.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_costas == Decimal("200.00")
    assert allocation.to_interest == Decimal("0.00")
    assert allocation.to_principal == Decimal("0.00")
    assert nueva_deuda.costas == Decimal("300.00")
    assert remanente == Decimal("0.00")


def test_allocate_proporcional_el_centavo_de_redondeo_va_al_impuesto():
    # 100 / 3 = 33,333... -> 33,33 a sanciones y 33,33 a intereses; el impuesto
    # recibe el resto (100,00 - 66,66 = 33,34) para que el abono cuadre al centavo.
    deuda = PendingDebt(
        principal=Decimal("100.00"), interest=Decimal("100.00"), indexation=Decimal("100.00")
    )
    allocation, nueva_deuda, _ = AllocationEngine.allocate_proporcional_art_804(
        Decimal("100.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_indexation == Decimal("33.33")
    assert allocation.to_interest == Decimal("33.33")
    assert allocation.to_principal == Decimal("33.34")
    assert nueva_deuda.total() == Decimal("200.00")


def test_allocate_proporcional_abono_que_excede_la_deuda_deja_remanente():
    deuda = PendingDebt(
        principal=Decimal("1000.00"),
        interest=Decimal("100.00"),
        indexation=Decimal("50.00"),
        costas=Decimal("10.00"),
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("1200.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.total_payment == Decimal("1160.00")
    assert nueva_deuda.total() == Decimal("0.00")
    assert remanente == Decimal("40.00")


def test_allocate_proporcional_sin_deuda_devuelve_todo_como_remanente():
    deuda = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    allocation, _, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("500.00"), deuda, date(2024, 4, 1)
    )
    assert allocation.total_payment == Decimal("0.00")
    assert remanente == Decimal("500.00")


def test_allocate_proporcional_redondeo_nunca_deja_saldos_negativos():
    # 0,01 / 2 = 0,005 -> ambos redondean a 0,01 (HALF_UP), mas que el abono.
    # El reparto debe seguir cuadrando al centavo sin saldos negativos.
    deuda = PendingDebt(
        principal=Decimal("0.00"), interest=Decimal("1.00"), indexation=Decimal("1.00")
    )
    allocation, nueva_deuda, remanente = AllocationEngine.allocate_proporcional_art_804(
        Decimal("0.01"), deuda, date(2024, 4, 1)
    )
    assert allocation.to_indexation + allocation.to_interest + allocation.to_principal == (
        Decimal("0.01")
    )
    assert allocation.to_principal == Decimal("0.00")
    assert min(nueva_deuda.principal, nueva_deuda.interest, nueva_deuda.indexation) >= 0
    assert remanente == Decimal("0.00")
