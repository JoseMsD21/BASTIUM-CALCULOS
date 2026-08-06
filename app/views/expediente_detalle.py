from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.exceptions import (
    AreaNoImplementadaError,
    CostasFueraDeRangoError,
    CuotaLitisExcedeTopeError,
    ParametroNoDisponibleError,
    TarifaNoDisponibleError,
    TRMNoDisponibleError,
    UVTNoDisponibleError,
)
from app.engine.audit.service import (
    historial_de_expediente,
    reconstruir_liquidacion,
    registrar_liquidacion,
)
from app.engine.liquidation.registry import AreaRegistry
from app.views.abonos import AbonoFormDialog
from app.views.concurrency import TareaEnHilo
from app.views.eventos_laborales import EventoLaboralFormDialog
from app.views.obligaciones import ObligacionFormDialog
from database.models import AreaDerecho, Expediente


def _liquidar_en_hilo_de_fondo(expediente_id: int):
    """Se ejecuta en el QThreadPool (Sprint 26), no en el hilo de UI.

    Abre y cierra su propia sesion de SQLAlchemy dentro de este mismo hilo -- no
    recibe una sesion ya abierta del hilo principal, porque SQLAlchemy no es
    thread-safe si una sesion se comparte entre hilos.
    """
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligaciones = list(expediente.obligaciones)
    abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
    for obligacion in obligaciones:
        list(obligacion.eventos_laborales)  # fuerza el lazy-load antes de session.close()
    fecha_corte = expediente.fecha_corte_default
    area = expediente.area_derecho.value
    session.close()

    estrategia = AreaRegistry.get_strategy(area)
    resultado = estrategia.liquidar(
        obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte
    )

    session = session_module.get_session()
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho=area,
        fecha_corte=fecha_corte,
        resultado=resultado,
    )
    session.close()
    return resultado


class ExpedienteDetallePage(QWidget):
    liquidacion_finalizada = Signal()

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

        self.boton_liquidar = QPushButton("Liquidar")
        self.boton_liquidar.setProperty("class", "primary")
        self.boton_liquidar.clicked.connect(self._liquidar)

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
        layout_principal.addWidget(self.boton_liquidar)
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
        if not self.boton_liquidar.isEnabled():
            return  # ya hay una liquidacion en curso: evita doble liquidacion concurrente
        self.boton_liquidar.setEnabled(False)

        self._dialogo_progreso_liquidar = QProgressDialog("Liquidando...", None, 0, 0, self)
        self._dialogo_progreso_liquidar.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialogo_progreso_liquidar.setCancelButton(None)
        self._dialogo_progreso_liquidar.setMinimumDuration(0)
        self._dialogo_progreso_liquidar.show()

        self._tarea_liquidar = TareaEnHilo(_liquidar_en_hilo_de_fondo, self._expediente_id)
        self._tarea_liquidar.senales.completada.connect(self._on_liquidar_completado)
        self._tarea_liquidar.senales.fallo.connect(self._on_liquidar_fallo)
        QThreadPool.globalInstance().start(self._tarea_liquidar)

    def _finalizar_liquidacion_en_curso(self) -> None:
        self._dialogo_progreso_liquidar.close()
        self.boton_liquidar.setEnabled(True)

    def _on_liquidar_completado(self, resultado) -> None:
        self._finalizar_liquidacion_en_curso()
        self._refrescar_historial()
        if self._on_liquidado:
            self._on_liquidado(resultado, self._expediente_id)
        self.liquidacion_finalizada.emit()

    def _on_liquidar_fallo(self, error: Exception) -> None:
        self._finalizar_liquidacion_en_curso()
        titulos_por_error = {
            AreaNoImplementadaError: "Area no implementada",
            CuotaLitisExcedeTopeError: "Cuota litis excede el tope",
            CostasFueraDeRangoError: "Costas fuera de rango",
            TarifaNoDisponibleError: "Tarifa de costas no disponible",
            UVTNoDisponibleError: "UVT no disponible",
            TRMNoDisponibleError: "TRM no disponible",
            ParametroNoDisponibleError: "Parámetro legal no configurado",
        }
        for tipo_error, titulo in titulos_por_error.items():
            if isinstance(error, tipo_error):
                QMessageBox.warning(self, titulo, str(error))
                self.liquidacion_finalizada.emit()
                return
        if isinstance(error, ValueError):
            QMessageBox.warning(self, "No se pudo liquidar", str(error))
            self.liquidacion_finalizada.emit()
            return
        # Error genuinamente inesperado (no es un ValueError de dominio conocido): se
        # re-lanza tal cual. Este slot corre en el hilo principal via una senal encolada
        # entre hilos, asi que Qt lo captura con su manejador de excepciones por defecto
        # (imprime el traceback a stderr via sys.excepthook y la app sigue corriendo) en
        # vez de propagarse como una excepcion normal -- mismo comportamiento que tenia
        # el try/except sincrono original para tipos de error no anticipados. Se emite la
        # senal ANTES de relanzar para que liquidacion_finalizada siga siendo un
        # invariante confiable (se emite en TODO camino de salida de este slot, exito o
        # fallo, esperado o no) -- de lo contrario un test que haga
        # qtbot.waitSignal(page.liquidacion_finalizada) alrededor de un error inesperado
        # colgaria hasta el timeout en vez de fallar de forma clara.
        self.liquidacion_finalizada.emit()
        raise error
