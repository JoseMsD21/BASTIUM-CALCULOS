from datetime import date

from PySide6.QtCore import Qt

import database.session as session_module
from app.views.main_window import MainWindow
from database.models import AreaDerecho, Expediente


def test_main_window_arranca_en_el_dashboard(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.stacked_widget.currentWidget() is window.dashboard_page


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


def test_volver_regresa_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_volver_respeta_el_orden_de_visitas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._volver()

    assert window.stacked_widget.currentWidget() is window.detalle_page

    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_volver_sin_historial_no_hace_nada(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window._volver()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_ir_inicio_limpia_el_historial_y_regresa_al_dashboard(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("detalle")
    window.show_page("resultado")
    window._ir_inicio()

    assert window.stacked_widget.currentWidget() is window.dashboard_page
    assert window._history == []


def test_ir_inicio_refresca_el_dashboard(qtbot, monkeypatch):
    window = MainWindow()
    qtbot.addWidget(window)

    llamadas = []
    monkeypatch.setattr(window.dashboard_page, "refrescar", lambda: llamadas.append(1))

    window.show_page("detalle")
    window._ir_inicio()

    assert llamadas == [1]


def test_botones_navegacion_ocultos_en_pagina_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    assert window.boton_volver.isVisible() is False
    assert window.boton_inicio.isVisible() is False


def test_botones_navegacion_visibles_al_entrar_a_detalle(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")

    assert window.boton_volver.isVisible() is True
    assert window.boton_inicio.isVisible() is True


def test_click_en_volver_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")
    window.boton_volver.click()

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_click_en_inicio_regresa_al_dashboard_y_oculta_los_botones(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()

    window.show_page("detalle")
    window.show_page("resultado")
    window.boton_inicio.click()

    assert window.stacked_widget.currentWidget() is window.dashboard_page
    assert window.boton_volver.isVisible() is False
    assert window.boton_inicio.isVisible() is False


def test_boton_parametros_navega_a_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.boton_parametros.click()

    assert window.stacked_widget.currentWidget() is window.parametros_page


def test_ventana_principal_tiene_icono_de_aplicacion(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.windowIcon().isNull()


def test_botones_de_navegacion_tienen_icono(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert not window.boton_volver.icon().isNull()
    assert not window.boton_inicio.icon().isNull()
    assert not window.boton_parametros.icon().isNull()


def test_breadcrumb_muestra_expedientes_en_pagina_inicial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.etiqueta_breadcrumb.text() == "Expedientes"


def test_breadcrumb_muestra_parametros_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.etiqueta_breadcrumb.text() == "Parámetros"


def test_breadcrumb_muestra_el_radicado_al_abrir_un_expediente(qtbot):
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00123",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)

    window._abrir_detalle(expediente_id)

    assert window.etiqueta_breadcrumb.text() == "Expedientes › Radicado 2026-00123"


def test_breadcrumb_incluye_liquidacion_al_mostrar_el_resultado(qtbot):
    from decimal import Decimal

    from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
    from app.engine.liquidation.result import LiquidationResult

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00124",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)
    window._abrir_detalle(expediente_id)

    debt = PendingDebt(
        principal=Decimal("100.00"), interest=Decimal("0.00"), indexation=Decimal("0.00")
    )
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

    window._mostrar_resultado(resultado, expediente_id)

    assert window.etiqueta_breadcrumb.text() == "Expedientes › Radicado 2026-00124 › Liquidación"


def test_breadcrumb_regresa_a_expedientes_al_ir_a_inicio(qtbot):
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-00125",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    window = MainWindow()
    qtbot.addWidget(window)
    window._abrir_detalle(expediente_id)

    window._ir_inicio()

    assert window.etiqueta_breadcrumb.text() == "Expedientes"


def test_alt_izquierda_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    qtbot.keyClick(window, Qt.Key.Key_Left, Qt.KeyboardModifier.AltModifier)

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_backspace_navega_a_la_pagina_anterior(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    qtbot.keyClick(window, Qt.Key.Key_Backspace)

    assert window.stacked_widget.currentWidget() is window.dashboard_page


def test_ctrl_home_regresa_al_dashboard_y_limpia_el_historial(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    qtbot.waitExposed(window)
    window.activateWindow()
    qtbot.wait(50)

    window.show_page("detalle")
    window.show_page("resultado")
    qtbot.keyClick(window, Qt.Key.Key_Home, Qt.KeyboardModifier.ControlModifier)

    assert window.stacked_widget.currentWidget() is window.dashboard_page
    assert window._history == []


def test_boton_parametros_activo_en_la_pantalla_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")

    assert window.boton_parametros.property("class") == "primary"


def test_boton_parametros_inactivo_en_otras_pantallas(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.boton_parametros.property("class") == "secondary"

    window.show_page("detalle")

    assert window.boton_parametros.property("class") == "secondary"


def test_boton_parametros_deja_de_estar_activo_al_salir_de_parametros(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.show_page("parametros")
    assert window.boton_parametros.property("class") == "primary"

    window._ir_inicio()

    assert window.boton_parametros.property("class") == "secondary"


def test_botones_volver_e_inicio_tienen_clase_secundaria(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    assert window.boton_volver.property("class") == "secondary"
    assert window.boton_inicio.property("class") == "secondary"


def test_main_window_dashboard_ver_expedientes_navega_a_la_lista(qtbot):
    window = MainWindow()
    qtbot.addWidget(window)

    window.dashboard_page.boton_ver_expedientes.click()

    assert window.stacked_widget.currentWidget() is window.expedientes_page
