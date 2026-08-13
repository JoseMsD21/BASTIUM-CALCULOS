from PySide6.QtWidgets import QApplication, QCheckBox, QLabel, QVBoxLayout, QWidget

from app.core.apariencia import (
    MODO_CLARO,
    MODO_OSCURO,
    aplicar_tema,
    cargar_modo_tema,
    guardar_modo_tema,
)


class AparienciaView(QWidget):
    """Seccion "Apariencia" de Configuraciones (Sprint 66): aloja el interruptor
    de modo oscuro/claro, movido aqui desde ParametrosView (donde vivia de forma
    temporal desde el Sprint 50 -- ver app/views/configuracion.py)."""

    def __init__(self):
        super().__init__()

        self.casilla_modo_oscuro = QCheckBox("Modo oscuro")
        self.casilla_modo_oscuro.setChecked(cargar_modo_tema() == MODO_OSCURO)
        self.casilla_modo_oscuro.toggled.connect(self._alternar_modo_tema)

        descripcion = QLabel(
            "Cambia los colores de toda la aplicacion entre el tema claro (por defecto) y "
            "el tema oscuro, incluida la grafica del Dashboard. El cambio se aplica de "
            "inmediato, sin reiniciar el programa, y se recuerda la proxima vez que abras "
            "BASTIUM."
        )
        descripcion.setWordWrap(True)

        layout = QVBoxLayout()
        layout.addWidget(self.casilla_modo_oscuro)
        layout.addWidget(descripcion)
        layout.addStretch()
        self.setLayout(layout)

    def _alternar_modo_tema(self, marcado: bool) -> None:
        """Aplica el tema en caliente (sin reiniciar la app) y persiste la
        eleccion -- ver `app.core.apariencia.aplicar_tema()`/`guardar_modo_tema()`."""
        modo = MODO_OSCURO if marcado else MODO_CLARO
        aplicar_tema(QApplication.instance(), modo)
        guardar_modo_tema(modo)
