from datetime import date
from decimal import Decimal

from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.engine import LiquidationCore
from app.engine.temporal.schedulers.base import Event


def test_engine_processes_chronological_events():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(date=date(2026, 1, 15), payload={"amount": Decimal("50.00")}, event_type="INTEREST"),
        Event(date=date(2026, 1, 31), payload={"amount": Decimal("500.00")}, event_type="PAYMENT"),
    ]

    # 1. Instanciamos el motor con una tasa de control (0%) para probar puramente la imputación
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)

    # 2. Definimos la fecha de corte exacta del último evento
    cutoff = date(2026, 1, 31)

    # 3. Procesamos inyectando el límite temporal
    result = engine.process(events, cutoff_date=cutoff)

    # Validaciones estables
    assert len(result.items) == 3
    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("550.00")
    assert final_debt.interest == Decimal("0.00")
    assert result.total_payments_applied() == Decimal("500.00")


def test_engine_popula_rate_source_desde_el_rate_provider():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
    ]
    provider = MemoryRateProvider()
    provider.add_rate_period(
        date(2025, 12, 31),
        date(2026, 1, 31),
        Rate.from_percent(Decimal("1.0")),
        source="Tasa de prueba",
    )
    engine = LiquidationCore(rate_provider=provider)

    result = engine.process(events, cutoff_date=date(2026, 1, 1))

    assert all(item.rate_source == "Tasa de prueba" for item in result.items)


def test_engine_rate_source_es_na_sin_rate_provider():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
    ]
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("0.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 1))

    assert all(item.rate_source == "N/A" for item in result.items)


def test_capitalizacion_intereses_anatocismo_traslada_interes_devengado_al_capital():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 31), payload={}, event_type="CAPITALIZACION_INTERESES_ANATOCISMO"
        ),
    ]
    # 1% diario sobre 1000.00 durante 30 dias (2026-01-02 a 2026-01-31) = 300.00 exacto
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("1.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 31))

    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("1300.00")
    assert final_debt.interest == Decimal("0.00")


def test_capitalizacion_intereses_anatocismo_con_interes_ya_pagado_no_capitaliza_nada():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("1000.00"), "reference": ""},
            event_type="PAYMENT",
        ),
        Event(
            date=date(2026, 1, 31), payload={}, event_type="CAPITALIZACION_INTERESES_ANATOCISMO"
        ),
    ]
    engine = LiquidationCore(default_daily_rate=Rate.from_percent(Decimal("1.0")))

    result = engine.process(events, cutoff_date=date(2026, 1, 31))

    final_debt = result.final_balance()
    assert final_debt.principal == Decimal("0.00")
    assert final_debt.interest == Decimal("0.00")


def test_engine_usar_suma_unica_false_interes_solo_sobre_principal():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))  # 1% diario plano, tasa de control
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=False)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    fb = result.final_balance()
    assert fb.principal == Decimal("1000.00")
    assert fb.indexation == Decimal("500.00")
    # 10 dias * 1000.00 * 1% = 100.00 -- solo sobre principal, indexation no cuenta
    assert fb.interest == Decimal("100.00")


def test_engine_usar_suma_unica_true_interes_sobre_principal_mas_indexation():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=True)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    fb = result.final_balance()
    assert fb.principal == Decimal("1000.00")
    assert fb.indexation == Decimal("500.00")
    # 10 dias * (1000.00 + 500.00) * 1% = 150.00 -- interes sobre capital ya indexado
    assert fb.interest == Decimal("150.00")


def test_engine_usar_suma_unica_default_es_false():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate)  # sin pasar usar_suma_unica

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    assert result.final_balance().interest == Decimal("100.00")


def test_engine_usar_suma_unica_true_accrues_interest_when_only_indexation_present():
    # Escenario borde: principal en 0 (nunca hubo evento de capital), solo un
    # evento INDEXATION. Con usar_suma_unica=True, el interes debe correr sobre
    # ese saldo aunque principal sea 0 -- el guard de _accrue_time_passage debe
    # evaluar capital_base, no solo principal.
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=True)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    fb = result.final_balance()
    assert fb.principal == Decimal("0.00")
    assert fb.indexation == Decimal("500.00")
    # 10 dias * 500.00 * 1% = 50.00
    assert fb.interest == Decimal("50.00")


