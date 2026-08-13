from PySide6.QtCore import Signal
from PySide6.QtWidgets import QHBoxLayout, QPushButton, QStackedWidget, QVBoxLayout, QWidget

from app.views.apariencia import AparienciaView
from app.views.configuracion import ParametrosView

SECCION_PARAMETROS = "parametros"
SECCION_APARIENCIA = "apariencia"

_ETIQUETA_POR_SECCION = {
    SECCION_PARAMETROS: "Parámetros",
    SECCION_APARIENCIA: "Apariencia",
}


class ConfiguracionesView(QWidget):
    """Pantalla "Configuraciones" (Sprint 66): submenu lateral estilo Ajustes
    (Parametros, Apariencia, con espacio para futuras secciones) + panel de
    contenido que alterna entre ellas segun la seccion elegida. Reemplaza el
    acceso directo que antes llevaba de un clic del sidebar principal
    directamente a ParametrosView."""

    # Emitida cada vez que cambia la seccion activa (mostrar_parametros()/
    # mostrar_apariencia()), con el nombre de la nueva seccion -- MainWindow la
    # usa para mantener el breadcrumb sincronizado sin que esta clase conozca
    # nada sobre breadcrumbs.
    seccion_cambiada = Signal(str)

    def __init__(self):
        super().__init__()
        self._seccion_actual = SECCION_PARAMETROS

        self.parametros_view = ParametrosView()
        self.apariencia_view = AparienciaView()

        self.boton_seccion_parametros = QPushButton(" Parámetros")
        self.boton_seccion_parametros.clicked.connect(self.mostrar_parametros)

        self.boton_seccion_apariencia = QPushButton(" Apariencia")
        self.boton_seccion_apariencia.clicked.connect(self.mostrar_apariencia)

        submenu = QWidget()
        layout_submenu = QVBoxLayout(submenu)
        layout_submenu.addWidget(self.boton_seccion_parametros)
        layout_submenu.addWidget(self.boton_seccion_apariencia)
        layout_submenu.addStretch()

        self._stack_secciones = QStackedWidget()
        self._stack_secciones.addWidget(self.parametros_view)
        self._stack_secciones.addWidget(self.apariencia_view)

        layout = QHBoxLayout()
        layout.addWidget(submenu)
        layout.addWidget(self._stack_secciones, stretch=1)
        self.setLayout(layout)

        self._actualizar_estado_activo_submenu()

    @property
    def seccion_actual(self) -> str:
        return self._seccion_actual

    def etiqueta_seccion_actual(self) -> str:
        return _ETIQUETA_POR_SECCION[self._seccion_actual]

    def mostrar_parametros(self) -> None:
        self._seccion_actual = SECCION_PARAMETROS
        self._stack_secciones.setCurrentWidget(self.parametros_view)
        self.parametros_view.refrescar()
        self._actualizar_estado_activo_submenu()
        self.seccion_cambiada.emit(self._seccion_actual)

    def mostrar_apariencia(self) -> None:
        self._seccion_actual = SECCION_APARIENCIA
        self._stack_secciones.setCurrentWidget(self.apariencia_view)
        self._actualizar_estado_activo_submenu()
        self.seccion_cambiada.emit(self._seccion_actual)

    def _actualizar_estado_activo_submenu(self) -> None:
        # Misma convencion class="primary"/"secondary" que usa el sidebar
        # principal (MainWindow._actualizar_estado_activo_navegacion) para
        # resaltar la seccion activa -- unpolish()/polish() manual porque el
        # cambio ocurre en tiempo de ejecucion, despues del primer show().
        self.boton_seccion_parametros.setProperty(
            "class", "primary" if self._seccion_actual == SECCION_PARAMETROS else "secondary"
        )
        self.boton_seccion_parametros.style().unpolish(self.boton_seccion_parametros)
        self.boton_seccion_parametros.style().polish(self.boton_seccion_parametros)
        self.boton_seccion_apariencia.setProperty(
            "class", "primary" if self._seccion_actual == SECCION_APARIENCIA else "secondary"
        )
        self.boton_seccion_apariencia.style().unpolish(self.boton_seccion_apariencia)
        self.boton_seccion_apariencia.style().polish(self.boton_seccion_apariencia)
