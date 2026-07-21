from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.services.parametro_service import (
    CATALOGO_PARAMETROS,
    ModoResolucion,
    agregar_valor,
    valor_vigente_hoy,
)


class ParametroFormDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Agregar valor de parametro")

        self.combo_clave = QComboBox()
        for clave, info in CATALOGO_PARAMETROS.items():
            self.combo_clave.addItem(f"{info.descripcion} ({clave})", userData=clave)

        self.campo_valor = QLineEdit()
        self.campo_vigente_desde = QDateEdit(QDate.currentDate())
        self.campo_vigente_desde.setCalendarPopup(True)
        self.campo_vigente_hasta = QDateEdit(QDate.currentDate())
        self.campo_vigente_hasta.setCalendarPopup(True)
        self.campo_usuario = QLineEdit()
        self.campo_motivo = QLineEdit()

        boton_guardar = QPushButton("Guardar")
        boton_guardar.clicked.connect(self._guardar_y_cerrar)

        layout = QFormLayout()
        layout.addRow("Parametro", self.combo_clave)
        layout.addRow("Valor", self.campo_valor)
        layout.addRow("Vigente desde", self.campo_vigente_desde)
        layout.addRow("Vigente hasta", self.campo_vigente_hasta)
        layout.addRow("Usuario", self.campo_usuario)
        layout.addRow("Motivo (opcional)", self.campo_motivo)
        layout.addRow(boton_guardar)
        self.setLayout(layout)

        self.combo_clave.currentIndexChanged.connect(self._actualizar_visibilidad_vigente_hasta)
        self._actualizar_visibilidad_vigente_hasta()

    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        self.campo_vigente_hasta.setVisible(info.modo == ModoResolucion.TRAMO_CERRADO)

    def guardar(self):
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]

        try:
            valor = Decimal(self.campo_valor.text())
        except InvalidOperation as error:
            raise ValueError("El valor debe ser un numero valido.") from error
        if not valor.is_finite():
            raise ValueError("El valor debe ser un numero finito.")

        usuario = self.campo_usuario.text().strip()
        if not usuario:
            raise ValueError("El campo Usuario es obligatorio.")

        qdate_desde = self.campo_vigente_desde.date()
        vigente_desde = date(qdate_desde.year(), qdate_desde.month(), qdate_desde.day())

        vigente_hasta = None
        if info.modo == ModoResolucion.TRAMO_CERRADO:
            qdate_hasta = self.campo_vigente_hasta.date()
            vigente_hasta = date(qdate_hasta.year(), qdate_hasta.month(), qdate_hasta.day())
            if vigente_hasta < vigente_desde:
                raise ValueError("'Vigente hasta' no puede ser anterior a 'Vigente desde'.")

        motivo = self.campo_motivo.text().strip() or None

        return agregar_valor(
            clave=clave,
            valor=valor,
            vigente_desde=vigente_desde,
            usuario=usuario,
            motivo=motivo,
            vigente_hasta=vigente_hasta,
        )

    def _guardar_y_cerrar(self) -> None:
        try:
            self.guardar()
            self.accept()
        except ValueError as error:
            QMessageBox.warning(self, "Datos invalidos", str(error))


class ParametrosView(QWidget):
    def __init__(self):
        super().__init__()
        self._claves_por_fila: list[str] = []

        columnas = ["Categoria", "Parametro", "Valor vigente hoy", "Vigente desde"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        boton_agregar = QPushButton("+ Agregar valor nuevo")
        boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(boton_agregar)

        layout = QVBoxLayout()
        layout.addLayout(botones)
        layout.addWidget(self.tabla)
        self.setLayout(layout)

        self.refrescar()

    def refrescar(self) -> None:
        claves = list(CATALOGO_PARAMETROS.items())
        self.tabla.setRowCount(len(claves))
        self._claves_por_fila = []
        for fila_idx, (clave, info) in enumerate(claves):
            vigente = valor_vigente_hoy(clave)
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(info.categoria))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(info.descripcion))
            self.tabla.setItem(
                fila_idx, 2, QTableWidgetItem(str(vigente.valor) if vigente else "(sin dato)")
            )
            self.tabla.setItem(
                fila_idx, 3,
                QTableWidgetItem(vigente.vigente_desde.isoformat() if vigente else ""),
            )
            self._claves_por_fila.append(clave)

    def _abrir_dialogo_agregar(self) -> None:
        pass  # implementado en la siguiente tarea
