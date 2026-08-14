"""Sección "Restablecer" de Configuraciones: ConfirmarRestablecerDialog (esta
clase) exige escribir "RESTABLECER" para habilitar el botón de confirmar --
misma filosofía de "sin papelera, definitivo tras confirmar" que ya usan
Eliminar en Obligaciones/Abonos (Sprint 60), reforzada porque el radio de
acción de esta acción es TODA la base, no una fila."""

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
)

from app.views.form_utils import hacer_redimensionable


class ConfirmarRestablecerDialog(QDialog):
    TEXTO_CONFIRMACION = "RESTABLECER"

    def __init__(self, parent=None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self.setWindowTitle("Confirmar restablecimiento")

        advertencia = QLabel(
            "Esta acción borra TODOS los expedientes, obligaciones, abonos, eventos, "
            "descuentos y los parámetros legales que hayas cargado tú mismo (los del "
            "sistema no se tocan). El tema visual vuelve a claro. No se puede deshacer, "
            "salvo restaurando el backup automático que se crea antes de borrar.\n\n"
            f"Escribe {self.TEXTO_CONFIRMACION} para habilitar el botón de confirmar."
        )
        advertencia.setWordWrap(True)

        self.campo_confirmacion = QLineEdit()
        self.campo_confirmacion.textChanged.connect(self._actualizar_estado_boton)

        self.boton_confirmar = QPushButton("Restablecer datos de fábrica")
        self.boton_confirmar.setProperty("class", "destructive")
        self.boton_confirmar.setEnabled(False)
        self.boton_confirmar.clicked.connect(self.accept)

        boton_cancelar = QPushButton("Cancelar")
        boton_cancelar.setProperty("class", "secondary")
        boton_cancelar.clicked.connect(self.reject)

        botones = QHBoxLayout()
        botones.addWidget(boton_cancelar)
        botones.addWidget(self.boton_confirmar)

        layout = QVBoxLayout()
        layout.addWidget(advertencia)
        layout.addWidget(self.campo_confirmacion)
        layout.addLayout(botones)
        self.setLayout(layout)

    def _actualizar_estado_boton(self, texto: str) -> None:
        self.boton_confirmar.setEnabled(texto == self.TEXTO_CONFIRMACION)
