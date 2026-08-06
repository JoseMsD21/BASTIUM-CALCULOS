from pathlib import Path

from PySide6 import QtSvg  # noqa: F401 - registra el icon engine de SVG en QIcon/QPixmap
from PySide6.QtGui import QIcon

ICONOS_DISPONIBLES = frozenset(
    {"home", "back", "settings", "save", "cancel", "delete", "export", "info", "warning"}
)

_ICONS_DIR = Path(__file__).resolve().parents[2] / "resources" / "icons"
_APP_ICON_PATH = Path(__file__).resolve().parents[2] / "resources" / "icon_app.svg"


def icon(nombre: str) -> QIcon:
    """Carga uno de los iconos de navegacion/accion/estado del proyecto.

    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Parametros),
    "save" (Guardar), "cancel" (Cancelar -- provisionado, sin boton "Cancelar"
    existente todavia en el codigo), "delete" (Eliminar), "export" (Exportar) --
    los 7 del set minimo del Sprint 31 -- mas "info" (icono informativo junto a
    un valor por defecto) y "warning" (icono de advertencia de validacion en
    tiempo real), agregados en el Sprint 34. Los SVG viven en
    `resources/icons/<nombre>.svg`.
    """
    if nombre not in ICONOS_DISPONIBLES:
        raise ValueError(
            f"'{nombre}' no es un icono valido. Disponibles: {sorted(ICONOS_DISPONIBLES)}"
        )
    return QIcon(str(_ICONS_DIR / f"{nombre}.svg"))


def icono_aplicacion() -> QIcon:
    """Icono de marca de BASTIUM para `MainWindow.setWindowIcon()` (Sprint 31)."""
    return QIcon(str(_APP_ICON_PATH))
