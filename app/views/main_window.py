from PySide6.QtWidgets import QMainWindow, QStackedWidget

from app.views.expedientes import ExpedientesListView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.liquidaciones import ResultadoLiquidacionView


class MainWindow(QMainWindow):
    """Ventana principal: aloja las 3 pantallas del flujo y la navegacion entre ellas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.expedientes_page = ExpedientesListView(on_expediente_abierto=self._abrir_detalle)
        self.detalle_page = ExpedienteDetallePage(on_liquidado=self._mostrar_resultado)
        self.resultado_page = ResultadoLiquidacionView()

        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)

        self._pages = {
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
        }
        self.show_page("expedientes")

    def show_page(self, name: str) -> None:
        self.stacked_widget.setCurrentWidget(self._pages[name])

    def _abrir_detalle(self, expediente_id: int) -> None:
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")

    def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
        self.resultado_page.mostrar(resultado, expediente_id)
        self.show_page("resultado")