def test_engine_usar_suma_unica_false_no_accrual_when_only_indexation_present():
    # Mismo escenario pero usar_suma_unica=False: capital_base == principal == 0,
    # el guard debe seguir bloqueando la acumulacion (sin cambio de comportamiento
    # respecto a antes de este sprint).
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=False)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    assert result.final_balance().interest == Decimal("0.00")


def test_engine_usar_suma_unica_true_capital_base_en_liquidation_item_incluye_indexation():
    # LiquidationItem.capital_base existe "para que el juez pueda auditar la
    # trazabilidad" (ver docstring de LiquidationItem) -- bajo Suma Unica debe
    # reflejar la base real que genero el interes (principal + indexation), no
    # solo principal, o el rubro auditado quedaria inconsistente con el interes
    # reportado en la misma fila/corte.
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=True)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    item_indexation = next(i for i in result.items if i.balance.event_type == "INDEXATION")
    assert item_indexation.capital_base == Decimal("1500.00")

    item_cierre = result.items[-1]
    assert item_cierre.capital_base == Decimal("1500.00")


def test_engine_usar_suma_unica_false_capital_base_sigue_siendo_solo_principal():
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate, usar_suma_unica=False)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    item_indexation = next(i for i in result.items if i.balance.event_type == "INDEXATION")
    assert item_indexation.capital_base == Decimal("1000.00")

    item_cierre = result.items[-1]
    assert item_cierre.capital_base == Decimal("1000.00")


def test_engine_sobrepago_expone_remanente_como_saldo_a_favor():
    # Escenario del bug real (auditoria 2026-07-21): un abono de $10.000.000 contra
    # una deuda de $7.000.000. Antes de esta correccion, payment_amount guardaba el
    # monto nominal completo ($10.000.000) y el excedente de $3.000.000 desaparecia
    # sin dejar rastro en el LiquidationResult.
    events = [
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("7000000.00")},
            event_type="INSTALLMENT",
        ),
        Event(
            date=date(2026, 1, 10),
            payload={"amount": Decimal("10000000.00")},
            event_type="PAYMENT",
        ),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 10))

    item_pago = next(i for i in result.items if i.balance.event_type == "PAYMENT")
    assert item_pago.payment_amount == Decimal("7000000.00")
    assert item_pago.saldo_a_favor == Decimal("3000000.00")
    assert result.total_payments_applied() == Decimal("7000000.00")
    assert result.final_balance().total() == Decimal("0.00")


def test_engine_pago_exacto_no_genera_saldo_a_favor():
    events = [
        Event(
            date=date(2026, 1, 1),
            payload={"amount": Decimal("500000.00")},
            event_type="INSTALLMENT",
        ),
        Event(
            date=date(2026, 1, 10), payload={"amount": Decimal("500000.00")}, event_type="PAYMENT"
        ),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 10))

    item_pago = next(i for i in result.items if i.balance.event_type == "PAYMENT")
    assert item_pago.payment_amount == Decimal("500000.00")
    assert item_pago.saldo_a_favor == Decimal("0.00")


def test_engine_atribuye_interes_causado_por_paso_del_tiempo_a_cada_item():
    # Bug real (Sprint 40): la tabla de detalle del PDF mostraba 0 en la columna de
    # interes en todas las filas, aunque el interes si se causaba silenciosamente via
    # _accrue_time_passage (el saldo final de intereses ya era correcto). Cada fila
    # debe reflejar cuanto interes se causo desde el evento anterior hasta este.
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        # 10 dias de mora (2026-01-02 a 2026-01-11) sobre 1000.00 al 1% diario = 100.00
        Event(
            date=date(2026, 1, 11), payload={"amount": Decimal("500.00")}, event_type="INSTALLMENT"
        ),
        # 10 dias mas (2026-01-12 a 2026-01-21) sobre 1500.00 al 1% diario = 150.00
        Event(
            date=date(2026, 1, 21), payload={}, event_type="CAPITALIZACION_INTERESES_ANATOCISMO"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 21))

    item_segundo_installment = result.items[1]
    assert item_segundo_installment.interest_amount == Decimal("100.00")

    item_capitalizacion = result.items[2]
    assert item_capitalizacion.interest_amount == Decimal("150.00")

    # La primera fila no tuvo paso del tiempo antes (mismo dia del primer evento)
    assert result.items[0].interest_amount == Decimal("0.00")


