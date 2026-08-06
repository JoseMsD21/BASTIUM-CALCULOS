from datetime import date

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QInputDialog,
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
from app.views.icons import icon
from database.models import AreaDerecho, Expediente


class ExpedienteFormDialog(QDialog):
    def __init__(self, parent=None, expediente: Expediente | None = None):
        super().__init__(parent)
        self._expediente_id = expediente.id if expediente else None
        self.setWindowTitle("Editar expediente" if expediente else "Nuevo expediente")

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

        if expediente:
            self.campo_radicado.setText(expediente.radicado)
            self.campo_demandante.setText(expediente.demandante)
            self.campo_demandado.setText(expediente.demandado)
            self.campo_juzgado.setText(expediente.juzgado or "")
            self.campo_fecha_corte.setDate(
                QDate(
                    expediente.fecha_corte_default.year,
                    expediente.fecha_corte_default.month,
                    expediente.fecha_corte_default.day,
                )
            )
            indice_area = self.combo_area.findData(expediente.area_derecho.value)
            if indice_area >= 0:
                self.combo_area.setCurrentIndex(indice_area)

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Radicado", self.campo_radicado)
        layout.addRow("Demandante", self.campo_demandante)
        layout.addRow("Demandado", self.campo_demandado)
        layout.addRow("Area del derecho", self.combo_area)
        layout.addRow("Juzgado", self.campo_juzgado)
        layout.addRow("Fecha de corte", self.campo_fecha_corte)
        layout.addRow(self.boton_guardar)
        self.setLayout(layout)

        self._expediente_id_creado = None

    def guardar(self) -> int:
        if not self.campo_radicado.text().strip():
            raise ValueError("El radicado es obligatorio.")

        qdate = self.campo_fecha_corte.date()
        fecha_corte = date(qdate.year(), qdate.month(), qdate.day())

        session = session_module.get_session()
        if self._expediente_id is not None:
            expediente = session.get(Expediente, self._expediente_id)
        else:
            expediente = Expediente()
            session.add(expediente)

        expediente.radicado = self.campo_radicado.text().strip()
        expediente.demandante = self.campo_demandante.text().strip()
        expediente.demandado = self.campo_demandado.text().strip()
        expediente.area_derecho = AreaDerecho(self.combo_area.currentData())
        expediente.juzgado = self.campo_juzgado.text().strip() or None
        expediente.fecha_corte_default = fecha_corte

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

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
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

            boton_editar = QPushButton("Editar")
            boton_editar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._editar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 4, boton_editar)

            boton_eliminar = QPushButton("Eliminar")
            boton_eliminar.setIcon(icon("delete"))
            boton_eliminar.setProperty("class", "destructive")
            boton_eliminar.clicked.connect(
                lambda _checked=False, id_=expediente.id: self._eliminar_expediente(id_)
            )
            self.tabla.setCellWidget(fila, 5, boton_eliminar)

            self._expediente_ids_por_fila.append(expediente.id)
        session.close()

    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = ExpedienteFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila[fila])

    def _editar_expediente(self, expediente_id: int) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        dialogo = ExpedienteFormDialog(self, expediente=expediente)
        session.close()
        if dialogo.exec():
            self.refrescar()

    def _eliminar_expediente(self, expediente_id: int) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        radicado = expediente.radicado
        session.close()

        respuesta = QMessageBox.question(
            self,
            "Eliminar expediente",
            f"¿Eliminar el expediente '{radicado}'? Se borraran tambien todas sus "
            "obligaciones, abonos y registros de auditoria asociados. Esta accion "
            "no se puede deshacer.",
        )
        if respuesta != QMessageBox.StandardButton.Yes:
            return

        texto, ok = QInputDialog.getText(
            self,
            "Confirmar eliminacion",
            f"Escribe el radicado '{radicado}' para confirmar:",
        )
        if not ok or texto.strip() != radicado:
            QMessageBox.warning(
                self, "Eliminacion cancelada", "El radicado no coincide. No se elimino el expediente."
            )
            return

        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        session.delete(expediente)
        session.commit()
        session.close()

        self.refrescar()
