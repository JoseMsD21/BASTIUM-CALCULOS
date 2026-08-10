"""QSettings compartido (Sprint 50).

`MainWindow._crear_settings()` establecio este patron en el Sprint 37 (formato
Ini explicito, no el nativo por plataforma, para que
`QSettings.setPath()` pueda redirigirlo por completo en los tests -- ver
`tests/conftest.py::_qsettings_aislado`). Se extrae aqui para que la
persistencia del modo oscuro/claro (`app/core/apariencia.py`) reutilice la
misma logica de aislamiento en vez de duplicarla; `MainWindow._crear_settings()`
ahora delega en `crear_settings()`.
"""

from PySide6.QtCore import QCoreApplication, QSettings

# Namespace usado si QCoreApplication.organizationName()/applicationName() todavia
# no se fijaron (ej. tests que construyen widgets sin pasar por main.py) -- coincide
# con los valores que main.py fija en la app real (Sprint 37).
_ORGANIZACION_POR_DEFECTO = "BASTIUM"
_APLICACION_POR_DEFECTO = "BASTIUM"


def crear_settings() -> QSettings:
    """QSettings con formato Ini explicito apuntando al namespace BASTIUM."""
    organizacion = QCoreApplication.organizationName() or _ORGANIZACION_POR_DEFECTO
    aplicacion = QCoreApplication.applicationName() or _APLICACION_POR_DEFECTO
    return QSettings(
        QSettings.Format.IniFormat, QSettings.Scope.UserScope, organizacion, aplicacion
    )
