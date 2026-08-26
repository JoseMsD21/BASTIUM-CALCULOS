"""Sección "Restablecer" de Configuraciones: ConfirmarRestablecerDialog (esta
clase) exige escribir "RESTABLECER" para habilitar el botón de confirmar --
misma filosofía de "sin papelera, definitivo tras confirmar" que ya usan
Eliminar en Obligaciones/Abonos (Sprint 60), reforzada porque el radio de
acción de esta acción es TODA la base, no una fila."""

from pathlib import Path

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.core.apariencia import MODO_CLARO, aplicar_tema, guardar_modo_tema
from app.services.restablecer_service import (
    crear_backup_de_base_de_datos,
    restablecer_datos_fabrica,
)
from app.views.concurrency import TareaEnHilo
from app.views.form_utils import hacer_redimensionable


def _restablecer_en_hilo_de_fondo() -> Path:
    """Se ejecuta en el QThreadPool (Sprint 26/112), no en el hilo de UI --
    mismo patron que `_liquidar_en_hilo_de_fondo` (expediente_detalle.py).
    El backup y el borrado deben correr en ESTE orden y en el MISMO hilo (el
    borrado solo debe intentarse si el backup tuvo exito) -- una sola tarea
    en vez de dos, para no complicar la coordinacion entre hilos por algo
    que ya es secuencial por diseño."""
    ruta_backup = crear_backup_de_base_de_datos()
    restablecer_datos_fabrica()
    return ruta_backup


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
    con backup automático previo y confirmación escrita.

    Backup + borrado corren en el `QThreadPool` (Sprint 112) en vez de
    bloquear el hilo de UI sin ningún indicio visual -- con meses/años de
    historial, la copia del archivo completo y el borrado ORM fila-por-fila
    tardan lo suficiente para que la app pareciera congelada, en la
    operación más destructiva e irreversible de todas."""

    restablecimiento_finalizado = Signal()

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
        if not self.boton_restablecer.isEnabled():
            return  # ya hay un restablecimiento en curso
        dialogo = ConfirmarRestablecerDialog(self)
        if not dialogo.exec():
            return
        self.boton_restablecer.setEnabled(False)

        self._dialogo_progreso = QProgressDialog(
            "Restableciendo datos de fábrica...", None, 0, 0, self
        )
        self._dialogo_progreso.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialogo_progreso.setCancelButton(None)
        self._dialogo_progreso.setMinimumDuration(0)
        self._dialogo_progreso.show()

        self._tarea_restablecer = TareaEnHilo(_restablecer_en_hilo_de_fondo)
        self._tarea_restablecer.senales.completada.connect(self._on_restablecer_completado)
        self._tarea_restablecer.senales.fallo.connect(self._on_restablecer_fallo)
        QThreadPool.globalInstance().start(self._tarea_restablecer)

    def _finalizar_restablecimiento_en_curso(self) -> None:
        self._dialogo_progreso.close()
        self.boton_restablecer.setEnabled(True)

    def _on_restablecer_completado(self, ruta_backup: Path) -> None:
        self._finalizar_restablecimiento_en_curso()
        guardar_modo_tema(MODO_CLARO)
        aplicar_tema(QApplication.instance(), MODO_CLARO)
        QMessageBox.information(
            self,
            "Restablecimiento completo",
            "Se restablecieron los datos de fábrica.\n"
            f"Copia de seguridad guardada en:\n{ruta_backup}",
        )
        self.restablecimiento_finalizado.emit()

    def _on_restablecer_fallo(self, error: Exception) -> None:
        self._finalizar_restablecimiento_en_curso()
        if isinstance(error, OSError):
            QMessageBox.critical(
                self,
                "Error al crear el backup",
                f"No se pudo crear la copia de seguridad, no se borró nada:\n{error}",
            )
            self.restablecimiento_finalizado.emit()
            return
        # Error inesperado (no OSError del backup): mismo criterio que
        # ExpedienteDetallePage._on_liquidar_fallo -- se emite la señal ANTES
        # de relanzar para que restablecimiento_finalizado sea un invariante
        # confiable en todo camino de salida, y Qt lo captura con su
        # manejador de excepciones por defecto al correr en el hilo
        # principal via una señal encolada entre hilos.
        self.restablecimiento_finalizado.emit()
        raise error
