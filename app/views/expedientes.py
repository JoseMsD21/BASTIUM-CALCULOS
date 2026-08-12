from datetime import date

from PySide6.QtCore import QDate, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core import theme_colors as colores
from app.core.constants import AREAS_DERECHO
from app.views.form_utils import agregar_ayuda, hacer_redimensionable
from app.views.icons import icon
from database.models import AreaDerecho, Expediente


class ExpedienteFormDialog(QDialog):
    def __init__(self, parent=None, expediente: Expediente | None = None):
        super().__init__(parent)
        hacer_redimensionable(self)
        self._expediente_id = expediente.id if expediente else None
        self.setWindowTitle("Editar expediente" if expediente else "Nuevo expediente")

        self.campo_radicado = QLineEdit()
        self.campo_radicado.setToolTip(
            "Numero de radicado judicial del proceso, tal como aparece en el expediente "
            "fisico o electronico del despacho."
        )
        self.campo_demandante = QLineEdit()
        self.campo_demandante.setToolTip("Nombre completo de la parte demandante (o accionante).")
        self.campo_demandado = QLineEdit()
        self.campo_demandado.setToolTip("Nombre completo de la parte demandada (o accionada).")
        self.campo_juzgado = QLineEdit()
        self.campo_juzgado.setToolTip("Despacho judicial que conoce del proceso (opcional).")
        self.campo_fecha_corte = QDateEdit(QDate.currentDate())
        self.campo_fecha_corte.setCalendarPopup(True)
        self.campo_fecha_corte.setToolTip(
            "Fecha hasta la que se calculan los intereses por defecto al liquidar este expediente."
        )

        self.combo_area = QComboBox()
        self.combo_area.setToolTip(
            "Area del derecho del proceso -- determina que campos y reglas de calculo "
            "aplican al crear obligaciones dentro de este expediente."
        )
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
        layout.addRow("Radicado", self.campo_radicado)
        layout.addRow("Demandante", self.campo_demandante)
        layout.addRow("Demandado", self.campo_demandado)
        layout.addRow("Area del derecho", self.combo_area)
        layout.addRow("Juzgado", self.campo_juzgado)
        # "Fecha de corte" recibe ademas el icono (i) explicito (Sprint 59, helper
        # compartido agregar_ayuda) -- es el campo con mayor efecto no obvio del
        # formulario: fija hasta que dia se calculan los intereses por defecto al
        # liquidar, sin que el usuario tenga que abrir el dialogo de liquidacion para
        # descubrirlo.
        self._contenedor_campo_fecha_corte = agregar_ayuda(
            layout,
            "Fecha de corte",
            self.campo_fecha_corte,
            tooltip=(
                "Fecha hasta la que se calculan los intereses por defecto al liquidar "
                "este expediente."
            ),
            ejemplo=(
                "si el corte es 2026-06-30, los intereses se calculan hasta ese dia "
                "salvo que se indique otra fecha al momento de liquidar."
            ),
        )
        layout.addRow(self.boton_guardar)
        self.setLayout(layout)

        self._expediente_id_creado = None

        self.campo_radicado.textChanged.connect(self._validar_radicado_en_tiempo_real)

        # Orden de tabulacion explicito (Sprint 37), siguiendo el orden visual de
        # arriba hacia abajo del formulario (mismo orden en que se llamo addRow() mas
        # arriba). QFormLayout ya encadena el tab order automaticamente entre sus
        # propias filas siguiendo ese mismo orden, pero se fija aqui de forma
        # explicita para no depender de ese comportamiento implicito si el formulario
        # cambia en el futuro.
        orden = [
            self.campo_radicado,
            self.campo_demandante,
            self.campo_demandado,
            self.combo_area,
            self.campo_juzgado,
            self.campo_fecha_corte,
            self.boton_guardar,
        ]
        for anterior, siguiente in zip(orden, orden[1:], strict=False):
            self.setTabOrder(anterior, siguiente)

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

    def _marcar_campo_invalido(self, campo: QLineEdit, mensaje: str) -> None:
        campo.setProperty("class", "invalid")
        campo.setToolTip(mensaje)
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _marcar_campo_valido(self, campo: QLineEdit, tooltip_original: str) -> None:
        campo.setProperty("class", "")
        campo.setToolTip(tooltip_original)
        campo.style().unpolish(campo)
        campo.style().polish(campo)

    def _validar_radicado_en_tiempo_real(self) -> None:
        tooltip_original = (
            "Numero de radicado judicial del proceso, tal como aparece en el expediente "
            "fisico o electronico del despacho."
        )
        if not self.campo_radicado.text().strip():
            self._marcar_campo_invalido(self.campo_radicado, "El radicado es obligatorio.")
        else:
            self._marcar_campo_valido(self.campo_radicado, tooltip_original)

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
        self._estado_vacio_es_por_filtros = False

        self.campo_busqueda = QLineEdit()
        self.campo_busqueda.setPlaceholderText("Buscar por radicado, demandante o demandado...")
        self.campo_busqueda.textChanged.connect(self.refrescar)

        self.combo_filtro_area = QComboBox()
        self.combo_filtro_area.addItem("Todas las areas", userData="")
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            self.combo_filtro_area.addItem(etiqueta, userData=codigo)
        self.combo_filtro_area.currentIndexChanged.connect(self.refrescar)

        layout_filtros = QHBoxLayout()
        layout_filtros.addWidget(self.campo_busqueda)
        layout_filtros.addWidget(self.combo_filtro_area)

        self.tabla = QTableWidget(0, 6)
        self.tabla.setHorizontalHeaderLabels(
            ["Radicado", "Demandante", "Demandado", "Area", "Editar", "Eliminar"]
        )
        # QHeaderView trae un sortIndicatorSection por defecto de 0 (no -1) aunque el
        # usuario nunca haya hecho clic en un encabezado: al activar setSortingEnabled(True)
        # por primera vez, Qt aplica de inmediato un sort "fantasma" por esa columna. Se
        # limpia el indicador aqui, una sola vez, para que la tabla arranque en el orden de
        # insercion y solo se reordene cuando el usuario realmente hace clic en un encabezado.
        self.tabla.horizontalHeader().setSortIndicator(-1, Qt.SortOrder.AscendingOrder)
        self.tabla.cellDoubleClicked.connect(self._abrir_seleccionado)

        self.boton_nuevo = QPushButton("Nuevo expediente")
        self.boton_nuevo.setProperty("class", "primary")
        self.boton_nuevo.clicked.connect(self._abrir_dialogo_nuevo)

        self.etiqueta_estado_vacio = QLabel()
        self.etiqueta_estado_vacio.setWordWrap(True)
        self.etiqueta_estado_vacio.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.etiqueta_estado_vacio.setStyleSheet(
            f"color: {colores.TEXTO_SECUNDARIO}; padding: 24px; font-size: 11pt;"
        )

        self.boton_accion_estado_vacio = QPushButton()
        self.boton_accion_estado_vacio.setProperty("class", "primary")
        self.boton_accion_estado_vacio.clicked.connect(self._accion_estado_vacio)

        layout_estado_vacio = QVBoxLayout()
        layout_estado_vacio.addWidget(self.etiqueta_estado_vacio)
        layout_estado_vacio.addWidget(
            self.boton_accion_estado_vacio, alignment=Qt.AlignmentFlag.AlignCenter
        )
        self.widget_estado_vacio = QWidget()
        self.widget_estado_vacio.setLayout(layout_estado_vacio)
        self.widget_estado_vacio.setVisible(False)

        layout = QVBoxLayout()
        layout.addWidget(self.boton_nuevo)
        layout.addLayout(layout_filtros)
        layout.addWidget(self.tabla)
        layout.addWidget(self.widget_estado_vacio)
        self.setLayout(layout)

        self._expediente_ids_por_fila = []
        self.refrescar()

    def refrescar(self) -> None:
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        expedientes_filtrados = self._filtrar(expedientes)

        # Se desactiva el ordenamiento mientras se puebla la tabla: con
        # setSortingEnabled(True) ya activo, cada setItem() dispararia un
        # re-ordenamiento a mitad de poblado y mezclaria filas con datos
        # incompletos (gotcha conocido de QTableWidget).
        self.tabla.setSortingEnabled(False)
        self.tabla.setRowCount(len(expedientes_filtrados))
        self._expediente_ids_por_fila = []
        for fila, expediente in enumerate(expedientes_filtrados):
            item_radicado = QTableWidgetItem(expediente.radicado)
            # El id se guarda como UserRole en el item de la columna 0 (no en
            # una lista Python indexada por fila) porque el item -- con todos
            # sus roles de datos -- se mueve junto con la fila cuando el
            # usuario ordena por columna; una lista indexada por posicion no.
            item_radicado.setData(Qt.ItemDataRole.UserRole, expediente.id)
            self.tabla.setItem(fila, 0, item_radicado)
            self.tabla.setItem(fila, 1, QTableWidgetItem(expediente.demandante))
            self.tabla.setItem(fila, 2, QTableWidgetItem(expediente.demandado))
            self.tabla.setItem(fila, 3, QTableWidgetItem(expediente.area_derecho.value))

            boton_editar = QPushButton("Editar")
            boton_editar.setProperty("class", "secondary")
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
        self.tabla.setSortingEnabled(True)
        total_en_base_de_datos = len(expedientes)
        session.close()

        self._actualizar_estado_vacio(
            total_en_base_de_datos=total_en_base_de_datos,
            hay_resultados=bool(expedientes_filtrados),
        )

    def _actualizar_estado_vacio(
        self, *, total_en_base_de_datos: int, hay_resultados: bool
    ) -> None:
        if hay_resultados:
            self.tabla.setVisible(True)
            self.widget_estado_vacio.setVisible(False)
            return

        self.tabla.setVisible(False)
        self.widget_estado_vacio.setVisible(True)

        if total_en_base_de_datos == 0:
            self._estado_vacio_es_por_filtros = False
            self.etiqueta_estado_vacio.setText(
                "Todavia no hay expedientes cargados.\nCrea el primero para empezar a liquidar."
            )
            self.boton_accion_estado_vacio.setText("Crear expediente")
        else:
            self._estado_vacio_es_por_filtros = True
            self.etiqueta_estado_vacio.setText(
                "Ningun expediente coincide con la busqueda o el filtro actual."
            )
            self.boton_accion_estado_vacio.setText("Limpiar filtros")

    def _accion_estado_vacio(self) -> None:
        if self._estado_vacio_es_por_filtros:
            self._limpiar_filtros()
        else:
            self._abrir_dialogo_nuevo()

    def _limpiar_filtros(self) -> None:
        self.campo_busqueda.blockSignals(True)
        self.combo_filtro_area.blockSignals(True)
        self.campo_busqueda.clear()
        self.combo_filtro_area.setCurrentIndex(0)
        self.campo_busqueda.blockSignals(False)
        self.combo_filtro_area.blockSignals(False)
        self.refrescar()

    def _filtrar(self, expedientes: list[Expediente]) -> list[Expediente]:
        texto_busqueda = self.campo_busqueda.text().strip().lower()
        area_seleccionada = self.combo_filtro_area.currentData()

        def _coincide(expediente: Expediente) -> bool:
            if area_seleccionada and expediente.area_derecho.value != area_seleccionada:
                return False
            if texto_busqueda:
                campos = (expediente.radicado, expediente.demandante, expediente.demandado)
                if not any(texto_busqueda in (campo or "").lower() for campo in campos):
                    return False
            return True

        return [expediente for expediente in expedientes if _coincide(expediente)]

    def _abrir_dialogo_nuevo(self) -> None:
        dialogo = ExpedienteFormDialog(self)
        if dialogo.exec():
            self.refrescar()

    def _abrir_seleccionado(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            expediente_id = self.tabla.item(fila, 0).data(Qt.ItemDataRole.UserRole)
            self._on_expediente_abierto(expediente_id)

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
                self,
                "Eliminacion cancelada",
                "El radicado no coincide. No se elimino el expediente.",
            )
            return

        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        session.delete(expediente)
        session.commit()
        session.close()

        self.refrescar()
