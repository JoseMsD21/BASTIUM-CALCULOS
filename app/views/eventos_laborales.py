from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QComboBox, QDateEdit, QDialog, QFormLayout, QMessageBox, QPushButton

import database.session as session_module
from app.views.icons import icon
from database.models import EventoLaboral, MotivoSuspension, TipoEventoLaboral


class EventoLaboralFormDialog(QDialog):
    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar evento contractual")
        self._obligacion_id = obligacion_id

        self.combo_tipo = QComboBox()
        self.combo_tipo.addItem("Suspension", userData=TipoEventoLaboral.SUSPENSION)
        self.combo_tipo.addItem("Incapacidad comun", userData=TipoEventoLaboral.INCAPACIDAD_COMUN)
        self.combo_tipo.addItem("Incapacidad laboral", userData=TipoEventoLaboral.INCAPACIDAD_LABORAL)

        self.campo_fecha_inicio = QDateEdit(QDate.currentDate())
        self.campo_fecha_inicio.setCalendarPopup(True)
        self.campo_fecha_fin = QDateEdit(QDate.currentDate())
        self.campo_fecha_fin.setCalendarPopup(True)

        self.combo_motivo = QComboBox()
        self.combo_motivo.addItem("Huelga", userData=MotivoSuspension.HUELGA)
        self.combo_motivo.addItem("Licencia no remunerada", userData=MotivoSuspension.LICENCIA_NO_REMUNERADA)
        self.combo_motivo.addItem("Disciplinaria", userData=MotivoSuspension.DISCIPLINARIA)

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Tipo de evento", self.combo_tipo)
        layout.addRow("Fecha de inicio", self.campo_fecha_inicio)
        layout.addRow("Fecha de fin", self.campo_fecha_fin)
        layout.addRow("Motivo de suspension", self.combo_motivo)
        layout.addRow(self.boton_guardar)
        self.setLayout(layout)

        self.combo_tipo.currentIndexChanged.connect(self._actualizar_visibilidad_motivo)
        self._actualizar_visibilidad_motivo()

    def _actualizar_visibilidad_motivo(self) -> None:
        self.combo_motivo.setVisible(self.combo_tipo.currentData() == TipoEventoLaboral.SUSPENSION)

    def guardar(self) -> int:
        qdate_inicio = self.campo_fecha_inicio.date()
        fecha_inicio = date(qdate_inicio.year(), qdate_inicio.month(), qdate_inicio.day())
        qdate_fin = self.campo_fecha_fin.date()
        fecha_fin = date(qdate_fin.year(), qdate_fin.month(), qdate_fin.day())

        if fecha_fin <= fecha_inicio:
            raise ValueError("La fecha de fin debe ser posterior a la fecha de inicio del evento.")

        tipo = self.combo_tipo.currentData()
        motivo = self.combo_motivo.currentData() if tipo == TipoEventoLaboral.SUSPENSION else None

        session = session_module.get_session()
        evento = EventoLaboral(
            obligacion_id=self._obligacion_id,
            tipo=tipo,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            motivo_suspension=motivo,
        )
        session.add(evento)
        session.commit()
        evento_id = evento.id
        session.close()
        return evento_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
