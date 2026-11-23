"""Sprint 106: formato de fecha unico dia/mes/año y widgets de fecha
estructurados (fechas anuales fijas Dia/Mes, fecha opcional)."""

from datetime import date

import pytest
from PySide6.QtWidgets import QDateEdit

from app.views.fecha_widgets import (
    FORMATO_FECHA_UI,
    CampoFechaOpcional,
    SelectorFechasAnuales,
    formatear_fecha,
)


def test_formato_fecha_ui_es_dia_mes_anio():
    assert FORMATO_FECHA_UI == "dd/MM/yyyy"


def test_formatear_fecha_dia_mes_anio_y_none():
    assert formatear_fecha(date(2026, 3, 5)) == "05/03/2026"
    assert formatear_fecha(None) == "—"


# --- SelectorFechasAnuales -------------------------------------------------


def test_selector_agrega_fechas_y_las_expone_en_formato_de_almacenamiento_mm_dd(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.agregar_fecha(15, 6)
    selector.agregar_fecha(23, 3)

    # El formato guardado no cambia (lo consume el motor de recurrencia, Sprint 73).
    assert selector.fechas_mm_dd() == ["06-15", "03-23"]


def test_selector_muestra_cada_fecha_como_dia_mes(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.agregar_fecha(5, 12)

    assert selector.lista.item(0).text() == "05/12 (5 de diciembre)"


def test_selector_ignora_fecha_duplicada(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.agregar_fecha(15, 6)
    selector.agregar_fecha(15, 6)

    assert selector.fechas_mm_dd() == ["06-15"]


def test_selector_rechaza_dia_inexistente_en_el_mes(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    with pytest.raises(ValueError):
        selector.agregar_fecha(31, 4)
    with pytest.raises(ValueError):
        selector.agregar_fecha(30, 2)


def test_selector_acepta_29_de_febrero(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.agregar_fecha(29, 2)

    assert selector.fechas_mm_dd() == ["02-29"]


def test_selector_topa_el_dia_maximo_segun_el_mes_elegido(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.combo_mes.setCurrentIndex(selector.combo_mes.findData(2))
    assert selector.spin_dia.maximum() == 29
    selector.combo_mes.setCurrentIndex(selector.combo_mes.findData(4))
    assert selector.spin_dia.maximum() == 30
    selector.combo_mes.setCurrentIndex(selector.combo_mes.findData(12))
    assert selector.spin_dia.maximum() == 31


def test_selector_boton_agregar_usa_dia_y_mes_elegidos(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)

    selector.combo_mes.setCurrentIndex(selector.combo_mes.findData(12))
    selector.spin_dia.setValue(15)
    selector.boton_agregar.click()

    assert selector.fechas_mm_dd() == ["12-15"]


def test_selector_boton_quitar_elimina_la_fecha_seleccionada(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)
    selector.agregar_fecha(15, 6)
    selector.agregar_fecha(15, 12)

    selector.lista.setCurrentRow(0)
    selector.boton_quitar.click()

    assert selector.fechas_mm_dd() == ["12-15"]


def test_selector_establecer_fechas_reemplaza_la_lista(qtbot):
    selector = SelectorFechasAnuales()
    qtbot.addWidget(selector)
    selector.agregar_fecha(1, 1)

    selector.establecer_fechas_mm_dd(["06-15", "12-15"])

    assert selector.fechas_mm_dd() == ["06-15", "12-15"]
    assert selector.lista.item(1).text().startswith("15/12")


# --- CampoFechaOpcional ----------------------------------------------------


def test_campo_fecha_opcional_vacio_por_defecto(qtbot):
    campo = CampoFechaOpcional()
    qtbot.addWidget(campo)

    assert campo.fecha() is None
    assert campo.campo_fecha.isEnabled() is False


def test_campo_fecha_opcional_roundtrip(qtbot):
    campo = CampoFechaOpcional()
    qtbot.addWidget(campo)

    campo.establecer_fecha(date(2020, 3, 15))
    assert campo.fecha() == date(2020, 3, 15)
    assert campo.check.isChecked() is True

    campo.establecer_fecha(None)
    assert campo.fecha() is None


def test_campo_fecha_opcional_usa_formato_dia_mes_anio(qtbot):
    campo = CampoFechaOpcional()
    qtbot.addWidget(campo)

    assert campo.campo_fecha.displayFormat() == "dd/MM/yyyy"


# --- Formato unico en todos los formularios con fecha ----------------------


def _formatos_de_fecha(widget) -> set[str]:
    return {campo.displayFormat() for campo in widget.findChildren(QDateEdit)}


def test_todos_los_formularios_con_fecha_usan_dia_mes_anio(qtbot, monkeypatch):
    """Definicion de Hecho del Sprint 106: todo campo de fecha visible muestra
    y acepta dia/mes/año, sin depender del formato regional del sistema."""
    from app.views.abonos import AbonoFormDialog
    from app.views.configuracion import ParametroFormDialog
    from app.views.descuentos_laborales import DescuentoLaboralFormDialog
    from app.views.eventos_laborales import EventoLaboralFormDialog
    from app.views.expediente_detalle import ExpedienteDetallePage
    from app.views.expedientes import ExpedienteFormDialog
    from app.views.horas_extra_laborales import HoraExtraLaboralFormDialog
    from app.views.obligaciones import ObligacionFormDialog
    from tests.views.conftest import crear_sesion_en_memoria

    crear_sesion_en_memoria(monkeypatch)

    widgets = [
        ExpedienteFormDialog(),
        ExpedienteDetallePage(),
        AbonoFormDialog(obligacion_id=1),
        EventoLaboralFormDialog(obligacion_id=1),
        DescuentoLaboralFormDialog(obligacion_id=1),
        HoraExtraLaboralFormDialog(obligacion_id=1),
        ParametroFormDialog(),
    ]
    for area in ("CIVIL_FAMILIA", "COMERCIAL", "LABORAL", "TRIBUTARIO"):
        widgets.append(ObligacionFormDialog(expediente_id=1, area=area))

    for widget in widgets:
        qtbot.addWidget(widget)
        formatos = _formatos_de_fecha(widget)
        assert formatos, f"{type(widget).__name__} no tiene QDateEdit"
        assert formatos == {"dd/MM/yyyy"}, f"{type(widget).__name__}: {formatos}"


def test_ninguna_vista_construye_qdateedit_sin_pasar_por_crear_campo_fecha():
    """Guardia estatica (Sprint 106): todo QDateEdit de app/views/ se crea con
    `crear_campo_fecha` (que fija dd/MM/yyyy) -- un QDateEdit nuevo creado a
    mano volveria a depender del formato regional del sistema operativo."""
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[2] / "app" / "views"
    infractores = [
        archivo.name
        for archivo in raiz.glob("*.py")
        if archivo.name != "fecha_widgets.py"
        and "QDateEdit(" in archivo.read_text(encoding="utf-8")
    ]
    assert not infractores, f"Usar crear_campo_fecha() en vez de QDateEdit(): {infractores}"
