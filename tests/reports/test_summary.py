from datetime import date
from decimal import Decimal

from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder


def test_summary_builder_aggregates_totals_correctly():
    debt = PendingDebt(Decimal("1000000"), Decimal("250000"), Decimal("0"))
    rb = RunningBalance(date(2026, 4, 15), debt, "PAYMENT")
    
    item = LiquidationItem(
        date=date(2026, 4, 15),
        concept="Abono",
        capital_base=Decimal("1000000"),
        interest_rate=Decimal("1.5"),
        interest_amount=Decimal("10000"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("500000"),
        balance=rb
    )
    
    result = LiquidationResult([item])
    builder = ReportSummaryBuilder()
    summary = builder.build_summary(result)
    
    assert summary["total_abonos"] == "$500,000.00"
    assert summary["saldo_final_capital"] == "$1,000,000.00"
    assert summary["saldo_final_intereses"] == "$250,000.00"
    assert summary["gran_total_adeudado"] == "$1,250,000.00"


def test_summary_incluye_saldo_a_favor_cuando_hay_sobrepago():
    # Sprint 46: el saldo a favor de un sobrepago (Sprint 23, LiquidationItem.saldo_a_favor)
    # debe llegar al resumen ejecutivo -- antes de este sprint el dato se calculaba
    # correctamente pero nunca se mostraba en ningun reporte.
    debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
    rb = RunningBalance(date(2026, 1, 10), debt, "PAYMENT")
    item = LiquidationItem(
        date=date(2026, 1, 10),
        concept="Pago",
        capital_base=Decimal("7000000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("7000000.00"),
        balance=rb,
        saldo_a_favor=Decimal("3000000.00"),
    )
    result = LiquidationResult([item])
    summary = ReportSummaryBuilder().build_summary(result)

    assert summary["saldo_a_favor"] == "$3,000,000.00"


def test_summary_omite_saldo_a_favor_cuando_no_hay_sobrepago():
    # La clave debe estar completamente ausente del diccionario (no "$0.00") para
    # que cada consumidor (pdf.py/word.py/liquidaciones.py) pueda decidir con un
    # simple `if "saldo_a_favor" in summary:` en vez de comparar contra cero.
    debt = PendingDebt(Decimal("1000000"), Decimal("250000"), Decimal("0"))
    rb = RunningBalance(date(2026, 4, 15), debt, "PAYMENT")
    item = LiquidationItem(
        date=date(2026, 4, 15),
        concept="Abono",
        capital_base=Decimal("1000000"),
        interest_rate=Decimal("1.5"),
        interest_amount=Decimal("10000"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("500000"),
        balance=rb,
    )
    result = LiquidationResult([item])
    summary = ReportSummaryBuilder().build_summary(result)

    assert "saldo_a_favor" not in summary


def test_build_renta_liquida_retorna_none_sin_renta_liquida():
    debt = PendingDebt(Decimal("0"), Decimal("0"), Decimal("0"))
    rb = RunningBalance(date(2026, 1, 1), debt, "IMPUESTO_A_CARGO")
    item = LiquidationItem(
        date=date(2026, 1, 1), concept="x", capital_base=Decimal("0"), interest_rate=Decimal("0"),
        interest_amount=Decimal("0"), indexation_amount=Decimal("0"), payment_amount=Decimal("0"),
        balance=rb,
    )
    result = LiquidationResult([item])
    builder = ReportSummaryBuilder()

    assert builder.build_renta_liquida(result) is None


def test_build_renta_liquida_formatea_los_5_campos():
    from app.engine.tax.renta_liquida import RentaLiquidaGravableResult

    renta = RentaLiquidaGravableResult(
        ingresos_netos=Decimal("100000000.00"),
        renta_bruta=Decimal("60000000.00"),
        renta_liquida=Decimal("40000000.00"),
        hubo_perdida_liquida=False,
        renta_liquida_gravable=Decimal("35000000.00"),
    )
    result = LiquidationResult(items=[], renta_liquida=renta)
    builder = ReportSummaryBuilder()

    datos = builder.build_renta_liquida(result)

    assert datos["ingresos_netos"] == "$100,000,000.00"
    assert datos["renta_bruta"] == "$60,000,000.00"
    assert datos["renta_liquida"] == "$40,000,000.00"
    assert datos["hubo_perdida_liquida"] == "No"
    assert datos["renta_liquida_gravable"] == "$35,000,000.00"