def test_engine_suma_de_columna_interes_coincide_con_interes_final_sin_pagos():
    # Test de regresion clave del plan: sin pagos que reduzcan intereses ni
    # capitalizacion, la suma de interest_amount de todas las filas (incluida la fila
    # de cierre final) debe coincidir exactamente con final_debt.interest.
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 11), payload={"amount": Decimal("500.00")}, event_type="INSTALLMENT"
        ),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate)

    # Fecha de corte posterior al ultimo evento -- genera la fila de cierre final
    result = engine.process(events, cutoff_date=date(2026, 1, 25))

    suma_columna_interes = sum((item.interest_amount for item in result.items), Decimal("0.00"))
    final_debt = result.final_balance()

    assert suma_columna_interes == final_debt.interest
    assert final_debt.interest > Decimal("0.00")

    # La fila de cierre final tambien debe tener interest_amount > 0 (dejo de ser el
    # Decimal("0.00") hardcodeado)
    item_cierre = result.items[-1]
    assert item_cierre.balance.event_type == "LIQUIDATION_CUTOFF"
    assert item_cierre.interest_amount > Decimal("0.00")


def test_engine_evento_interest_explicito_se_suma_al_interes_causado_por_tiempo():
    # El branch event_type == "INTEREST" sigue existiendo para compatibilidad con
    # tests que lo usan explicitamente. Debe SUMARSE al interes causado por el paso
    # del tiempo en ese mismo tramo, no reemplazarlo.
    events = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        # 10 dias de mora sobre 1000.00 al 1% diario = 100.00 causados por tiempo,
        # mas 50.00 inyectados explicitamente por el evento INTEREST = 150.00 en la fila
        Event(date=date(2026, 1, 11), payload={"amount": Decimal("50.00")}, event_type="INTEREST"),
    ]
    rate = Rate.from_percent(Decimal("1.00"))
    engine = LiquidationCore(default_daily_rate=rate)

    result = engine.process(events, cutoff_date=date(2026, 1, 11))

    item_interest = result.items[-1]
    assert item_interest.balance.event_type == "INTEREST"
    assert item_interest.interest_amount == Decimal("150.00")


def test_liquidation_core_usa_la_estrategia_de_imputacion_inyectada():
    eventos = [
        Event(
            date=date(2024, 1, 1),
            payload={"amount": Decimal("100000.00")},
            event_type="INSTALLMENT",
        ),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(
        default_daily_rate=control_rate,
        estrategia_imputacion=AllocationEngine.allocate_capital_primero,
    )
    # Sembrar interes manualmente via un evento INTEREST antes del pago, para
    # distinguir capital-primero (nuevo) de interes-primero (default).
    eventos.append(
        Event(date=date(2024, 2, 1), payload={"amount": Decimal("5000.00")}, event_type="INTEREST")
    )
    eventos.append(
        Event(
            date=date(2024, 3, 1), payload={"amount": Decimal("100000.00")}, event_type="PAYMENT"
        )
    )
    resultado = engine.process(eventos, cutoff_date=date(2024, 3, 1))
    saldo = resultado.final_balance()
    assert saldo.principal == Decimal("0.00")
    assert saldo.interest == Decimal("5000.00")  # intereses NO se tocaron -- capital fue primero


def test_liquidation_core_sin_estrategia_mantiene_el_orden_por_defecto():
    eventos = [
        Event(
            date=date(2024, 1, 1),
            payload={"amount": Decimal("100000.00")},
            event_type="INSTALLMENT",
        ),
        Event(
            date=date(2024, 2, 1), payload={"amount": Decimal("5000.00")}, event_type="INTEREST"
        ),
        Event(
            date=date(2024, 3, 1), payload={"amount": Decimal("100000.00")}, event_type="PAYMENT"
        ),
    ]
    control_rate = Rate.from_percent(Decimal("0.0"))
    engine = LiquidationCore(default_daily_rate=control_rate)
    resultado = engine.process(eventos, cutoff_date=date(2024, 3, 1))
    saldo = resultado.final_balance()
    assert saldo.interest == Decimal("0.00")  # interes-primero (default): se cubre completo
    assert saldo.principal == Decimal("5000.00")
