import sys

from PySide6.QtWidgets import QApplication

from app._version import __version__
from app.views.main_window import MainWindow
from database.database import init_db


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    app.setApplicationName("BASTIUM")
    app.setApplicationVersion(__version__)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
