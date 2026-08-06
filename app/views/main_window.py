from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QLabel, QMainWindow, QPushButton, QStackedWidget, QToolBar

import database.session as session_module
from app.views.configuracion import ParametrosView
from app.views.dashboard import DashboardView
from app.views.expediente_detalle import ExpedienteDetallePage
from app.views.expedientes import ExpedientesListView
from app.views.icons import icon, icono_aplicacion
from app.views.liquidaciones import ResultadoLiquidacionView
from database.models import Expediente


class MainWindow(QMainWindow):
    """Ventana principal: aloja las pantallas del flujo y la navegacion entre ellas."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("BASTIUM - Ecosistema de Liquidacion Forense")
        self.setWindowIcon(icono_aplicacion())

        self.stacked_widget = QStackedWidget()
        self.setCentralWidget(self.stacked_widget)

        self.dashboard_page = DashboardView(
            on_expediente_abierto=self._abrir_detalle,
            on_ver_expedientes=self._ir_a_expedientes,
        )
        self.expedientes_page = ExpedientesListView(on_expediente_abierto=self._abrir_detalle)
        self.detalle_page = ExpedienteDetallePage(on_liquidado=self._mostrar_resultado)
        self.resultado_page = ResultadoLiquidacionView()
        self.parametros_page = ParametrosView()

        self.stacked_widget.addWidget(self.dashboard_page)
        self.stacked_widget.addWidget(self.expedientes_page)
        self.stacked_widget.addWidget(self.detalle_page)
        self.stacked_widget.addWidget(self.resultado_page)
        self.stacked_widget.addWidget(self.parametros_page)

        self._pages = {
            "dashboard": self.dashboard_page,
            "expedientes": self.expedientes_page,
            "detalle": self.detalle_page,
            "resultado": self.resultado_page,
            "parametros": self.parametros_page,
        }

        self._history: list[str] = []
        self._current_page_name = "dashboard"
        self._radicado_actual: str | None = None

        self._crear_barra_navegacion()
        self._crear_atajos_teclado()
        self.show_page("dashboard")

    def _crear_atajos_teclado(self) -> None:
        # Contexto por defecto de QShortcut (Qt.ShortcutContext.WindowShortcut): solo se
        # dispara si `self` (MainWindow) es la ventana activa. Cuando un dialogo modal
        # (ej. ExpedienteFormDialog) esta abierto, ese dialogo es la ventana activa y
        # MainWindow no lo es -- por eso Backspace no interfiere con la edicion de texto
        # dentro de los formularios (que viven en dialogos separados, no en las 4
        # pantallas alojadas directamente por MainWindow).
        self.atajo_volver_alt_izquierda = QShortcut(QKeySequence("Alt+Left"), self)
        self.atajo_volver_alt_izquierda.activated.connect(self._volver)

        self.atajo_volver_backspace = QShortcut(QKeySequence(Qt.Key.Key_Backspace), self)
        self.atajo_volver_backspace.activated.connect(self._volver)

        self.atajo_inicio = QShortcut(QKeySequence("Ctrl+Home"), self)
        self.atajo_inicio.activated.connect(self._ir_inicio)

    def _crear_barra_navegacion(self) -> None:
        barra = QToolBar("Navegacion")
        barra.setMovable(False)

        self.boton_volver = QPushButton(" Volver")
        self.boton_volver.setIcon(icon("back"))
        self.boton_volver.clicked.connect(self._volver)
        barra.addWidget(self.boton_volver)

        self.boton_inicio = QPushButton(" Inicio")
        self.boton_inicio.setIcon(icon("home"))
        self.boton_inicio.clicked.connect(self._ir_inicio)
        barra.addWidget(self.boton_inicio)

        self.boton_parametros = QPushButton(" Parametros")
        self.boton_parametros.setIcon(icon("settings"))
        self.boton_parametros.setProperty("class", "")
        self.boton_parametros.clicked.connect(self._ir_a_parametros)
        barra.addWidget(self.boton_parametros)

        barra.addSeparator()

        self.etiqueta_breadcrumb = QLabel()
        self.etiqueta_breadcrumb.setObjectName("etiqueta_breadcrumb")
        barra.addWidget(self.etiqueta_breadcrumb)

        self.addToolBar(barra)
        self._actualizar_botones_navegacion()

    def show_page(self, name: str, add_to_history: bool = True) -> None:
        if add_to_history and self._current_page_name != name:
            self._history.append(self._current_page_name)
        if name == "expedientes":
            self._radicado_actual = None
        self.stacked_widget.setCurrentWidget(self._pages[name])
        self._current_page_name = name
        self._actualizar_botones_navegacion()
        self._actualizar_breadcrumb()
        self._actualizar_estado_activo_navegacion()

    def _actualizar_botones_navegacion(self) -> None:
        self.boton_volver.setVisible(bool(self._history))
        self.boton_inicio.setVisible(self._current_page_name != "dashboard")

    def _actualizar_breadcrumb(self) -> None:
        self.etiqueta_breadcrumb.setText(self._texto_breadcrumb())

    def _texto_breadcrumb(self) -> str:
        if self._current_page_name == "parametros":
            return "Parámetros"
        if self._current_page_name == "detalle":
            if self._radicado_actual:
                return f"Expedientes › Radicado {self._radicado_actual}"
            return "Expedientes › Detalle"
        if self._current_page_name == "resultado":
            if self._radicado_actual:
                return f"Expedientes › Radicado {self._radicado_actual} › Liquidación"
            return "Expedientes › Liquidación"
        return "Expedientes"

    def _actualizar_estado_activo_navegacion(self) -> None:
        # boton_parametros es el unico boton de la barra que representa una pantalla fija
        # a la que el usuario puede "estar": Volver es una accion sin pantalla propia
        # (depende del historial) e Inicio se oculta justo cuando el usuario ya esta en
        # "expedientes" (nunca tendria sentido marcarlo "activo"). Se reutiliza la
        # convencion class="primary" del Sprint 31 (resources/theme.qss) para el estado
        # activo; fuera de "parametros" vuelve a la cadena vacia (estilo neutral). A
        # diferencia del Sprint 31 (que fijaba la propiedad una sola vez en __init__,
        # antes del primer show), aca el cambio ocurre en tiempo de ejecucion despues de
        # que la ventana ya se mostro, asi que hace falta unpolish()/polish() manual para
        # que Qt vuelva a evaluar el selector QSS.
        self.boton_parametros.setProperty(
            "class", "primary" if self._current_page_name == "parametros" else ""
        )
        self.boton_parametros.style().unpolish(self.boton_parametros)
        self.boton_parametros.style().polish(self.boton_parametros)

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
        self.dashboard_page.refrescar()
        self.show_page("dashboard", add_to_history=False)

    def _ir_a_expedientes(self) -> None:
        self.expedientes_page.refrescar()
        self.show_page("expedientes")

    def _obtener_radicado(self, expediente_id: int) -> str:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        radicado = expediente.radicado
        session.close()
        return radicado

    def _abrir_detalle(self, expediente_id: int) -> None:
        self._radicado_actual = self._obtener_radicado(expediente_id)
        self.detalle_page.cargar_expediente(expediente_id)
        self.show_page("detalle")

    def _mostrar_resultado(self, resultado, expediente_id: int) -> None:
        self.resultado_page.mostrar(resultado, expediente_id)
        self.show_page("resultado")

    def _ir_a_parametros(self) -> None:
        self.parametros_page.refrescar()
        self.show_page("parametros")
