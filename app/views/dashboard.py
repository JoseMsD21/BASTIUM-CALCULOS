from datetime import date, timedelta

from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core.constants import AREAS_DERECHO
from app.core.exceptions import ParametroNoDisponibleError
from app.engine.audit.service import historial_de_expediente
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from database.models import AuditLog, Expediente

DIAS_ALERTA_VENCIMIENTO = 90
MAX_LIQUIDACIONES_RECIENTES = 10


class DashboardView(QWidget):
    """Pantalla de inicio (Sprint 33): resumen agregado de todos los expedientes,
    en vez de abrir directo al listado plano de expedientes
    (`app/views/expedientes.py`, que sigue existiendo como pantalla "expedientes",
    alcanzable desde aquí con el botón "Ver todos los expedientes").

    Carga sus datos de forma síncrona -- sin `TareaEnHilo`/`QThreadPool` (Sprint
    26) -- porque son consultas SQL livianas más aritmética de fechas sobre, como
    mucho, unas pocas centenas de expedientes/obligaciones: no es la clase de
    operación pesada (`liquidar()`, exportar PDF/Word) que el Sprint 26 sacó del
    hilo de UI. Ver la sección Architecture del plan de este sprint para el
    detalle completo de esta decisión.
    """

    def __init__(self, on_expediente_abierto=None, on_ver_expedientes=None):
        super().__init__()
        self._on_expediente_abierto = on_expediente_abierto
        self._on_ver_expedientes = on_ver_expedientes

        self.boton_ver_expedientes = QPushButton("Ver todos los expedientes")
        self.boton_ver_expedientes.setProperty("class", "primary")
        self.boton_ver_expedientes.clicked.connect(self._emitir_ver_expedientes)

        self.etiqueta_total_expedientes = QLabel()

        self.tabla_por_area = QTableWidget(len(AREAS_DERECHO), 2)
        self.tabla_por_area.setHorizontalHeaderLabels(["Área", "Expedientes"])

        grupo_resumen = QGroupBox("Expedientes por área")
        layout_resumen = QVBoxLayout()
        layout_resumen.addWidget(self.etiqueta_total_expedientes)
        layout_resumen.addWidget(self.tabla_por_area)
        grupo_resumen.setLayout(layout_resumen)

        self.tabla_alertas = QTableWidget(0, 4)
        self.tabla_alertas.setHorizontalHeaderLabels(
            ["Radicado", "Concepto", "Fecha límite", "Estado"]
        )
        self.tabla_alertas.cellDoubleClicked.connect(self._abrir_expediente_de_alerta)
        self._expediente_ids_por_fila_alerta: list[int] = []

        grupo_alertas = QGroupBox("Plazos próximos a vencer")
        layout_alertas = QVBoxLayout()
        layout_alertas.addWidget(self.tabla_alertas)
        grupo_alertas.setLayout(layout_alertas)

        self.tabla_actividad = QTableWidget(0, 3)
        self.tabla_actividad.setHorizontalHeaderLabels(["Fecha", "Radicado", "Área"])

        grupo_actividad = QGroupBox("Actividad reciente")
        layout_actividad = QVBoxLayout()
        layout_actividad.addWidget(self.tabla_actividad)
        grupo_actividad.setLayout(layout_actividad)

        layout_cta = QHBoxLayout()
        layout_cta.addStretch()
        layout_cta.addWidget(self.boton_ver_expedientes)

        layout_principal = QVBoxLayout()
        layout_principal.addLayout(layout_cta)
        layout_principal.addWidget(grupo_resumen)
        layout_principal.addWidget(grupo_alertas)
        layout_principal.addWidget(grupo_actividad)
        self.setLayout(layout_principal)

        self.refrescar()

    def _emitir_ver_expedientes(self) -> None:
        if self._on_ver_expedientes:
            self._on_ver_expedientes()

    def _abrir_expediente_de_alerta(self, fila: int, _columna: int) -> None:
        if self._on_expediente_abierto:
            self._on_expediente_abierto(self._expediente_ids_por_fila_alerta[fila])

    def refrescar(self, hoy: date | None = None) -> None:
        hoy = hoy or date.today()
        session = session_module.get_session()
        expedientes = session.query(Expediente).all()

        self._refrescar_conteo_por_area(expedientes)
        self._refrescar_alertas_vencimiento(expedientes, hoy)
        self._refrescar_actividad_reciente(session, expedientes)

        session.close()

    def _refrescar_conteo_por_area(self, expedientes: list[Expediente]) -> None:
        self.etiqueta_total_expedientes.setText(f"Total de expedientes: {len(expedientes)}")

        conteo_por_area = dict.fromkeys((codigo for codigo, _et, _hab in AREAS_DERECHO), 0)
        for expediente in expedientes:
            conteo_por_area[expediente.area_derecho.value] += 1

        for fila, (codigo, etiqueta, _habilitada) in enumerate(AREAS_DERECHO):
            self.tabla_por_area.setItem(fila, 0, QTableWidgetItem(etiqueta))
            self.tabla_por_area.setItem(
                fila, 1, QTableWidgetItem(str(conteo_por_area[codigo]))
            )

    def _refrescar_alertas_vencimiento(
        self, expedientes: list[Expediente], hoy: date
    ) -> None:
        """Alerta si la prescripción de la acción ejecutiva (`TipoAccion.EJECUTIVA`
        -- el mismo default que usa `filtrar_cuotas_prescritas` en
        `app/engine/temporal/prescripcion.py`, ver Architecture del plan de este
        sprint) de alguna obligación no pagada cae dentro de los próximos
        `DIAS_ALERTA_VENCIMIENTO` días, o ya venció."""
        limite = hoy + timedelta(days=DIAS_ALERTA_VENCIMIENTO)
        alertas = []
        for expediente in expedientes:
            for obligacion in expediente.obligaciones:
                if obligacion.pagada:
                    continue
                try:
                    fecha_limite = calcular_prescripcion(
                        obligacion.fecha_origen, TipoAccion.EJECUTIVA
                    )
                except ParametroNoDisponibleError:
                    # Sin PRESCRIPCION_EJECUTIVA_MESES configurado en Parametros no
                    # se puede calcular la fecha limite de esta obligacion -- se
                    # omite de las alertas en vez de tumbar todo el dashboard.
                    continue
                if fecha_limite <= limite:
                    dias_restantes = (fecha_limite - hoy).days
                    if dias_restantes < 0:
                        estado = "Vencido"
                    else:
                        estado = f"Vence en {dias_restantes} días"
                    alertas.append((expediente, obligacion, fecha_limite, estado))

        alertas.sort(key=lambda item: item[2])

        self.tabla_alertas.setRowCount(len(alertas))
        self._expediente_ids_por_fila_alerta = []
        for fila, (expediente, obligacion, fecha_limite, estado) in enumerate(alertas):
            self.tabla_alertas.setItem(fila, 0, QTableWidgetItem(expediente.radicado))
            self.tabla_alertas.setItem(fila, 1, QTableWidgetItem(obligacion.concepto))
            self.tabla_alertas.setItem(fila, 2, QTableWidgetItem(fecha_limite.isoformat()))
            self.tabla_alertas.setItem(fila, 3, QTableWidgetItem(estado))
            self._expediente_ids_por_fila_alerta.append(expediente.id)

    def _refrescar_actividad_reciente(
        self, session, expedientes: list[Expediente]
    ) -> None:
        """Últimas liquidaciones ejecutadas en cualquier expediente, más recientes
        primero -- reutiliza `historial_de_expediente` (Sprint 9,
        `app/engine/audit/service.py`) una vez por expediente y fusiona/recorta el
        resultado combinado, en vez de duplicar la consulta a `AuditLog` aquí."""
        registros: list[AuditLog] = []
        for expediente in expedientes:
            registros.extend(historial_de_expediente(session, expediente.id))
        registros.sort(key=lambda log: log.fecha_ejecucion, reverse=True)
        registros = registros[:MAX_LIQUIDACIONES_RECIENTES]

        self.tabla_actividad.setRowCount(len(registros))
        for fila, registro in enumerate(registros):
            self.tabla_actividad.setItem(
                fila,
                0,
                QTableWidgetItem(registro.fecha_ejecucion.strftime("%Y-%m-%d %H:%M")),
            )
            self.tabla_actividad.setItem(
                fila, 1, QTableWidgetItem(registro.expediente.radicado)
            )
            self.tabla_actividad.setItem(fila, 2, QTableWidgetItem(registro.area_derecho))
