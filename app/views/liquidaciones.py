from PySide6.QtWidgets import QWidget


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()
        self._resultado = None

    def mostrar(self, resultado) -> None:
        self._resultado = resultado
