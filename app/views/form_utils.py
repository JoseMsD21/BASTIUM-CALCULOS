"""Utilidades compartidas para formularios basados en QFormLayout (Sprint 39).

`QFormLayout.addRow(str, widget)` crea internamente un `QLabel` para la
etiqueta que NO se sincroniza con `widget.setVisible(...)`: ocultar solo el
widget deja una fila "huerfana" en el formulario (la etiqueta de texto queda
visible sin su campo editable al lado). Este bug se reprodujo de forma
sistematica en `ObligacionFormDialog`, `EventoLaboralFormDialog` y
`ParametroFormDialog` cada vez que un campo condicional se ocultaba con
`widget.setVisible(False)` suelto (ver
docs/superpowers/plans/2026-08-06-sprint39-labels-huerfanas-qformlayout.md).

`set_row_visible` centraliza el patron correcto para que no vuelva a
reaparecer al agregar un campo condicional nuevo: los dialogos deben llamarla
en vez de invocar `widget.setVisible(...)` directamente sobre un widget que
vive en un `QFormLayout`.
"""

from PySide6.QtWidgets import QFormLayout, QWidget


def set_row_visible(layout: QFormLayout, widget: QWidget, visible: bool) -> None:
    """Oculta o muestra la fila COMPLETA (etiqueta + widget) de `widget` dentro
    de `layout`.

    Usa `QFormLayout.setRowVisible()` (disponible desde Qt 6.4, y por lo
    tanto en el PySide6 6.11 que usa este proyecto) porque sincroniza
    automatica y correctamente la etiqueta con el widget en una sola
    llamada. Si en algun entorno esa API no estuviera disponible (Qt mas
    viejo), cae al patron manual de ocultar tambien el `QLabel` devuelto por
    `labelForField()`. Si el widget fue agregado con `addRow(widget)` (un
    solo argumento, sin etiqueta -- ej. un QCheckBox que ocupa toda la
    fila), `labelForField()` devuelve `None` y solo se oculta el widget, que
    es el comportamiento correcto para ese caso.
    """
    if hasattr(layout, "setRowVisible"):
        layout.setRowVisible(widget, visible)
        return
    widget.setVisible(visible)
    etiqueta = layout.labelForField(widget)
    if etiqueta is not None:
        etiqueta.setVisible(visible)
