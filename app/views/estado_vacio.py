"""Estado vacío con la mascota de BASTIUM (Sprint 128).

Guía de identidad (`docs/identidad/GUIA_DE_IDENTIDAD.md`, "Experiencia de usuario"):
cuando una lista no tiene datos, en vez de una tabla en blanco se muestra la mascota
en pequeño y en tono suave, con una frase que explica qué pasa y qué hacer.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QVBoxLayout, QWidget

from app.assets.logos import MASCOTA_TRANSPARENTE
from app.core import theme_colors as colores

ALTO_MASCOTA = 88
OPACIDAD_MASCOTA = 0.55


def crear_etiqueta_mascota() -> QLabel:
    """La mascota pequeña y en tono suave, lista para poner sobre un mensaje."""
    etiqueta = QLabel()
    etiqueta.setObjectName("estado_vacio_mascota")
    etiqueta.setPixmap(
        QPixmap(str(MASCOTA_TRANSPARENTE)).scaledToHeight(
            ALTO_MASCOTA, Qt.TransformationMode.SmoothTransformation
        )
    )
    etiqueta.setAlignment(Qt.AlignmentFlag.AlignCenter)
    efecto = QGraphicsOpacityEffect(etiqueta)
    efecto.setOpacity(OPACIDAD_MASCOTA)
    etiqueta.setGraphicsEffect(efecto)
    return etiqueta


class EstadoVacio(QWidget):
    """Mascota + mensaje centrados. `set_mensaje()` cambia el texto sin rehacer el
    widget (ej. el listado de expedientes distingue "no hay ninguno" de "ninguno
    coincide con los filtros")."""

    def __init__(self, mensaje: str = "", parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("estado_vacio")

        self.etiqueta_mascota = crear_etiqueta_mascota()

        self.etiqueta_mensaje = QLabel(mensaje)
        self.etiqueta_mensaje.setObjectName("estado_vacio_mensaje")
        self.etiqueta_mensaje.setWordWrap(True)
        self.etiqueta_mensaje.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_mensaje.setStyleSheet(
            f"color: {colores.TEXTO_SECUNDARIO}; font-size: 10.5pt; padding: 4px 16px;"
        )

        layout = QVBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.etiqueta_mascota)
        layout.addWidget(self.etiqueta_mensaje)
        layout.addStretch()

    def set_mensaje(self, mensaje: str) -> None:
        self.etiqueta_mensaje.setText(mensaje)

    def mensaje(self) -> str:
        return self.etiqueta_mensaje.text()
