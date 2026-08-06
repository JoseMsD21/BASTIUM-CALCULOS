from datetime import date
from decimal import Decimal

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.views.expedientes import ExpedienteFormDialog, ExpedientesListView
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion


def _sesion_en_memoria(monkeypatch):
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))


def test_lista_muestra_expedientes_existentes(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-001",
            demandante="Ana",
            demandado="Luis",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-001"


def test_dialogo_crea_expediente_civil_familia(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-002")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    expediente_id = dialog.guardar()

    session = session_module.get_session()
    guardado = session.get(Expediente, expediente_id)
    assert guardado.radicado == "2026-002"
    assert guardado.area_derecho == AreaDerecho.CIVIL_FAMILIA
    session.close()


def test_dialogo_habilita_todas_las_areas(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    modelo = dialog.combo_area.model()
    assert modelo.rowCount() == len(AREAS_DERECHO)
    # Las 5 areas del derecho estan habilitadas desde el Sprint 3 (Laboral
    # fue la ultima en habilitarse) -- ver Pendientes.md.
    for indice in range(modelo.rowCount()):
        assert modelo.item(indice).isEnabled() is True


def test_dialogo_edita_expediente_existente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-003",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 5",
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    expediente_a_editar = session.get(Expediente, expediente_id)

    dialog = ExpedienteFormDialog(expediente=expediente_a_editar)
    qtbot.addWidget(dialog)
    session.close()

    assert dialog.windowTitle() == "Editar expediente"
    assert dialog.campo_radicado.text() == "2026-003"
    assert dialog.campo_juzgado.text() == "Juzgado 5"

    dialog.campo_demandante.setText("Ana Maria")
    resultado_id = dialog.guardar()

    assert resultado_id == expediente_id

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    actualizado = session.get(Expediente, expediente_id)
    assert actualizado.demandante == "Ana Maria"
    assert actualizado.radicado == "2026-003"
    session.close()


def test_tabla_tiene_columnas_de_editar_y_eliminar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-005",
            demandante="Pedro",
            demandado="Rosa",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    assert view.tabla.columnCount() == 6
    assert view.tabla.cellWidget(0, 4) is not None
    assert view.tabla.cellWidget(0, 5) is not None


def test_boton_editar_abre_dialogo_con_el_expediente_de_la_fila(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-004",
            demandante="Carlos",
            demandado="Maria",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    dialogos_creados = []

    class _DialogStub:
        def __init__(self, parent, expediente):
            dialogos_creados.append(expediente.radicado)

        def exec(self):
            return False

    monkeypatch.setattr("app.views.expedientes.ExpedienteFormDialog", _DialogStub)

    view._editar_expediente(view._expediente_ids_por_fila[0])

    assert dialogos_creados == ["2026-004"]


def test_eliminar_expediente_confirmado_borra_el_registro(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-006",
        demandante="Sofia",
        demandado="Diego",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-006", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    session.close()
    assert view.tabla.rowCount() == 0


def test_eliminar_expediente_con_radicado_incorrecto_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-007",
        demandante="Laura",
        demandado="Mario",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("radicado-equivocado", True),
    )
    monkeypatch.setattr("app.views.expedientes.QMessageBox.warning", lambda *args, **kwargs: None)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_cancelado_en_primer_dialogo_no_borra(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-008",
        demandante="Elena",
        demandado="Pablo",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.No,
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 1
    session.close()


def test_eliminar_expediente_borra_en_cascada_sus_obligaciones(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-009",
        demandante="Ines",
        demandado="Tomas",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.commit()

    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital",
            categoria="CAPITAL",
            fecha_origen=date(2026, 1, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-009", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view._eliminar_expediente(expediente_id)

    session = session_module.get_session()
    assert session.query(Expediente).count() == 0
    assert session.query(Obligacion).count() == 0
    session.close()


def test_boton_guardar_del_formulario_tiene_icono_y_clase_primaria(qtbot):
    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert not dialog.boton_guardar.icon().isNull()
    assert dialog.boton_guardar.property("class") == "primary"


def test_boton_nuevo_expediente_tiene_clase_primaria(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.boton_nuevo.property("class") == "primary"


def test_boton_eliminar_de_cada_fila_tiene_icono_y_clase_destructiva(qtbot, monkeypatch):
    from app.views.expedientes import ExpedientesListView

    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-099",
            demandante="Ana",
            demandado="Luis",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    boton_eliminar = view.tabla.cellWidget(0, 5)
    assert not boton_eliminar.icon().isNull()
    assert boton_eliminar.property("class") == "destructive"


def test_busqueda_filtra_por_radicado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-100",
                demandante="Ana",
                demandado="Luis",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-200",
                demandante="Carlos",
                demandado="Maria",
                area_derecho=AreaDerecho.COMERCIAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    assert view.tabla.rowCount() == 2

    view.campo_busqueda.setText("2026-100")

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-100"


def test_busqueda_filtra_por_demandante_o_demandado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-101",
                demandante="Fernanda Gomez",
                demandado="Luis",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-102",
                demandante="Carlos",
                demandado="Rodrigo Gomez",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-103",
                demandante="Sofia",
                demandado="Pedro",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("Gomez")

    assert view.tabla.rowCount() == 2


def test_busqueda_es_insensible_a_mayusculas_y_a_espacios_al_inicio_o_final(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-104",
            demandante="Valentina",
            demandado="Camilo",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("  VALENTINA  ")

    assert view.tabla.rowCount() == 1


def test_filtro_area_muestra_solo_expedientes_del_area_seleccionada(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-300",
                demandante="A",
                demandado="B",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-301",
                demandante="C",
                demandado="D",
                area_derecho=AreaDerecho.LABORAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    assert view.tabla.rowCount() == 2

    indice_laboral = view.combo_filtro_area.findData("LABORAL")
    view.combo_filtro_area.setCurrentIndex(indice_laboral)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-301"


def test_combo_filtro_area_incluye_la_opcion_todas_las_areas_por_defecto(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.combo_filtro_area.currentData() == ""
    assert view.combo_filtro_area.count() == len(AREAS_DERECHO) + 1


def test_busqueda_y_filtro_de_area_se_combinan(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add_all(
        [
            Expediente(
                radicado="2026-400",
                demandante="Pablo Ruiz",
                demandado="X",
                area_derecho=AreaDerecho.CIVIL_FAMILIA,
                fecha_corte_default=date(2026, 1, 1),
            ),
            Expediente(
                radicado="2026-401",
                demandante="Pablo Ruiz",
                demandado="Y",
                area_derecho=AreaDerecho.LABORAL,
                fecha_corte_default=date(2026, 1, 1),
            ),
        ]
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()

    view.campo_busqueda.setText("Pablo Ruiz")
    indice_laboral = view.combo_filtro_area.findData("LABORAL")
    view.combo_filtro_area.setCurrentIndex(indice_laboral)

    assert view.tabla.rowCount() == 1
    assert view.tabla.item(0, 0).text() == "2026-401"


def test_tabla_de_expedientes_tiene_ordenamiento_de_columnas_habilitado(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)

    assert view.tabla.isSortingEnabled() is True


def test_doble_clic_despues_de_ordenar_por_columna_abre_el_expediente_correcto(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente_zulema = Expediente(
        radicado="2026-900",
        demandante="Zulema",
        demandado="Ana",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    expediente_andres = Expediente(
        radicado="2026-901",
        demandante="Andres",
        demandado="Beto",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add_all([expediente_zulema, expediente_andres])
    session.commit()
    id_andres = expediente_andres.id
    session.close()

    abiertos = []
    view = ExpedientesListView(on_expediente_abierto=abiertos.append)
    qtbot.addWidget(view)
    view.refrescar()

    # Orden de insercion original: fila 0 = "Zulema" (2026-900), fila 1 = "Andres" (2026-901).
    assert view.tabla.item(0, 1).text() == "Zulema"

    # Se ordena por la columna "Demandante" (columna 1) ascendente: invierte el orden.
    view.tabla.sortItems(1, Qt.SortOrder.AscendingOrder)
    assert view.tabla.item(0, 1).text() == "Andres"

    view._abrir_seleccionado(0, 0)

    assert abiertos == [id_andres]


def test_eliminar_expediente_sigue_borrando_el_correcto_despues_de_ordenar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    expediente_z = Expediente(
        radicado="2026-902",
        demandante="Zulema",
        demandado="Ana",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    expediente_a = Expediente(
        radicado="2026-903",
        demandante="Andres",
        demandado="Beto",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add_all([expediente_z, expediente_a])
    session.commit()
    id_andres = expediente_a.id
    session.close()

    monkeypatch.setattr(
        "app.views.expedientes.QMessageBox.question",
        lambda *args, **kwargs: QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "app.views.expedientes.QInputDialog.getText",
        lambda *args, **kwargs: ("2026-903", True),
    )

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.refrescar()
    view.tabla.sortItems(1, Qt.SortOrder.AscendingOrder)

    boton_eliminar_fila_0 = view.tabla.cellWidget(0, 5)
    boton_eliminar_fila_0.click()

    session = session_module.get_session()
    assert session.get(Expediente, id_andres) is None
    session.close()


def test_base_de_datos_vacia_muestra_estado_vacio_con_boton_crear_expediente(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()

    assert view.tabla.isVisible() is False
    assert view.widget_estado_vacio.isVisible() is True
    assert "no hay expedientes" in view.etiqueta_estado_vacio.text().lower()
    assert view.boton_accion_estado_vacio.isVisible() is True
    assert view.boton_accion_estado_vacio.text() == "Crear expediente"


def test_estado_vacio_se_oculta_y_la_tabla_se_muestra_cuando_hay_resultados(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-960",
            demandante="Ines",
            demandado="Tomas",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.refrescar()

    assert view.tabla.isVisible() is True
    assert view.widget_estado_vacio.isVisible() is False


def test_filtro_sin_resultados_muestra_estado_vacio_con_boton_limpiar_filtros(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-950",
            demandante="Fernanda",
            demandado="Ricardo",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.refrescar()
    assert view.tabla.isVisible() is True

    view.campo_busqueda.setText("no-existe-este-radicado")

    assert view.tabla.isVisible() is False
    assert view.widget_estado_vacio.isVisible() is True
    assert "coincide" in view.etiqueta_estado_vacio.text().lower()
    assert view.boton_accion_estado_vacio.text() == "Limpiar filtros"


def test_boton_limpiar_filtros_del_estado_vacio_restaura_la_lista_completa(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)
    session = session_module.get_session()
    session.add(
        Expediente(
            radicado="2026-951",
            demandante="Gustavo",
            demandado="Helena",
            area_derecho=AreaDerecho.CIVIL_FAMILIA,
            fecha_corte_default=date(2026, 1, 1),
        )
    )
    session.commit()
    session.close()

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()
    view.campo_busqueda.setText("no-existe-este-radicado")
    assert view.tabla.rowCount() == 0

    view.boton_accion_estado_vacio.click()

    assert view.campo_busqueda.text() == ""
    assert view.combo_filtro_area.currentData() == ""
    assert view.tabla.rowCount() == 1
    assert view.tabla.isVisible() is True


def test_boton_crear_expediente_del_estado_vacio_abre_el_dialogo_de_nuevo_expediente(
    qtbot, monkeypatch
):
    _sesion_en_memoria(monkeypatch)

    dialogos_creados = []

    class _DialogStub:
        def __init__(self, parent):
            dialogos_creados.append(1)

        def exec(self):
            return False

    monkeypatch.setattr("app.views.expedientes.ExpedienteFormDialog", _DialogStub)

    view = ExpedientesListView()
    qtbot.addWidget(view)
    view.show()

    view.boton_accion_estado_vacio.click()

    assert dialogos_creados == [1]


def test_campo_radicado_tiene_tooltip_explicativo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert dialog.campo_radicado.toolTip() != ""


def test_campo_fecha_corte_tiene_tooltip_explicativo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)

    assert dialog.campo_fecha_corte.toolTip() != ""


def test_campo_radicado_vacio_se_marca_invalido_en_tiempo_real(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.campo_radicado.setText("2026-099")
    assert dialog.campo_radicado.property("class") != "invalid"

    dialog.campo_radicado.setText("   ")
    assert dialog.campo_radicado.property("class") == "invalid"

    dialog.campo_radicado.setText("2026-100")
    assert dialog.campo_radicado.property("class") != "invalid"


def test_ctrl_s_guarda_y_cierra_el_dialogo(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-050")
    dialog.campo_demandante.setText("Ana")
    dialog.campo_demandado.setText("Luis")
    dialog.campo_fecha_corte.setDate(date(2026, 1, 1))

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_S, Qt.KeyboardModifier.ControlModifier)

    assert dialog.result() == QDialog.DialogCode.Accepted
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-050").one_or_none()
    assert guardado is not None
    session.close()


def test_escape_cierra_el_dialogo_sin_guardar(qtbot, monkeypatch):
    _sesion_en_memoria(monkeypatch)

    dialog = ExpedienteFormDialog()
    qtbot.addWidget(dialog)
    dialog.campo_radicado.setText("2026-051")

    dialog.show()
    qtbot.waitExposed(dialog)
    dialog.activateWindow()
    qtbot.wait(50)

    qtbot.keyClick(dialog, Qt.Key.Key_Escape)

    assert dialog.result() == QDialog.DialogCode.Rejected
    session = session_module.get_session()
    guardado = session.query(Expediente).filter_by(radicado="2026-051").one_or_none()
    assert guardado is None
    session.close()
