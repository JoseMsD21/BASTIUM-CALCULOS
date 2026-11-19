"""PoliticaCausacion: la legada no cambia; la exacta reproduce `capital x tasa x dias / base`."""

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

import pytest

from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.politica import PoliticaCausacion
from app.engine.temporal.schedulers.base import Event

TASA_DIARIA = Decimal("0.06") / Decimal("365")
INICIO, CORTE = date(2024, 1, 1), date(2025, 1, 1)  # 366 dias (2024 bisiesto)


def _liquidar(capital: str, politica: PoliticaCausacion, corte: date = CORTE):
    proveedor = MemoryRateProvider()
    proveedor.add_rate_period(
        date(2000, 1, 1), date(2100, 12, 31), Rate(TASA_DIARIA), "Art. 1617 CC"
    )
    nucleo = LiquidationCore(rate_provider=proveedor, politica_causacion=politica)
    eventos = [
        Event(
            date=INICIO, event_type="INSTALLMENT", payload={"amount": capital, "label": "capital"}
        )
    ]
    return nucleo.process(eventos, corte)


def _manual(capital: str, dias: int) -> Decimal:
    return (Decimal(capital) * Decimal("0.06") * dias / Decimal("365")).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )


@pytest.mark.parametrize("capital", ["1000000.00", "10000000.00", "37845123.00", "250000000.00"])
def test_exacta_reproduce_el_calculo_manual_al_centavo(capital):
    resultado = _liquidar(capital, PoliticaCausacion.EXACTA_POR_PERIODO)
    assert resultado.total_interest_accrued() == _manual(capital, 366)


def test_legada_conserva_el_sesgo_historico_medido_en_la_auditoria():
    # Valores medidos ANTES del cambio (2026-11-12) con el motor sin modificar.
    assert _liquidar(
        "10000000.00", PoliticaCausacion.LEGADA_DIARIA_REDONDEADA
    ).total_interest_accrued() == Decimal("601645.44")
    assert _liquidar(
        "1000000.00", PoliticaCausacion.LEGADA_DIARIA_REDONDEADA
    ).total_interest_accrued() == Decimal("60163.08")


def test_el_default_es_la_politica_legada():
    por_defecto = LiquidationCore(rate_provider=MemoryRateProvider())
    assert por_defecto._politica_causacion is PoliticaCausacion.LEGADA_DIARIA_REDONDEADA


def test_exacta_con_dos_tramos_y_un_abono_redondea_por_tramo():
    proveedor = MemoryRateProvider()
    proveedor.add_rate_period(
        date(2000, 1, 1), date(2100, 12, 31), Rate(TASA_DIARIA), "Art. 1617 CC"
    )
    nucleo = LiquidationCore(
        rate_provider=proveedor, politica_causacion=PoliticaCausacion.EXACTA_POR_PERIODO
    )
    eventos = [
        Event(
            date=date(2024, 1, 1),
            event_type="INSTALLMENT",
            payload={"amount": "10000000.00", "label": "capital"},
        ),
        Event(
            date=date(2024, 7, 1),
            event_type="PAYMENT",
            payload={"amount": "100000.00", "label": "abono"},
        ),
    ]
    r = nucleo.process(eventos, date(2025, 1, 1))
    tramo1 = _manual("10000000.00", 182)  # 2024-01-02 .. 2024-07-01
    assert r.items[1].interest_amount == tramo1
    # El abono (100.000) cubre intereses primero; el saldo de intereses es tramo1 - 100.000.
    assert r.items[1].balance.debt.interest == tramo1 - Decimal("100000.00")
    assert r.items[1].balance.debt.principal == Decimal("10000000.00")


def test_resultado_exacto_identico_en_otro_hilo_con_otro_redondeo_global():
    import decimal
    import threading

    salida = {}

    def trabajo():
        decimal.getcontext().rounding = decimal.ROUND_DOWN  # contexto hostil del hilo
        decimal.getcontext().prec = 9
        salida["v"] = _liquidar(
            "10000000.00", PoliticaCausacion.EXACTA_POR_PERIODO
        ).total_interest_accrued()

    hilo = threading.Thread(target=trabajo)
    hilo.start()
    hilo.join()
    assert salida["v"] == _manual("10000000.00", 366)
