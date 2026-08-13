from app.views.configuraciones import ConfiguracionesView


def test_configuraciones_view_arranca_en_la_seccion_parametros(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.seccion_actual == "parametros"
    assert vista._stack_secciones.currentWidget() is vista.parametros_view


def test_configuraciones_view_mostrar_apariencia_cambia_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.mostrar_apariencia()

    assert vista.seccion_actual == "apariencia"
    assert vista._stack_secciones.currentWidget() is vista.apariencia_view


def test_configuraciones_view_click_en_boton_apariencia_cambia_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.boton_seccion_apariencia.click()

    assert vista.seccion_actual == "apariencia"


def test_configuraciones_view_click_en_boton_parametros_vuelve_a_parametros(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)
    vista.mostrar_apariencia()

    vista.boton_seccion_parametros.click()

    assert vista.seccion_actual == "parametros"


def test_configuraciones_view_mostrar_parametros_refresca_la_tabla(qtbot, monkeypatch):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    llamadas = []
    monkeypatch.setattr(vista.parametros_view, "refrescar", lambda: llamadas.append(1))

    vista.mostrar_parametros()

    assert llamadas == [1]


def test_configuraciones_view_emite_seccion_cambiada_al_cambiar_de_seccion(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    recibidas = []
    vista.seccion_cambiada.connect(recibidas.append)

    vista.mostrar_apariencia()
    vista.mostrar_parametros()

    assert recibidas == ["apariencia", "parametros"]


def test_configuraciones_view_boton_parametros_activo_por_defecto(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.boton_seccion_parametros.property("class") == "primary"
    assert vista.boton_seccion_apariencia.property("class") == "secondary"


def test_configuraciones_view_boton_apariencia_activo_al_seleccionarla(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    vista.mostrar_apariencia()

    assert vista.boton_seccion_apariencia.property("class") == "primary"
    assert vista.boton_seccion_parametros.property("class") == "secondary"


def test_configuraciones_view_etiqueta_seccion_actual(qtbot):
    vista = ConfiguracionesView()
    qtbot.addWidget(vista)

    assert vista.etiqueta_seccion_actual() == "Parámetros"

    vista.mostrar_apariencia()

    assert vista.etiqueta_seccion_actual() == "Apariencia"
