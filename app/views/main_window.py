from PySide6.QtWidgets import QMainWindow, QPushButton, QStackedWidget, QToolBar

from app.views.configuracion import ParametrosView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
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
        self.parametros_page = ParametrosView()

        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)
        self.stacked_widget.addWidget(self.parametros_page)

        self._pages = {
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
            "parametros": self.parametros_page,
        }

        self._history: list[str] = []
        self._current_page_name = "expedientes"

        self._crear_barra_navegacion()
        self.show_page("expedientes")

    def _crear_barra_navegacion(self) -> None:
        barra = QToolBar("Navegacion")
        barra.setMovable(False)

        self.boton_volver = QPushButton("← Volver")
        self.boton_volver.clicked.connect(self._volver)
        barra.addWidget(self.boton_volver)

        self.boton_inicio = QPushButton("\U0001F3E0 Inicio")
        self.boton_inicio.clicked.connect(self._ir_inicio)
        barra.addWidget(self.boton_inicio)

        self.boton_parametros = QPushButton("⚙ Parametros")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()

    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name
        self._actualizar_botones_navegacion()

    def _actualizar_botones_navegacion(self) -> None:
        self.boton_volver.setVisible(bool(self._history))
        self.boton_inicio.setVisible(self._current_page_name != "expedientes")

    def showEvent(self, event) -> None:
        # QToolBar resets the visibility of widgets added via addWidget() to True
        # the first time the toolbar itself becomes visible, overriding any
        # setVisible(False) applied while the window was not yet shown. Resync
        # the buttons' visibility once the window is actually shown.
        super().showEvent(event)
        self._actualizar_botones_navegacion()

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

    def _ir_a_parametros(self) -> None:
        self.parametros_page.refrescar()
        self.show_page("parametros")
