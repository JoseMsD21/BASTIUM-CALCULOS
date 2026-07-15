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
