from PySide6.QtWidgets import QWidget


class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
