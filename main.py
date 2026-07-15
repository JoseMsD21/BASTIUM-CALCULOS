import sys

from PySide6.QtWidgets import QApplication

from database.database import init_db
from app.views.main_window import MainWindow


def main() -> None:
    init_db()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.resize(1000, 700)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
