from datetime import date, datetime
from decimal import Decimal

import pytest
from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import QDialog, QLabel

import database.session as session_module
from app.services.areas_parametro import (
    AREA_UNIDAD_POR_CLAVE,
    deserializar_areas,
    serializar_areas,
)
from app.services.parametro_service import agregar_valor, editar_valor, historial
from app.views.configuracion import (
    HistorialParametroDialog,
    ParametroFormDialog,
    ParametrosView,
)
from database.models import AreaDerecho, ParametroLegal


def _area_unidad(clave):
    areas, unidad = AREA_UNIDAD_POR_CLAVE[clave]
    return {"areas_derecho": areas, "unidad": unidad}


def _insertar_fila_cruda(clave, areas_derecho, unidad, vigente_desde=date(2026, 1, 1)):
    """Inserta una fila de ParametroLegal sin pasar por agregar_valor() --
    unico modo de producir un `areas_derecho` corrupto (JSON invalido o
    codigo de area desconocido) hoy, ya que agregar_valor()/la migracion
    siempre pasan por serializar_areas()/AREA_UNIDAD_POR_CLAVE, controlados.
    Simula una fila legada o dañada para probar que ParametrosView no se cae
    con datos corruptos (revision de calidad, Sprint 57)."""
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave=clave,
            valor=Decimal("1.5"),
            vigente_desde=vigente_desde,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
            areas_derecho=areas_derecho,
            unidad=unidad,
        )
    )
    session.commit()
    session.close()


def test_parametros_view_lista_todas_las_claves_del_catalogo(qtbot):
    from app.services.parametro_service import CATALOGO_PARAMETROS

    vista = ParametrosView()
    qtbot.addWidget(vista)
    assert vista.tabla.rowCount() == len(CATALOGO_PARAMETROS)


def test_parametros_view_muestra_sin_dato_cuando_no_hay_valor_cargado(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "(sin dato)"


def test_parametros_view_muestra_el_valor_vigente_cuando_hay_dato(qtbot):
    agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "test",
        **_area_unidad("USURA_MULTIPLICADOR"),
    )
    vista = ParametrosView()
    qtbot.addWidget(vista)
    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"


def test_parametro_form_dialog_todos_los_campos_tienen_icono_informativo(qtbot):
    """Task 6 (sprint "Parametros: editar/eliminar de usuario"): homologa el
    icono (i) (agregar_ayuda) a TODOS los campos del formulario -- supera al
    antiguo test_parametro_form_dialog_campos_no_autoexplicativos_tienen_tooltip,
    que verificaba el tooltip directamente sobre el widget crudo (mecanismo
    que dejo de aplicar una vez que agregar_ayuda mueve el tooltip al icono,
    no al widget envuelto)."""
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    for nombre_contenedor in (
        "_contenedor_combo_clave",
        "_contenedor_campo_valor",
        "_contenedor_campo_vigente_desde",
        "_contenedor_vigente_hasta_con_ayuda",
        "_contenedor_areas_con_ayuda",
        "_contenedor_campo_unidad",
        "_contenedor_campo_usuario",
        "_contenedor_campo_motivo",
    ):
        contenedor = getattr(dialogo, nombre_contenedor)
        iconos_info = [hijo for hijo in contenedor.findChildren(QLabel) if hijo.toolTip()]
        assert len(iconos_info) == 1, f"{nombre_contenedor} deberia tener 1 icono (i)"


