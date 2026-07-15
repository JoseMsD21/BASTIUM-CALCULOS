from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from database.models import AreaDerecho, Expediente


class NuevoExpedienteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Nuevo expediente")

        self.campo_radicado = QLineEdit()
        self.campo_demandante = QLineEdit()
        self.campo_demandado = QLineEdit()
        self.campo_juzgado = QLineEdit()
        self.campo_fecha_corte = QDateEdit(QDate.currentDate())
        self.campo_fecha_corte.setCalendarPopup(True)

        self.combo_area = QComboBox()
        for codigo, etiqueta, habilitada in AREAS_DERECHO:
            self.combo_area.addItem(etiqueta, userData=codigo)
            if not habilitada:
                indice = self.combo_area.count() - 1
                item = self.combo_area.model().item(indice)
                item.setEnabled(False)
                item.setToolTip("Proximamente")

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Radicado", self.campo_radicado)
        layout.addRow("Demandante", self.campo_demandante)
        layout.addRow("Demandado", self.campo_demandado)
        layout.addRow("Area del derecho", self.combo_area)
        layout.addRow("Juzgado", self.campo_juzgado)
        layout.addRow("Fecha de corte", self.campo_fecha_corte)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

        self._expediente_id_creado = None

    def guardar(self) -> int:
        if not self.campo_radicado.text().strip():
            raise ValueError("El radicado es obligatorio.")

        qdate = self.campo_fecha_corte.date()
        fecha_corte = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        expediente = Expediente(
            radicado=self.campo_radicado.text().strip(),
            demandante=self.campo_demandante.text().strip(),
            demandado=self.campo_demandado.text().strip(),
            area_derecho=AreaDerecho(self.combo_area.currentData()),
            juzgado=self.campo_juzgado.text().strip() or None,
            fecha_corte_default=fecha_corte,
        )
        session.add(expediente)
        session.commit()
        expediente_id = expediente.id
        session.close()
        return expediente_id

    def _guardar_y_cerrar(self) -> None:
        try:
            self._expediente_id_creado = self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos incompletos", str(error))


class ExpedientesListView(QWidget):
    def __init__(self, on_expediente_abierto=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto

        self.tabla = QTableWidget(0, 4)
        self.tabla.setHorizontalHeaderLabels(["Radicado", "Demandante", "Demandado", "Area"])
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        boton_nuevo = QPushButton("Nuevo expediente")
        boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(boton_nuevo)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()

    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self.tabla.setRowCount(len(expedientes))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes):
            self.tabla.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla.setItem(fila, 1, QTableWidgetItem(expediente.demandante))
            self.tabla.setItem(fila, 2, QTableWidgetItem(expediente.demandado))
            self.tabla.setItem(fila, 3, QTableWidgetItem(expediente.area_derecho.value))
            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = NuevoExpedienteDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila[fila])
