from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.exceptions import AreaNoImplementadaError, TasaUsurariaError
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import Expediente


class ExpedienteDetallePage(QWidget):
    def __init__(self, on_liquidado=None):
        super().__init__()
        self._on_liquidado = on_liquidado
        self._expediente_id = None
        self._obligacion_ids_por_fila = []

        self.tabla_obligaciones = QTableWidget(0, 3)
        self.tabla_obligaciones.setHorizontalHeaderLabels(["Concepto", "Tipo", "Valor"])
        boton_agregar_obligacion = QPushButton("Agregar obligacion")
        boton_agregar_obligacion.clicked.connect(self._abrir_dialogo_obligacion)

        grupo_obligaciones = QGroupBox("Obligaciones")
        layout_obligaciones = QVBoxLayout()
        layout_obligaciones.addWidget(boton_agregar_obligacion)
        layout_obligaciones.addWidget(self.tabla_obligaciones)
        grupo_obligaciones.setLayout(layout_obligaciones)

        self.tabla_abonos = QTableWidget(0, 3)
        self.tabla_abonos.setHorizontalHeaderLabels(["Fecha", "Monto", "Referencia"])
        boton_agregar_abono = QPushButton("Agregar abono")
        boton_agregar_abono.clicked.connect(self._abrir_dialogo_abono)

        grupo_abonos = QGroupBox("Abonos")
        layout_abonos = QVBoxLayout()
        layout_abonos.addWidget(boton_agregar_abono)
        layout_abonos.addWidget(self.tabla_abonos)
        grupo_abonos.setLayout(layout_abonos)

        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)

        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(columnas)
        layout_principal.addWidget(boton_liquidar)
        self.setLayout(layout_principal)

    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        self._refrescar_obligaciones()
        self._refrescar_abonos()

    def _refrescar_obligaciones(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        obligaciones = list(expediente.obligaciones)

        self.tabla_obligaciones.setRowCount(len(obligaciones))
        self._obligacion_ids_por_fila = []
        for fila, obligacion in enumerate(obligaciones):
            self.tabla_obligaciones.setItem(fila, 0, QTableWidgetItem(obligacion.concepto))
            self.tabla_obligaciones.setItem(fila, 1, QTableWidgetItem(obligacion.tipo.value))
            self.tabla_obligaciones.setItem(fila, 2, QTableWidgetItem(str(obligacion.valor)))
            self._obligacion_ids_por_fila.append(obligacion.id)
        session.close()

    def _refrescar_abonos(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        abonos = [abono for obligacion in expediente.obligaciones for abono in obligacion.abonos]

        self.tabla_abonos.setRowCount(len(abonos))
        for fila, abono in enumerate(abonos):
            self.tabla_abonos.setItem(fila, 0, QTableWidgetItem(abono.fecha.isoformat()))
            self.tabla_abonos.setItem(fila, 1, QTableWidgetItem(str(abono.monto)))
            self.tabla_abonos.setItem(fila, 2, QTableWidgetItem(abono.referencia or ""))
        session.close()

    def _abrir_dialogo_obligacion(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        area = expediente.area_derecho.value
        session.close()

        dialogo = ObligacionFormDialog(expediente_id=self._expediente_id, area=area, parent=self)
        if dialogo.exec():
            self._refrescar_obligaciones()

    def _abrir_dialogo_abono(self) -> None:
        fila_seleccionada = self.tabla_obligaciones.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(self, "Seleccion requerida", "Selecciona una obligacion antes de agregar un abono.")
            return

        obligacion_id = self._obligacion_ids_por_fila[fila_seleccionada]
        dialogo = AbonoFormDialog(obligacion_id=obligacion_id, parent=self)
        if dialogo.exec():
            self._refrescar_abonos()

    def _liquidar(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        obligaciones = list(expediente.obligaciones)
        abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
        fecha_corte = expediente.fecha_corte_default
        area = expediente.area_derecho.value
        session.close()

        try:
            estrategia = AreaRegistry.get_strategy(area)
            resultado = estrategia.liquidar(obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte)
        except AreaNoImplementadaError as error:
            QMessageBox.warning(self, "Area no implementada", str(error))
            return
        except TasaUsurariaError as error:
            QMessageBox.warning(self, "Tasa usuraria", str(error))
            return
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