def test_parametros_view_columnas_tienen_tooltip(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    for indice in range(vista.tabla.columnCount()):
        item = vista.tabla.horizontalHeaderItem(indice)
        assert item.toolTip() != "", f"Columna {indice} deberia tener tooltip"


def test_parametro_form_dialog_unidad_muestra_icono_informativo(qtbot):
    """Sprint 59: 'Unidad' (Sprint 57) se pre-rellena segun la clave elegida --
    recibe el icono (i) explicito, mismo patron que 'Tasa efectiva anual' en
    ObligacionFormDialog, para dejar claro que es una propuesta editable."""
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    iconos_info = [
        hijo for hijo in dialogo._contenedor_campo_unidad.findChildren(QLabel) if hijo.toolTip()
    ]
    assert len(iconos_info) == 1


def test_parametro_form_dialog_guarda_un_valor_abierto(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")
    assert filas[0].usuario == "abogado1"


def test_parametro_form_dialog_valor_invalido_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("no-es-un-numero")
    dialogo.campo_usuario.setText("abogado1")
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_parametro_form_dialog_usuario_vacio_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_parametro_form_dialog_vigente_hasta_deshabilitado_fuera_de_tramo_cerrado(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
    assert dialogo.campo_vigente_hasta.isEnabled() is False

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.campo_vigente_hasta.isVisible() is True
    assert dialogo.campo_vigente_hasta.isEnabled() is True


def test_parametro_form_dialog_nota_vigente_hasta_cambia_segun_el_modo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert "no vence en una fecha fija" in dialogo._nota_vigente_hasta.text()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo._nota_vigente_hasta.text() == ""


def test_parametro_form_dialog_checkbox_indefinido_siempre_deshabilitado(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO"))
    assert dialogo.casilla_indefinido.isEnabled() is False
    assert dialogo.casilla_indefinido.isChecked() is False


def test_parametro_form_dialog_valor_no_finito_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("inf")
    dialogo.campo_usuario.setText("abogado1")
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_historial_parametro_dialog_lista_todas_las_filas_de_una_clave(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)
    assert dialogo.tabla.rowCount() == 2
    assert dialogo.tabla.item(0, 0).text() == "1750905.00"


def test_parametros_view_abrir_dialogo_agregar_refresca_la_tabla(qtbot, monkeypatch):
    from PySide6.QtWidgets import QDialog

    vista = ParametrosView()
    qtbot.addWidget(vista)
    monkeypatch.setattr(
        ParametroFormDialog,
        "guardar",
        lambda self: agregar_valor(
            "USURA_MULTIPLICADOR",
            Decimal("1.5"),
            date(1900, 1, 1),
            "abogado1",
            **_area_unidad("USURA_MULTIPLICADOR"),
        ),
    )

    def _exec_simulado(self):
        # Simula el flujo real (click en "Guardar" -> _guardar_y_cerrar ->
        # guardar() -> accept()) sin abrir el bucle de eventos modal.
        self.guardar()
        return QDialog.DialogCode.Accepted

    monkeypatch.setattr(ParametroFormDialog, "exec", _exec_simulado)

    vista._abrir_dialogo_agregar()

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"


def test_parametro_form_dialog_vigente_hasta_anterior_a_desde_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("IBC_CONSUMO_ORDINARIO")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.campo_vigente_desde.setDate(QDate(2026, 2, 1))
    dialogo.campo_vigente_hasta.setDate(QDate(2026, 1, 1))
    try:
        dialogo.guardar()
        raise AssertionError("se esperaba ValueError")
    except ValueError:
        pass


def test_parametro_form_dialog_boton_guardar_tiene_icono_y_clase_primaria(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    assert not dialogo.boton_guardar.icon().isNull()
    assert dialogo.boton_guardar.property("class") == "primary"


def test_parametros_view_boton_agregar_tiene_clase_primaria(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.boton_agregar.property("class") == "primary"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")


def test_escape_cierra_el_dialogo_sin_guardar(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_Escape)

    assert dialogo.result() == QDialog.DialogCode.Rejected
    assert historial("USURA_MULTIPLICADOR") == []


def test_enter_guarda_y_cierra_el_dialogo(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(
        dialogo.combo_clave.findData("USURA_MULTIPLICADOR")
    )
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.show()
    qtbot.waitExposed(dialogo)
    dialogo.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialogo, Qt.Key.Key_Return)

    assert dialogo.result() == QDialog.DialogCode.Accepted
    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("1.5")


# --- Sprint 57: casillas de area y campo de unidad ---


def test_parametro_form_dialog_preselecciona_areas_segun_la_clave(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("SMLMV"))

    areas_esperadas, unidad_esperada = AREA_UNIDAD_POR_CLAVE["SMLMV"]
    areas_esperadas_set = set(areas_esperadas)
    for area, casilla in dialogo.casillas_area.items():
        assert casilla.isChecked() == (area in areas_esperadas_set), area
    assert dialogo.campo_unidad.currentText() == unidad_esperada


def test_parametro_form_dialog_cambiar_de_clave_actualiza_la_preseleccion(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    assert dialogo.casillas_area[AreaDerecho.COMERCIAL].isChecked() is True
    assert dialogo.casillas_area[AreaDerecho.LABORAL].isChecked() is False
    assert dialogo.campo_unidad.currentText() == "veces"

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("SS_PENSION_PCT"))
    assert dialogo.casillas_area[AreaDerecho.LABORAL].isChecked() is True
    assert dialogo.casillas_area[AreaDerecho.COMERCIAL].isChecked() is False
    assert dialogo.campo_unidad.currentText() == "%"


def test_parametro_form_dialog_sin_ninguna_area_marcada_lanza_value_error(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    for casilla in dialogo.casillas_area.values():
        casilla.setChecked(False)

    with pytest.raises(ValueError):
        dialogo.guardar()


def test_parametro_form_dialog_unidad_vacia_lanza_value_error(qtbot):
    """Con el desplegable (Task 5), la unica forma de dejar la unidad vacia es
    elegir 'Otros...' y no escribir nada (o solo espacios) en el campo que se
    revela -- las opciones fijas del combo nunca estan vacias."""
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.campo_unidad.setCurrentText("Otros...")
    dialogo._campo_unidad_otros.setText("   ")

    with pytest.raises(ValueError):
        dialogo.guardar()


def test_parametro_form_dialog_guarda_areas_derecho_y_unidad_correctos(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert deserializar_areas(filas[0].areas_derecho) == [AreaDerecho.COMERCIAL]
    assert filas[0].unidad == "veces"


def test_parametro_form_dialog_permite_ajustar_areas_y_unidad_antes_de_guardar(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")

    dialogo.casillas_area[AreaDerecho.CIVIL_FAMILIA].setChecked(True)
    dialogo.campo_unidad.setCurrentText("Otros...")
    dialogo._campo_unidad_otros.setText("veces (ajustado)")

    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert set(deserializar_areas(filas[0].areas_derecho)) == {
        AreaDerecho.COMERCIAL,
        AreaDerecho.CIVIL_FAMILIA,
    }
    assert filas[0].unidad == "veces (ajustado)"


# --- Task 5: "Unidad" como QComboBox con opcion "Otros..." ---


def test_parametro_form_dialog_unidad_es_combobox_con_opciones_conocidas(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    textos = [dialogo.campo_unidad.itemText(i) for i in range(dialogo.campo_unidad.count())]
    assert textos == ["%", "COP", "meses", "índice", "veces", "puntos", "Otros..."]


def test_parametro_form_dialog_unidad_preselecciona_segun_la_clave(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)

    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("SMLMV"))
    assert dialogo.campo_unidad.currentText() == "COP"


def test_parametro_form_dialog_unidad_otros_revela_campo_de_texto(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.show()

    assert dialogo._campo_unidad_otros.isVisible() is False
    dialogo.campo_unidad.setCurrentText("Otros...")
    assert dialogo._campo_unidad_otros.isVisible() is True


def test_parametro_form_dialog_guarda_unidad_otros(qtbot):
    dialogo = ParametroFormDialog()
    qtbot.addWidget(dialogo)
    dialogo.combo_clave.setCurrentIndex(dialogo.combo_clave.findData("USURA_MULTIPLICADOR"))
    dialogo.campo_valor.setText("1.5")
    dialogo.campo_usuario.setText("abogado1")
    dialogo.campo_unidad.setCurrentText("Otros...")
    dialogo._campo_unidad_otros.setText("fracciones")

    dialogo.guardar()

    fila = historial("USURA_MULTIPLICADOR")[0]
    assert fila.unidad == "fracciones"


def test_parametros_view_tabla_tiene_columnas_area_y_unidad(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    assert vista.tabla.columnCount() == 7
    etiquetas = [vista.tabla.horizontalHeaderItem(i).text() for i in range(7)]
    assert etiquetas == [
        "Categoria",
        "Parametro",
        "Valor vigente hoy",
        "Vigente desde",
        "Vigente hasta",
        "Área",
        "Unidad",
    ]


def test_parametros_view_muestra_area_y_unidad_de_la_fila_vigente(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_smlmv = vista._claves_por_fila.index("SMLMV")
    assert vista.tabla.item(fila_smlmv, 6).text() == "COP"
    texto_area = vista.tabla.item(fila_smlmv, 5).text()
    assert "Civil" in texto_area
    assert "Laboral" in texto_area


def test_parametros_view_area_y_unidad_vacios_sin_dato_cargado(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 5).text() == ""
    assert vista.tabla.item(fila_usura, 6).text() == ""


# --- Revision de calidad Sprint 57: areas_derecho corrupto no debe tumbar
# ParametrosView.refrescar() completo, solo degradar esa celda ---


def test_parametros_view_json_corrupto_en_areas_derecho_no_rompe_el_refresco(qtbot):
    _insertar_fila_cruda(
        "USURA_MULTIPLICADOR", areas_derecho="{esto no es json valido", unidad="veces"
    )
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    vista = ParametrosView()  # no debe lanzar excepcion
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 5).text() == "?"

    # El resto de la tabla se sigue mostrando bien -- la fila corrupta no
    # afecta a las demas.
    fila_smlmv = vista._claves_por_fila.index("SMLMV")
    assert "Civil" in vista.tabla.item(fila_smlmv, 5).text()


def test_parametros_view_codigo_de_area_desconocido_no_rompe_el_refresco(qtbot):
    _insertar_fila_cruda(
        "USURA_MULTIPLICADOR", areas_derecho='["AREA_RETIRADA_DEL_ENUM"]', unidad="veces"
    )
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    vista = ParametrosView()  # no debe lanzar excepcion
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 5).text() == "?"

    fila_smlmv = vista._claves_por_fila.index("SMLMV")
    assert "Civil" in vista.tabla.item(fila_smlmv, 5).text()


# --- Sprint 58: vigencia inteligente en ParametrosView.tabla e Historial ---


def test_parametros_view_muestra_vigencia_calculada_para_anual_exacto(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_smlmv = vista._claves_por_fila.index("SMLMV")
    assert vista.tabla.item(fila_smlmv, 4).text() == "2026-12-31 (calculado)"


def test_parametros_view_muestra_indefinido_para_abierto_sin_vigente_hasta(qtbot):
    agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1990, 1, 1),
        "abogado1",
        **_area_unidad("USURA_MULTIPLICADOR"),
    )

    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 4).text() == "Indefinido"


def test_parametros_view_vigente_hasta_vacio_sin_dato_cargado(qtbot):
    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 4).text() == ""


def test_historial_parametro_dialog_muestra_vigencia_calculada_para_anual_exacto(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.item(0, 2).text() == "2026-12-31 (calculado)"


def test_historial_parametro_dialog_vigente_hasta_real_no_cambia(qtbot):
    agregar_valor(
        "IBC_CONSUMO_ORDINARIO",
        Decimal("16.24"),
        date(2026, 1, 1),
        "abogado1",
        vigente_hasta=date(2026, 1, 31),
        **_area_unidad("IBC_CONSUMO_ORDINARIO"),
    )

    dialogo = HistorialParametroDialog("IBC_CONSUMO_ORDINARIO")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.item(0, 2).text() == "2026-01-31"


# --- Sprint 58: IPC crudo (IPC_VARIACION_ANUAL) vs. calculado (IPC_INDICE_ACUMULADO) ---


def test_historial_parametro_dialog_ipc_indice_acumulado_muestra_columna_variacion(qtbot):
    agregar_valor(
        "IPC_INDICE_ACUMULADO",
        Decimal("500.00"),
        date(2025, 1, 1),
        "sistema",
        **_area_unidad("IPC_INDICE_ACUMULADO"),
    )
    agregar_valor(
        "IPC_VARIACION_ANUAL",
        Decimal("5.10"),
        date(2025, 1, 1),
        "sistema",
        **_area_unidad("IPC_VARIACION_ANUAL"),
    )

    dialogo = HistorialParametroDialog("IPC_INDICE_ACUMULADO")
    qtbot.addWidget(dialogo)

    etiquetas = [
        dialogo.tabla.horizontalHeaderItem(i).text() for i in range(dialogo.tabla.columnCount())
    ]
    assert "Variación anual (%)" in etiquetas
    columna_variacion = etiquetas.index("Variación anual (%)")
    assert dialogo.tabla.item(0, columna_variacion).text() == "5.10"


def test_historial_parametro_dialog_ipc_indice_acumulado_muestra_nota_de_formula(qtbot):
    agregar_valor(
        "IPC_INDICE_ACUMULADO",
        Decimal("500.00"),
        date(2025, 1, 1),
        "sistema",
        **_area_unidad("IPC_INDICE_ACUMULADO"),
    )

    dialogo = HistorialParametroDialog("IPC_INDICE_ACUMULADO")
    qtbot.addWidget(dialogo)

    # La nota es el segundo widget del layout (el primero es self.tabla) --
    # se verifica el texto realmente mostrado en la UI, no un atributo de
    # clase, para que este test detecte si algun dia la nota deja de
    # agregarse al layout.
    nota = dialogo.layout().itemAt(1).widget()
    assert isinstance(nota, QLabel)
    assert "índice del año anterior" in nota.text()


def test_historial_parametro_dialog_otra_clave_no_muestra_nota_de_formula(qtbot):
    """Complementa test_historial_parametro_dialog_otra_clave_no_muestra_columna_variacion:
    ademas de no tener la columna extra, el dialogo de una clave sin dato
    crudo asociado no debe agregar la nota de formula al layout (solo la
    tabla)."""
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)

    assert dialogo.layout().count() == 1


def test_historial_parametro_dialog_otra_clave_no_muestra_columna_variacion(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    dialogo = HistorialParametroDialog("SMLMV")
    qtbot.addWidget(dialogo)

    etiquetas = [
        dialogo.tabla.horizontalHeaderItem(i).text() for i in range(dialogo.tabla.columnCount())
    ]
    assert "Variación anual (%)" not in etiquetas


# --- Sprint 58: enlace "Ver historial" en ParametrosView.tabla ---


def test_parametros_view_muestra_enlace_ver_historial_con_mas_de_una_fila(qtbot):
    agregar_valor(
        "SMLMV", Decimal("1423500.00"), date(2025, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )
    agregar_valor(
        "SMLMV", Decimal("1750905.00"), date(2026, 1, 1), "abogado1", **_area_unidad("SMLMV")
    )

    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_smlmv = vista._claves_por_fila.index("SMLMV")
    texto = vista.tabla.item(fila_smlmv, 2).text()
    assert "1750905.00" in texto
    assert "Ver 2 valores históricos" in texto


def test_parametros_view_sin_enlace_ver_historial_con_una_sola_fila(qtbot):
    agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1990, 1, 1),
        "abogado1",
        **_area_unidad("USURA_MULTIPLICADOR"),
    )

    vista = ParametrosView()
    qtbot.addWidget(vista)

    fila_usura = vista._claves_por_fila.index("USURA_MULTIPLICADOR")
    assert vista.tabla.item(fila_usura, 2).text() == "1.5"


# --- Task 7: ParametroFormDialog en modo edicion (parametro_id) ---


def test_parametro_form_dialog_modo_edicion_precarga_los_campos(qtbot):
    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
        motivo="motivo original",
    )

    dialogo = ParametroFormDialog(parametro_id=fila.id)
    qtbot.addWidget(dialogo)

    assert dialogo.windowTitle() == "Editar valor de parametro"
    assert dialogo.combo_clave.currentData() == "USURA_MULTIPLICADOR"
    assert dialogo.combo_clave.isEnabled() is False
    assert dialogo.campo_valor.text() == "1.5"
    assert dialogo.campo_usuario.text() == "abogado1"
    assert dialogo.campo_motivo.text() == "motivo original"
    assert dialogo.casillas_area[AreaDerecho.COMERCIAL].isChecked() is True


def test_parametro_form_dialog_modo_edicion_guarda_actualiza_no_crea(qtbot):
    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )

    dialogo = ParametroFormDialog(parametro_id=fila.id)
    qtbot.addWidget(dialogo)
    dialogo.campo_valor.setText("9.9")
    dialogo.guardar()

    filas = historial("USURA_MULTIPLICADOR")
    assert len(filas) == 1
    assert filas[0].valor == Decimal("9.9")


# --- Task 8: Editar/Eliminar por fila en HistorialParametroDialog ---


def test_historial_parametro_dialog_fila_de_usuario_tiene_botones(qtbot):
    agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.cellWidget(0, 5) is not None  # Editar
    assert dialogo.tabla.cellWidget(0, 6) is not None  # Eliminar


def test_historial_parametro_dialog_fila_de_sistema_no_tiene_botones(qtbot):
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=Decimal("1.5"),
            vigente_desde=date(1900, 1, 1),
            usuario="sistema",
            creado_en=datetime.now(),
            areas_derecho=serializar_areas([AreaDerecho.COMERCIAL]),
            unidad="veces",
            creado_por_sistema=True,
        )
    )
    session.commit()
    session.close()

    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    assert dialogo.tabla.cellWidget(0, 5) is None
    assert dialogo.tabla.cellWidget(0, 6) is None


def test_historial_parametro_dialog_eliminar_borra_y_refresca(qtbot, monkeypatch):
    from PySide6.QtWidgets import QMessageBox

    fila = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(1900, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    monkeypatch.setattr(
        QMessageBox, "question", lambda *a, **k: QMessageBox.StandardButton.Yes
    )
    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)

    dialogo._eliminar_valor(fila.id)

    assert dialogo.tabla.rowCount() == 0
    assert historial("USURA_MULTIPLICADOR") == []


def test_historial_parametro_dialog_reordenar_filas_no_deja_botones_fantasma(qtbot):
    """Regresion (Task 8): historial() ordena por vigente_desde descendente,
    asi que editar la fecha de una fila de usuario puede cambiarle el indice
    de fila relativo a una fila de sistema entre dos llamadas a _refrescar().
    QTableWidget.setRowCount(N) con el mismo N NO limpia los cellWidget de
    filas que conservan su indice -- sin removeCellWidget() explicito en
    _refrescar(), la fila de sistema que hereda el indice 0 (antes ocupado
    por la fila de usuario con botones) quedaria mostrando esos botones
    "fantasma"."""
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=Decimal("2.0"),
            vigente_desde=date(2020, 1, 1),
            usuario="sistema",
            creado_en=datetime.now(),
            areas_derecho=serializar_areas([AreaDerecho.COMERCIAL]),
            unidad="veces",
            creado_por_sistema=True,
        )
    )
    session.commit()
    session.close()

    fila_usuario = agregar_valor(
        "USURA_MULTIPLICADOR",
        Decimal("1.5"),
        date(2025, 1, 1),
        "abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )

    dialogo = HistorialParametroDialog("USURA_MULTIPLICADOR")
    qtbot.addWidget(dialogo)
    # Orden inicial (vigente_desde desc): fila_usuario (2025) en indice 0 con
    # botones, sistema (2020) en indice 1 sin botones.
    assert dialogo.tabla.cellWidget(0, 5) is not None
    assert dialogo.tabla.cellWidget(1, 5) is None

    # Editar la fila de usuario para que su vigente_desde quede ANTES que la
    # de sistema -- invierte el orden: sistema pasa a indice 0.
    editar_valor(
        fila_usuario.id,
        valor=Decimal("1.5"),
        vigente_desde=date(2019, 1, 1),
        usuario="abogado1",
        areas_derecho=[AreaDerecho.COMERCIAL],
        unidad="veces",
    )
    dialogo._refrescar()

    assert dialogo.tabla.item(0, 0).text() == "2.0"  # ahora es la fila de sistema
    assert dialogo.tabla.cellWidget(0, 5) is None
    assert dialogo.tabla.cellWidget(0, 6) is None
    assert dialogo.tabla.cellWidget(1, 5) is not None
    assert dialogo.tabla.cellWidget(1, 6) is not None
