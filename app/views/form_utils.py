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

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QFormLayout, QHBoxLayout, QLabel, QWidget

from app.views.icons import icon


def guardar_o_actualizar(session, modelo_cls, id_existente: int | None, **campos) -> int:
    """Actualiza los atributos de la fila existente (`id_existente`) en vez de
    borrarla y crear una nueva -- editar sin borrar y recrear (Sprint 44).

    `ExpedienteFormDialog` (app/views/expedientes.py) ya resolvia este mismo
    problema para `Expediente` con `session.get(...) if id else Modelo()`
    seguido de asignacion atributo por atributo; esta funcion extrae ese
    patron para que `ObligacionFormDialog` y `EventoLaboralFormDialog` lo
    compartan en vez de duplicarlo cada uno por su lado (los dos formularios
    ya construian sus campos como un dict de kwargs antes de guardar, asi que
    aqui se reciben como `**campos` y se aplican con `setattr` en el camino de
    edicion, o se pasan tal cual al constructor en el camino de creacion).

    No hace `session.close()` -- el llamador sigue siendo dueño del ciclo de
    vida de la sesion (igual que antes de esta extraccion), para no forzar un
    unico patron de apertura/cierre entre los dialogos que la usen.
    """
    if id_existente is not None:
        instancia = session.get(modelo_cls, id_existente)
        for campo, valor in campos.items():
            setattr(instancia, campo, valor)
    else:
        instancia = modelo_cls(**campos)
        session.add(instancia)
    session.commit()
    return instancia.id


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


def agregar_ayuda(
    layout: QFormLayout,
    etiqueta: str,
    campo: QWidget,
    *,
    tooltip: str,
    ejemplo: str | None = None,
) -> QWidget:
    """Agrega una fila a `layout` con `campo` y un icono (i) al lado, con
    tooltip explicativo (mas un ejemplo concreto si se da) -- Sprint 59.

    Extraido de `ObligacionFormDialog._envolver_campo_con_iconos` (Sprint 34),
    que originalmente solo agregaba este icono informativo junto a "Tasa
    efectiva anual". Se generaliza aqui como funcion compartida para que los
    4 formularios principales de captura (Parametros, Expediente, Obligacion,
    Abono) lo usen en vez de reimplementar el mismo patron cada uno.

    Si se da `ejemplo`, se concatena al tooltip como una segunda linea
    ("{tooltip}\\nEjemplo: {ejemplo}") -- mismo formato que ya usaba el
    unico call site en produccion cuando el texto ya incluia el ejemplo en
    una sola frase (ese caso sigue funcionando igual pasando solo `tooltip`,
    sin `ejemplo`).

    Retorna el contenedor (fila + icono) para que el caller lo use como el
    widget de la fila si necesita ocultarlo despues con `set_row_visible`.
    """
    contenedor = QWidget()
    layout_fila = QHBoxLayout(contenedor)
    layout_fila.setContentsMargins(0, 0, 0, 0)
    layout_fila.addWidget(campo)
    etiqueta_info = QLabel()
    etiqueta_info.setPixmap(icon("info").pixmap(16, 16))
    texto_tooltip = tooltip if ejemplo is None else f"{tooltip}\nEjemplo: {ejemplo}"
    etiqueta_info.setToolTip(texto_tooltip)
    layout_fila.addWidget(etiqueta_info)
    layout.addRow(etiqueta, contenedor)
    return contenedor


def hacer_redimensionable(dialog: QDialog) -> None:
    """Agrega minimizar/maximizar y redimensionado a un QDialog -- Qt no los
    incluye por defecto en Windows (Sprint 56). Llamar una vez en __init__,
    justo despues de super().__init__(parent)."""
    dialog.setWindowFlags(
        dialog.windowFlags()
        | Qt.WindowType.WindowMinimizeButtonHint
        | Qt.WindowType.WindowMaximizeButtonHint
    )
