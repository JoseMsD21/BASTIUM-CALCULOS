"""Widget de notificacion no bloqueante ("toast"/snackbar) -- Sprint 36.

Sustituye a `QMessageBox.information(...)` para confirmaciones de bajo riesgo (ej.
"Obligación guardada" o "Exportación completa"): a diferencia de un QMessageBox, no
es modal -- no entra a un loop de eventos anidado, no roba el foco de teclado, y no
exige que el usuario haga clic para cerrarlo y seguir trabajando. Se implementa como
un QLabel hijo de la vista activa (no una ventana top-level aparte), superpuesto
sobre ella y con auto-ocultado via `QTimer.singleShot`.

`QMessageBox` se mantiene para errores y para confirmaciones de acciones
destructivas/irreversibles (ver `resources/theme.qss` y la convencion de clase de
boton "primary"/"secondary"/"destructive" del mismo sprint) -- ese feedback SI debe
bloquear hasta que el usuario lo reconozca.
"""

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QLabel, QWidget

from app.core import theme_colors as colores

DURACION_MS_DEFECTO = 3000
_MARGEN_INFERIOR_PX = 24

_ESTILO_POR_TIPO = {
    "success": (colores.EXITO, colores.TEXTO_SOBRE_PRIMARIO),
    "info": (colores.PRIMARIO, colores.TEXTO_SOBRE_PRIMARIO),
    "warning": (colores.ADVERTENCIA, colores.TEXTO_SOBRE_PRIMARIO),
}


def mostrar_toast(
    parent: QWidget,
    mensaje: str,
    tipo: str = "success",
    duracion_ms: int = DURACION_MS_DEFECTO,
) -> QLabel:
    """Muestra `mensaje` como notificacion flotante no bloqueante sobre `parent`.

    Se auto-oculta despues de `duracion_ms` milisegundos sin necesidad de
    interaccion del usuario. Al ser un widget hijo comun (no una ventana modal),
    el resto de `parent` sigue recibiendo clics y eventos de teclado con
    normalidad mientras el toast esta visible. Devuelve el QLabel creado -- los
    llamadores de produccion pueden ignorar el valor de retorno; existe
    principalmente para que los tests puedan inspeccionar su estado.
    """
    fondo, texto = _ESTILO_POR_TIPO.get(tipo, _ESTILO_POR_TIPO["success"])

    toast = QLabel(mensaje, parent)
    toast.setWordWrap(True)
    toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
    toast.setStyleSheet(
        f"background-color: {fondo}; color: {texto}; padding: 10px 18px; "
        "border-radius: 6px; font-weight: bold;"
    )
    toast.adjustSize()
    _posicionar_sobre(toast, parent)
    toast.show()
    toast.raise_()

    QTimer.singleShot(duracion_ms, toast.close)
    return toast


def _posicionar_sobre(toast: QLabel, parent: QWidget) -> None:
    """Centra `toast` horizontalmente, pegado al borde inferior de `parent`."""
    x = max(0, (parent.width() - toast.width()) // 2)
    y = max(0, parent.height() - toast.height() - _MARGEN_INFERIOR_PX)
    toast.move(x, y)
