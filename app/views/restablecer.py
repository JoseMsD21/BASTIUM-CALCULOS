"""Sección "Restablecer" de Configuraciones: ConfirmarRestablecerDialog (esta
clase) exige escribir "RESTABLECER" para habilitar el botón de confirmar --
misma filosofía de "sin papelera, definitivo tras confirmar" que ya usan
Eliminar en Obligaciones/Abonos (Sprint 60), reforzada porque el radio de
acción de esta acción es TODA la base, no una fila."""

from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.apariencia import MODO_CLARO, aplicar_tema, guardar_modo_tema
from app.services.restablecer_service import (
    crear_backup_de_base_de_datos,
    restablecer_datos_fabrica,
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


class RestablecerView(QWidget):
    """Sección "Restablecer" de Configuraciones (ver design spec
    2026-08-13-restablecer-datos-fabrica-design.md): borra todos los
    expedientes y los parámetros legales de usuario, restaura el tema claro,
    con backup automático previo y confirmación escrita."""

    def __init__(self):
        super().__init__()

        descripcion = QLabel(
            "Borra todos los expedientes, obligaciones, abonos, eventos, descuentos y "
            "los parámetros legales que hayas cargado tú mismo, dejando la app como "
            "recién instalada (los parámetros de sistema y el tema claro por defecto "
            "quedan intactos/restaurados). Antes de borrar se crea automáticamente una "
            "copia de seguridad en la carpeta backups/."
        )
        descripcion.setWordWrap(True)

        self.boton_restablecer = QPushButton("Restablecer datos de fábrica")
        self.boton_restablecer.setProperty("class", "destructive")
        self.boton_restablecer.clicked.connect(self._restablecer)

        layout = QVBoxLayout()
        layout.addWidget(descripcion)
        layout.addWidget(self.boton_restablecer)
        layout.addStretch()
        self.setLayout(layout)

    def _restablecer(self) -> None:
        dialogo = ConfirmarRestablecerDialog(self)
        if not dialogo.exec():
            return
        try:
            ruta_backup = crear_backup_de_base_de_datos()
        except OSError as error:
            QMessageBox.critical(
                self,
                "Error al crear el backup",
                f"No se pudo crear la copia de seguridad, no se borró nada:\n{error}",
            )
            return
        restablecer_datos_fabrica()
        guardar_modo_tema(MODO_CLARO)
        aplicar_tema(QApplication.instance(), MODO_CLARO)
        QMessageBox.information(
            self,
            "Restablecimiento completo",
            "Se restablecieron los datos de fábrica.\n"
            f"Copia de seguridad guardada en:\n{ruta_backup}",
        )
