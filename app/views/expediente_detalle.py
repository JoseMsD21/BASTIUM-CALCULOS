from PySide6.QtWidgets import QWidget


class ExpedienteDetallePage(QWidget):
    def __init__(self, on_liquidado=None):
        super().__init__()
        self._on_liquidado = on_liquidado
        self._expediente_id = None

    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
