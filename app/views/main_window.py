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

        self._history: list[str] = []
        self._current_page_name = "expedientes"

        self.show_page("expedientes")

    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name

    def _volver(self) -> None:
        if not self._history:
            return
        pagina_anterior = self._history.pop()
        self.show_page(pagina_anterior, add_to_history=False)

    def _ir_inicio(self) -> None:
        self._history.clear()
        self.show_page("expedientes", add_to_history=False)

    def _abrir_detalle(self, expediente_id: int) -> None:
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")

    def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
        self.resultado_page.mostrar(resultado, expediente_id)
        self.show_page("resultado")
