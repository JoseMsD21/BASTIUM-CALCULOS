from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import QDateEdit, QDialog, QFormLayout, QLineEdit, QMessageBox, QPushButton

import database.session as session_module
from database.models import Abono


class AbonoFormDialog(QDialog):
    def __init__(self, obligacion_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar abono")
        self._obligacion_id = obligacion_id

        self.campo_fecha = QDateEdit(QDate.currentDate())
        self.campo_fecha.setCalendarPopup(True)
        self.campo_monto = QLineEdit()
        self.campo_referencia = QLineEdit()

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Fecha", self.campo_fecha)
        layout.addRow("Monto", self.campo_monto)
        layout.addRow("Referencia", self.campo_referencia)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

    def guardar(self) -> int:
        try:
            monto = Decimal(self.campo_monto.text())
        except InvalidOperation as error:
            raise ValueError("El monto debe ser un numero valido.") from error

        if monto <= Decimal("0"):
            raise ValueError("El monto del abono debe ser mayor que cero.")

        qdate = self.campo_fecha.date()
        fecha = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        abono = Abono(
            obligacion_id=self._obligacion_id,
            fecha=fecha,
            monto=monto,
            referencia=self.campo_referencia.text().strip() or None,
        )
        session.add(abono)
        session.commit()
        abono_id = abono.id
        session.close()
        return abono_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))
