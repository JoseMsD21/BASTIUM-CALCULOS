from pathlib import Path

from PySide6 import QtSvg  # noqa: F401 - registra el icon engine de SVG en QIcon/QPixmap
from PySide6.QtGui import QIcon

from app.assets.logos import ICONO_APP_PNG

ICONOS_DISPONIBLES = frozenset(
    {"home", "back", "settings", "save", "cancel", "delete", "export", "info", "warning"}
)

_ICONS_DIR = Path(__file__).resolve().parents[2] / "resources" / "icons"


def icon(nombre: str) -> QIcon:
    """Carga uno de los iconos de navegacion/accion/estado del proyecto.

    Nombres validos: "home" (Inicio), "back" (Volver), "settings" (Configuraciones),
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
    """Icono de marca de BASTIUM para `MainWindow.setWindowIcon()`.

    Sprint 31: circulo borgona con una "B" (SVG provisional). Sprint 122: el
    monograma oficial "B." del equipo (`app/assets/marca/bastium-icono-256.png`).
    """
    return QIcon(str(ICONO_APP_PNG))
