from datetime import date
from decimal import Decimal, InvalidOperation

from PySide6.QtCore import QDate
from PySide6.QtGui import QKeySequence, QShortcut
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
    historial,
    valor_vigente_hoy,
)
from app.views.form_utils import set_row_visible
from app.views.icons import icon


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

        self.boton_guardar = QPushButton("Guardar")
        self.boton_guardar.setIcon(icon("save"))
        self.boton_guardar.setProperty("class", "primary")
        self.boton_guardar.clicked.connect(self._guardar_y_cerrar)
        # Ctrl+S = guardar (Sprint 32). Esc = cancelar ya viene gratis de
        # QDialog.keyPressEvent() (reject() por defecto) -- no requiere codigo aqui.
        self.atajo_guardar = QShortcut(QKeySequence("Ctrl+S"), self)
        self.atajo_guardar.activated.connect(self._guardar_y_cerrar)

        # Guardado como atributo (en vez de variable local `layout`) para que
        # _actualizar_visibilidad_vigente_hasta pueda ocultar la fila completa
        # (etiqueta + campo) con set_row_visible (Sprint 39) en vez de solo el
        # QDateEdit.
        self._layout_formulario = QFormLayout()
        self._layout_formulario.addRow("Parametro", self.combo_clave)
        self._layout_formulario.addRow("Valor", self.campo_valor)
        self._layout_formulario.addRow("Vigente desde", self.campo_vigente_desde)
        self._layout_formulario.addRow("Vigente hasta", self.campo_vigente_hasta)
        self._layout_formulario.addRow("Usuario", self.campo_usuario)
        self._layout_formulario.addRow("Motivo (opcional)", self.campo_motivo)
        self._layout_formulario.addRow(self.boton_guardar)
        self.setLayout(self._layout_formulario)

        self.combo_clave.currentIndexChanged.connect(self._actualizar_visibilidad_vigente_hasta)
        self._actualizar_visibilidad_vigente_hasta()

    def _actualizar_visibilidad_vigente_hasta(self) -> None:
        clave = self.combo_clave.currentData()
        info = CATALOGO_PARAMETROS[clave]
        # set_row_visible (no campo_vigente_hasta.setVisible() suelto) para que la
        # etiqueta "Vigente hasta" generada por addRow(str, widget) se oculte junto
        # con el campo -- de lo contrario queda una fila huerfana (Sprint 39).
        set_row_visible(
            self._layout_formulario,
            self.campo_vigente_hasta,
            info.modo == ModoResolucion.TRAMO_CERRADO,
        )

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


class HistorialParametroDialog(QDialog):
    def __init__(self, clave: str, parent=None):
        super().__init__(parent)
        info = CATALOGO_PARAMETROS[clave]
        self.setWindowTitle(f"Historial: {info.descripcion}")

        columnas = ["Valor", "Vigente desde", "Vigente hasta", "Usuario", "Motivo"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)

        filas = historial(clave)
        self.tabla.setRowCount(len(filas))
        for fila_idx, fila in enumerate(filas):
            self.tabla.setItem(fila_idx, 0, QTableWidgetItem(str(fila.valor)))
            self.tabla.setItem(fila_idx, 1, QTableWidgetItem(fila.vigente_desde.isoformat()))
            self.tabla.setItem(
                fila_idx, 2,
                QTableWidgetItem(fila.vigente_hasta.isoformat() if fila.vigente_hasta else ""),
            )
            self.tabla.setItem(fila_idx, 3, QTableWidgetItem(fila.usuario))
            self.tabla.setItem(fila_idx, 4, QTableWidgetItem(fila.motivo or ""))

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        self.setLayout(layout)


class ParametrosView(QWidget):
    def __init__(self):
        super().__init__()
        self._claves_por_fila: list[str] = []

        columnas = ["Categoria", "Parametro", "Valor vigente hoy", "Vigente desde"]
        self.tabla = QTableWidget(0, len(columnas))
        self.tabla.setHorizontalHeaderLabels(columnas)
        self.tabla.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla.cellDoubleClicked.connect(self._abrir_historial)

        self.boton_agregar = QPushButton("+ Agregar valor nuevo")
        self.boton_agregar.setProperty("class", "primary")
        self.boton_agregar.clicked.connect(self._abrir_dialogo_agregar)

        botones = QHBoxLayout()
        botones.addWidget(self.boton_agregar)

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
        dialogo = ParametroFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_historial(self, fila: int, _columna: int) -> None:
        clave = self._claves_por_fila[fila]
        HistorialParametroDialog(clave, self).exec()
