from app.views.main_window import MainWindow


def test_main_window_arranca_en_la_lista_de_expedientes(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.stacked_widget.currentWidget() is window.expedientes_page


def test_main_window_navega_a_la_pagina_de_detalle(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")

    assert window.stacked_widget.currentWidget() is window.detalle_page


def test_main_window_navega_a_la_pagina_de_resultado(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("resultado")

    assert window.stacked_widget.currentWidget() is window.resultado_page


def test_main_window_pasa_expediente_id_a_la_pagina_de_resultado(qtbot):
    from datetime import date
    from decimal import Decimal

    from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
    from app.engine.liquidation.result import LiquidationResult

    window = MainWindow()
    qtbot.addWidget(window)

    debt = PendingDebt(principal=Decimal("100.00"), interest=Decimal("0.00"), indexation=Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="LIQUIDATION_CUTOFF")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Prueba",
        capital_base=Decimal("100.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    resultado = LiquidationResult(items=[item])

    window._mostrar_resultado(resultado, expediente_id=42)

    assert window.resultado_page._expediente_id == 42
