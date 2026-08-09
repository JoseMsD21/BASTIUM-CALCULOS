from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
)

import database.session as session_module
from app.views.icons import icon
from database.models import DescuentoLaboral


class DescuentoLaboralFormDialog(QDialog):
    """Descuento del empleador sobre una obligacion Laboral (Sprint 44, punto
    3) -- mismo patron de dialogo que `AbonoFormDialog` (app/views/abonos.py),
    solo que en vez de reducir la deuda como un pago del deudor, modela un
    descuento que el empleador ya aplico (legal o no) sobre lo que le debe al
    trabajador. `LaboralStrategy.liquidar()` reutiliza el mismo mecanismo de
    pagos/allocation para restarlo del neto adeudado."""

    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar descuento del empleador")
        self._obligacion_id = obligacion_id

        self.campo_fecha = QDateEdit(QDate.currentDate())
        self.campo_fecha.setCalendarPopup(True)
        self.campo_monto = QLineEdit()
        self.check_es_legal = QCheckBox("Descuento legal (autorizado)")
        self.check_es_legal.setChecked(True)
        self.check_es_legal.setToolTip(
            "Desmarca si el descuento no estaba autorizado -- es solo informativo para "
            "el reporte, no cambia como se resta del neto adeudado."
        )
        self.campo_motivo = QLineEdit()
        self.campo_motivo.setToolTip("Motivo del descuento (opcional, ej. 'Prestamo cooperativa').")

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        # Enter/Return dispara Guardar (Sprint 37): Qt ya trata automaticamente al
        # unico QPushButton de un QDialog como boton por defecto, pero se fija
        # explicitamente para no depender de ese comportamiento implicito si en el
        # futuro se agrega otro boton (ej. "Cancelar").
        self.boton_guardar.setDefault(True)
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Fecha", self.campo_fecha)
        layout.addRow("Monto", self.campo_monto)
        layout.addRow(self.check_es_legal)
        layout.addRow("Motivo (opcional)", self.campo_motivo)
        layout.addRow(self.boton_guardar)
        self.setLayout(layout)

    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del descuento debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        descuento = DescuentoLaboral(
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            es_legal=self.check_es_legal.isChecked(),
            motivo=self.campo_motivo.text().strip() or None,
        )
        session.add(descuento)
        session.commit()
        descuento_id = descuento.id
        session.close()
        return descuento_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
