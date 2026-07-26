from PySide6.QtWidgets import (
    QAbstractItemView,
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
from app.core.exceptions import (
    AreaNoImplementadaError,
    CuotaLitisExcedeTopeError,
    ParametroNoDisponibleError,
    TasaUsurariaError,
    UVTNoDisponibleError,
)
from app.engine.audit.service import historial_de_expediente, reconstruir_liquidacion, registrar_liquidacion
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.eventos_laborales import EventoLaboralFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Expediente


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

        self.tabla_eventos_laborales = QTableWidget(0, 3)
        self.tabla_eventos_laborales.setHorizontalHeaderLabels(["Tipo", "Fecha inicio", "Fecha fin"])
        boton_agregar_evento_laboral = QPushButton("Agregar evento")
        boton_agregar_evento_laboral.clicked.connect(self._abrir_dialogo_evento_laboral)

        self.grupo_eventos_laborales = QGroupBox("Eventos contractuales")
        layout_eventos_laborales = QVBoxLayout()
        layout_eventos_laborales.addWidget(boton_agregar_evento_laboral)
        layout_eventos_laborales.addWidget(self.tabla_eventos_laborales)
        self.grupo_eventos_laborales.setLayout(layout_eventos_laborales)

        boton_liquidar = QPushButton("Liquidar")
        boton_liquidar.clicked.connect(self._liquidar)

        self._audit_log_ids_por_fila = []
        self.tabla_historial = QTableWidget(0, 4)
        self.tabla_historial.setHorizontalHeaderLabels(
            ["Fecha ejecución", "Usuario", "Área", "Fecha corte"]
        )
        self.tabla_historial.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabla_historial.cellDoubleClicked.connect(self._reconstruir_desde_historial)

        grupo_historial = QGroupBox("Historial de auditoría")
        layout_historial = QVBoxLayout()
        layout_historial.addWidget(self.tabla_historial)
        grupo_historial.setLayout(layout_historial)

        columnas = QHBoxLayout()
        columnas.addWidget(grupo_obligaciones)
        columnas.addWidget(grupo_abonos)
        columnas.addWidget(self.grupo_eventos_laborales)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(columnas)
        layout_principal.addWidget(boton_liquidar)
        layout_principal.addWidget(grupo_historial)
        self.setLayout(layout_principal)

    def cargar_expediente(self, expediente_id: int) -> None:
        self._expediente_id = expediente_id
        session = session_module.get_session()
        expediente = session.get(Expediente, expediente_id)
        es_laboral = expediente.area_derecho == AreaDerecho.LABORAL
        session.close()

        self.grupo_eventos_laborales.setVisible(es_laboral)
        self._refrescar_obligaciones()
        self._refrescar_abonos()
        self._refrescar_historial()
        if es_laboral:
            self._refrescar_eventos_laborales()

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

    def _refrescar_eventos_laborales(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        eventos = [
            evento for obligacion in expediente.obligaciones for evento in obligacion.eventos_laborales
        ]

        self.tabla_eventos_laborales.setRowCount(len(eventos))
        for fila, evento in enumerate(eventos):
            self.tabla_eventos_laborales.setItem(fila, 0, QTableWidgetItem(evento.tipo.value))
            self.tabla_eventos_laborales.setItem(fila, 1, QTableWidgetItem(evento.fecha_inicio.isoformat()))
            self.tabla_eventos_laborales.setItem(fila, 2, QTableWidgetItem(evento.fecha_fin.isoformat()))
        session.close()

    def _refrescar_historial(self) -> None:
        session = session_module.get_session()
        historial = historial_de_expediente(session, self._expediente_id)

        self.tabla_historial.setRowCount(len(historial))
        self._audit_log_ids_por_fila = []
        for fila, registro in enumerate(historial):
            self.tabla_historial.setItem(
                fila, 0, QTableWidgetItem(registro.fecha_ejecucion.strftime("%Y-%m-%d %H:%M:%S"))
            )
            self.tabla_historial.setItem(fila, 1, QTableWidgetItem(registro.usuario))
            self.tabla_historial.setItem(fila, 2, QTableWidgetItem(registro.area_derecho))
            self.tabla_historial.setItem(fila, 3, QTableWidgetItem(registro.fecha_corte.isoformat()))
            self._audit_log_ids_por_fila.append(registro.id)
        session.close()

    def _reconstruir_desde_historial(self, fila: int, columna: int) -> None:
        audit_log_id = self._audit_log_ids_por_fila[fila]
        session = session_module.get_session()
        resultado = reconstruir_liquidacion(session, audit_log_id)
        session.close()
        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)

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

    def _abrir_dialogo_evento_laboral(self) -> None:
        fila_seleccionada = self.tabla_obligaciones.currentRow()
        if fila_seleccionada < 0:
            QMessageBox.warning(
                self, "Seleccion requerida",
                "Selecciona una obligacion antes de agregar un evento contractual.",
            )
            return

        obligacion_id = self._obligacion_ids_por_fila[fila_seleccionada]
        dialogo = EventoLaboralFormDialog(obligacion_id=obligacion_id, parent=self)
        if dialogo.exec():
            self._refrescar_eventos_laborales()

    def _liquidar(self) -> None:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        obligaciones = list(expediente.obligaciones)
        abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
        for obligacion in obligaciones:
            list(obligacion.eventos_laborales)  # fuerza el lazy-load antes de session.close()
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
        except CuotaLitisExcedeTopeError as error:
            QMessageBox.warning(self, "Cuota litis excede el tope", str(error))
            return
        except UVTNoDisponibleError as error:
            QMessageBox.warning(self, "UVT no disponible", str(error))
            return
        except ParametroNoDisponibleError as error:
            QMessageBox.warning(self, "Parámetro legal no configurado", str(error))
            return
        except ValueError as error:
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            return

        session = session_module.get_session()
        registrar_liquidacion(
            session,
            expediente_id=self._expediente_id,
            area_derecho=area,
            fecha_corte=fecha_corte,
            resultado=resultado,
        )
        session.close()
        self._refrescar_historial()

        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
