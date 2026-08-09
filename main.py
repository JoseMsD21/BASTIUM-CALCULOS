import sys

from PySide6.QtWidgets import QApplication

from app._version import __version__
from app.core.apariencia import aplicar_tema, cargar_modo_tema
from app.views.main_window import MainWindow
from database.database import aplicar_migraciones_pendientes, init_db


def main() -> None:
    init_db()
    aplicar_migraciones_pendientes()
    app = QApplication(sys.argv)
    app.setOrganizationName("BASTIUM")
    app.setApplicationName("BASTIUM")
    app.setApplicationVersion(__version__)
    # Restaura el modo oscuro/claro elegido en la sesion anterior (Sprint 50) --
    # cargar_modo_tema() debe llamarse despues de fijar organizationName/
    # applicationName arriba, porque QSettings los usa para ubicar el .ini.
    aplicar_tema(app, cargar_modo_tema())
    window = MainWindow()
    # La geometria (tamaño/posicion/maximizado) se restaura sola en __init__ via
    # QSettings, con fallback a 1000x700 en el primer arranque (Sprint 37) -- ya no
    # hace falta fijarla aqui incondicionalmente.
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
