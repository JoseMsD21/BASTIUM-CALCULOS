import re
from datetime import date

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressDialog,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

import database.session as session_module
from app.core import theme_colors as colores
from app.core.constants import AREAS_DERECHO
from app.core.formato import formatear_moneda
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from app.services.vista_sensibilidad_indexacion import liquidar_vista_sensibilidad
from app.views.celdas import celda_moneda, celda_porcentaje
from app.views.concurrency import TareaEnHilo
from app.views.fecha_widgets import formatear_fecha
from app.views.icons import icon
from app.views.toast import mostrar_toast
from database.models import Expediente


def _sanitizar_nombre_archivo(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto)


def _construir_datos_reporte_en_hilo_de_fondo(resultado: LiquidationResult, expediente_id: int):
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)

    area_label = expediente.area_derecho.value
    for codigo, etiqueta, _habilitada in AREAS_DERECHO:
        if codigo == expediente.area_derecho.value:
            area_label = etiqueta
            break

    title = f"LIQUIDACIÓN DE OBLIGACIONES — ÁREA {area_label.upper()}"
    encabezado = build_encabezado(
        expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado
    )
    session.close()

    summary = ReportSummaryBuilder().build_summary(resultado)
    table_data = ReportTableBuilder().build_matrix(resultado)
    renta_liquida = ReportSummaryBuilder().build_renta_liquida(resultado)

    return title, encabezado, summary, table_data, renta_liquida


def _generar_pdf_en_hilo_de_fondo(
    resultado: LiquidationResult, expediente_id: int, ruta: str
) -> str:
    """Se ejecuta en el QThreadPool (Sprint 26): construye el reporte y genera el
    PDF fuera del hilo de UI, con su propia sesion de SQLAlchemy."""
    title, encabezado, summary, table_data, renta_liquida = (
        _construir_datos_reporte_en_hilo_de_fondo(resultado, expediente_id)
    )
    JudicialPDFGenerator(ruta).generate(
        title,
        summary,
        table_data,
        encabezado,
        renta_liquida=renta_liquida,
        alertas=resultado.alertas,
    )
    return ruta


def _generar_word_en_hilo_de_fondo(
    resultado: LiquidationResult, expediente_id: int, ruta: str
) -> str:
    """Version Word de _generar_pdf_en_hilo_de_fondo (Sprint 26)."""
    title, encabezado, summary, table_data, renta_liquida = (
        _construir_datos_reporte_en_hilo_de_fondo(resultado, expediente_id)
    )
    WordReportGenerator(ruta).generate(
        title,
        summary,
        table_data,
        encabezado,
        renta_liquida=renta_liquida,
        alertas=resultado.alertas,
    )
    return ruta


class ResultadoLiquidacionView(QWidget):
    exportacion_finalizada = Signal()
    # Sprint 107: se emite al terminar (con exito o con error) cada recalculo de
    # la vista de sensibilidad "Ver con/sin indexación".
    vista_sensibilidad_actualizada = Signal()

    def __init__(self):
        super().__init__()

        # `_resultado` es SIEMPRE la liquidacion oficial (la que se exporta y la que
        # quedo en el AuditLog); la vista de sensibilidad (Sprint 107) nunca lo
        # reemplaza, solo se pinta encima mientras el interruptor esta activo.
        self._resultado = None
        self._expediente_id = None
        self._fecha_corte: date | None = None
        self._exportando = False
        # Contador de solicitudes de recalculo: si el usuario cambia el interruptor
        # antes de que termine un recalculo en curso, la respuesta vieja se descarta.
        self._solicitud_sensibilidad = 0

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            [
                "Fecha",
                "Concepto",
                "Capital base",
                "Tasa %",
                "Interes",
                "Indexacion/Sanciones",
                "Pago",
                "Saldo",
            ]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: $0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: $0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: $0.00")
        # Sprint 79: costas procesales como rubro propio -- no generan interes y se
        # suman en seco al saldo final. Oculta cuando la liquidacion no tiene costas.
        self.etiqueta_costas = QLabel("Costas procesales (no generan interés): $0.00")
        self.etiqueta_costas.setVisible(False)
        # Sprint 100: fruto civil (Art. 964 C.C.) como rubro propio -- ya esta
        # dentro del capital; esta etiqueta solo lo discrimina. Oculta cuando la
        # liquidacion no tiene obligaciones de fruto civil.
        self.etiqueta_fruto_civil = QLabel("Fruto civil causado (sin intereses): $0.00")
        self.etiqueta_fruto_civil.setVisible(False)
        # Sprint 46: el saldo a favor de un sobrepago (Sprint 23, ya calculado
        # correctamente por LiquidationCore) se vuelve visible aqui -- oculto por
        # completo (nada, ni una fila vacia) cuando no hay sobrepago.
        self.etiqueta_saldo_a_favor = QLabel("Saldo a favor del deudor: $0.00")
        self.etiqueta_saldo_a_favor.setVisible(False)

        # Alertas no bloqueantes (Sprint 43, agregado en revision de calidad):
        # LiquidationResult.alertas ("Doble Actualización Prohibida" en Laboral,
        # "Techo de usura alcanzado" en Tributario, etc.) ya se muestran como toast
        # al terminar de liquidar (expediente_detalle.py), pero un toast se
        # desvanece a los 6 segundos -- esta etiqueta las deja visibles de forma
        # durable mientras el resultado siga en pantalla (y tambien al reabrir una
        # liquidacion historica desde el historial de auditoria), mismo criterio que
        # ya usa la fila de una obligacion prescrita (prefijo "⚠", ver mas abajo en
        # mostrar()). Oculta por completo cuando no hay alertas.
        self.etiqueta_alertas = QLabel()
        self.etiqueta_alertas.setWordWrap(True)
        self.etiqueta_alertas.setStyleSheet(f"color: {colores.ADVERTENCIA}; font-weight: bold;")
        self.etiqueta_alertas.setVisible(False)

        self.grupo_renta_liquida = QGroupBox("Depuración de Renta Líquida Gravable")
        self.etiqueta_ingresos_netos = QLabel("Ingresos netos: -")
        self.etiqueta_renta_bruta = QLabel("Renta bruta: -")
        self.etiqueta_renta_liquida = QLabel("Renta líquida: -")
        self.etiqueta_hubo_perdida = QLabel("¿Hubo pérdida líquida?: -")
        self.etiqueta_renta_liquida_gravable = QLabel("Renta líquida gravable: -")
        layout_renta_liquida = QVBoxLayout()
        layout_renta_liquida.addWidget(self.etiqueta_ingresos_netos)
        layout_renta_liquida.addWidget(self.etiqueta_renta_bruta)
        layout_renta_liquida.addWidget(self.etiqueta_renta_liquida)
        layout_renta_liquida.addWidget(self.etiqueta_hubo_perdida)
        layout_renta_liquida.addWidget(self.etiqueta_renta_liquida_gravable)
        self.grupo_renta_liquida.setLayout(layout_renta_liquida)
        self.grupo_renta_liquida.setVisible(False)

        self.boton_exportar_pdf = QPushButton("Exportar a PDF")
        self.boton_exportar_pdf.setIcon(icon("export"))
        self.boton_exportar_pdf.setProperty("class", "primary")
        self.boton_exportar_pdf.clicked.connect(self._exportar_pdf)
        self.boton_exportar_word = QPushButton("Exportar a Word")
        self.boton_exportar_word.setIcon(icon("export"))
        self.boton_exportar_word.setProperty("class", "primary")
        self.boton_exportar_word.clicked.connect(self._exportar_word)

        layout_botones = QHBoxLayout()
        layout_botones.addWidget(self.boton_exportar_pdf)
        layout_botones.addWidget(self.boton_exportar_word)

        # Sprint 107 (respuesta del despacho: implementacion hibrida): interruptor
        # de PRESENTACION "Ver con/sin indexación". El checkbox de la obligacion
        # (ObligacionFormDialog) sigue siendo la intencion juridica guardada; este
        # interruptor solo recalcula en memoria la vista (analisis de sensibilidad o
        # debate pedagogico ante el juez) para todas las obligaciones del
        # expediente, sin escribir nada en la base de datos (ni obligaciones ni
        # AuditLog) -- ver app/services/vista_sensibilidad_indexacion.py. Mientras
        # esta activo, exportar a PDF/Word queda deshabilitado: solo se exporta la
        # liquidacion oficial, nunca la vista de sensibilidad.
        self.check_vista_sensibilidad = QCheckBox("Ver con/sin indexación")
        self.check_vista_sensibilidad.setToolTip(
            "Vista de sensibilidad: recalcula en memoria esta liquidación con la "
            "indexación IPC activada o desactivada para todas las obligaciones. No "
            "modifica las obligaciones ni la liquidación oficial guardada."
        )
        self.check_vista_sensibilidad.setEnabled(False)
        self.check_vista_sensibilidad.toggled.connect(self._on_interruptor_sensibilidad)
        self.selector_indexacion_sensibilidad = QComboBox()
        self.selector_indexacion_sensibilidad.addItem("Sin indexación IPC", False)
        self.selector_indexacion_sensibilidad.addItem("Con indexación IPC", True)
        self.selector_indexacion_sensibilidad.setEnabled(False)
        self.selector_indexacion_sensibilidad.currentIndexChanged.connect(
            self._on_sentido_sensibilidad_cambiado
        )
        layout_sensibilidad = QHBoxLayout()
        layout_sensibilidad.addWidget(self.check_vista_sensibilidad)
        layout_sensibilidad.addWidget(self.selector_indexacion_sensibilidad)
        layout_sensibilidad.addStretch()

        self.etiqueta_vista_sensibilidad = QLabel()
        self.etiqueta_vista_sensibilidad.setWordWrap(True)
        self.etiqueta_vista_sensibilidad.setStyleSheet(
            f"color: {colores.ADVERTENCIA}; font-weight: bold;"
        )
        self.etiqueta_vista_sensibilidad.setVisible(False)

        layout = QVBoxLayout()
        layout.addLayout(layout_sensibilidad)
        layout.addWidget(self.etiqueta_vista_sensibilidad)
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_alertas)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_fruto_civil)
        layout.addWidget(self.etiqueta_costas)
        layout.addWidget(self.etiqueta_saldo_final)
        layout.addWidget(self.etiqueta_saldo_a_favor)
        layout.addWidget(self.grupo_renta_liquida)
        layout.addLayout(layout_botones)
        self.setLayout(layout)

    def mostrar(
        self,
        resultado: LiquidationResult,
        expediente_id: int,
        fecha_corte: date | None = None,
    ) -> None:
        """Muestra la liquidacion OFICIAL. `fecha_corte` (Sprint 107) habilita el
        interruptor "Ver con/sin indexación", que necesita recalcular con la misma
        fecha de corte; sin ella el interruptor queda deshabilitado."""
        self._resultado = resultado
        self._expediente_id = expediente_id
        self._fecha_corte = fecha_corte

        # Un resultado nuevo siempre llega en su vista oficial.
        self._solicitud_sensibilidad += 1
        self.check_vista_sensibilidad.blockSignals(True)
        self.check_vista_sensibilidad.setChecked(False)
        self.check_vista_sensibilidad.blockSignals(False)
        self.check_vista_sensibilidad.setEnabled(fecha_corte is not None)
        self.selector_indexacion_sensibilidad.setEnabled(fecha_corte is not None)
        self.etiqueta_vista_sensibilidad.setVisible(False)
        self._actualizar_botones_exportar()

        self._pintar_resultado(resultado)

    def _pintar_resultado(self, resultado: LiquidationResult) -> None:
        if resultado.alertas:
            self.etiqueta_alertas.setText("\n".join(f"⚠ {alerta}" for alerta in resultado.alertas))
            self.etiqueta_alertas.setVisible(True)
        else:
            self.etiqueta_alertas.setText("")
            self.etiqueta_alertas.setVisible(False)

        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            concepto_texto = item.concept
            if item.prescrita:
                # Sprint 42: decision del despacho -- la obligacion prescrita se
                # sigue incluyendo en el calculo (el saldo no cambia), solo se
                # marca visualmente para que el abogado decida que hacer con esa
                # informacion (ver ReportTableBuilder.build_matrix, mismo
                # criterio para el PDF/Word).
                concepto_texto = f"⚠ {concepto_texto} — Obligación prescrita, no exigible"

            celdas_fila = [
                QTableWidgetItem(formatear_fecha(item.date)),
                QTableWidgetItem(concepto_texto),
                celda_moneda(item.capital_base),
                celda_porcentaje(item.interest_rate),
                celda_moneda(item.interest_amount),
                celda_moneda(item.indexation_amount),
                celda_moneda(item.payment_amount),
                celda_moneda(item.balance.debt.total()),
            ]
            if item.prescrita:
                for celda in celdas_fila:
                    celda.setForeground(QColor("red"))
            for columna, celda in enumerate(celdas_fila):
                self.tabla.setItem(fila, columna, celda)

        self.etiqueta_interes_total.setText(
            f"Interes acumulado: {formatear_moneda(resultado.total_interest_accrued())}"
        )
        self.etiqueta_pagos_total.setText(
            f"Pagos aplicados: {formatear_moneda(resultado.total_payments_applied())}"
        )
        self.etiqueta_saldo_final.setText(
            f"Saldo final: {formatear_moneda(resultado.final_balance().total())}"
        )

        costas = resultado.final_balance().costas
        if costas > 0:
            self.etiqueta_costas.setText(
                f"Costas procesales (no generan interés): {formatear_moneda(costas)}"
            )
            self.etiqueta_costas.setVisible(True)
        else:
            self.etiqueta_costas.setVisible(False)

        if any(item.balance.event_type == "FRUTO_CIVIL" for item in resultado.items):
            self.etiqueta_fruto_civil.setText(
                "Fruto civil causado (Art. 964 C.C., sin intereses): "
                f"{formatear_moneda(resultado.total_fruto_civil())}"
            )
            self.etiqueta_fruto_civil.setVisible(True)
        else:
            self.etiqueta_fruto_civil.setVisible(False)

        total_saldo_a_favor = resultado.total_saldo_a_favor()
        if total_saldo_a_favor > 0:
            self.etiqueta_saldo_a_favor.setText(
                f"Saldo a favor del deudor: {formatear_moneda(total_saldo_a_favor)}"
            )
            self.etiqueta_saldo_a_favor.setVisible(True)
        else:
            self.etiqueta_saldo_a_favor.setVisible(False)

        if resultado.renta_liquida is not None:
            rl = resultado.renta_liquida
            self.etiqueta_ingresos_netos.setText(
                f"Ingresos netos: {formatear_moneda(rl.ingresos_netos)}"
            )
            self.etiqueta_renta_bruta.setText(f"Renta bruta: {formatear_moneda(rl.renta_bruta)}")
            self.etiqueta_renta_liquida.setText(
                f"Renta líquida: {formatear_moneda(rl.renta_liquida)}"
            )
            self.etiqueta_hubo_perdida.setText(
                f"¿Hubo pérdida líquida?: {'Sí' if rl.hubo_perdida_liquida else 'No'}"
            )
            self.etiqueta_renta_liquida_gravable.setText(
                f"Renta líquida gravable: {formatear_moneda(rl.renta_liquida_gravable)}"
            )
            self.grupo_renta_liquida.setVisible(True)
        else:
            self.grupo_renta_liquida.setVisible(False)

    # --- Sprint 107: vista de sensibilidad "Ver con/sin indexación" ---

    def _en_vista_sensibilidad(self) -> bool:
        return self.check_vista_sensibilidad.isChecked()

    def _actualizar_botones_exportar(self) -> None:
        """Exportar solo esta disponible para la liquidacion oficial: nunca
        mientras se ve la vista de sensibilidad ni durante otra exportacion."""
        en_sensibilidad = self._en_vista_sensibilidad()
        habilitado = not self._exportando and not en_sensibilidad
        self.boton_exportar_pdf.setEnabled(habilitado)
        self.boton_exportar_word.setEnabled(habilitado)
        tooltip = (
            "Desactive «Ver con/sin indexación» para exportar la liquidación oficial."
            if en_sensibilidad
            else ""
        )
        self.boton_exportar_pdf.setToolTip(tooltip)
        self.boton_exportar_word.setToolTip(tooltip)

    def _on_interruptor_sensibilidad(self, activo: bool) -> None:
        self._actualizar_botones_exportar()
        if activo:
            self._recalcular_vista_sensibilidad()
        else:
            self._volver_a_vista_oficial()

    def _on_sentido_sensibilidad_cambiado(self, _indice: int) -> None:
        if self._en_vista_sensibilidad():
            self._recalcular_vista_sensibilidad()

    def _volver_a_vista_oficial(self) -> None:
        self._solicitud_sensibilidad += 1  # descarta cualquier recalculo en curso
        self.etiqueta_vista_sensibilidad.setVisible(False)
        if self._resultado is not None:
            self._pintar_resultado(self._resultado)

    def _recalcular_vista_sensibilidad(self) -> None:
        if self._expediente_id is None or self._fecha_corte is None:
            return
        self._solicitud_sensibilidad += 1
        solicitud = self._solicitud_sensibilidad
        con_indexacion = bool(self.selector_indexacion_sensibilidad.currentData())

        self._tarea_sensibilidad = TareaEnHilo(
            liquidar_vista_sensibilidad, self._expediente_id, self._fecha_corte, con_indexacion
        )
        self._tarea_sensibilidad.senales.completada.connect(
            lambda resultado: self._on_sensibilidad_completada(
                resultado, solicitud, con_indexacion
            )
        )
        self._tarea_sensibilidad.senales.fallo.connect(
            lambda error: self._on_sensibilidad_fallo(error, solicitud)
        )
        QThreadPool.globalInstance().start(self._tarea_sensibilidad)

    def _on_sensibilidad_completada(
        self, resultado: LiquidationResult, solicitud: int, con_indexacion: bool
    ) -> None:
        if solicitud == self._solicitud_sensibilidad and self._en_vista_sensibilidad():
            sentido = "CON" if con_indexacion else "SIN"
            self.etiqueta_vista_sensibilidad.setText(
                f"VISTA DE SENSIBILIDAD — NO ES LA LIQUIDACIÓN OFICIAL: recalculada en "
                f"memoria {sentido} indexación IPC para todas las obligaciones, con los "
                f"datos actuales del expediente. No modifica las obligaciones ni la "
                f"liquidación guardada. Exportar está deshabilitado en esta vista."
            )
            self.etiqueta_vista_sensibilidad.setVisible(True)
            self._pintar_resultado(resultado)
        self.vista_sensibilidad_actualizada.emit()

    def _on_sensibilidad_fallo(self, error: Exception, solicitud: int) -> None:
        if solicitud == self._solicitud_sensibilidad and self._en_vista_sensibilidad():
            # Vuelve a la vista oficial (setChecked dispara _on_interruptor_sensibilidad).
            self.check_vista_sensibilidad.setChecked(False)
            QMessageBox.warning(
                self, "No se pudo calcular la vista de sensibilidad", str(error)
            )
        self.vista_sensibilidad_actualizada.emit()

    def _obtener_radicado(self) -> str:
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)
        radicado = expediente.radicado
        session.close()
        return radicado

    def _exportar_pdf(self) -> None:
        if not self.boton_exportar_pdf.isEnabled():
            return
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(self._obtener_radicado())}.pdf"

        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Exportar a PDF", nombre_sugerido, "PDF (*.pdf)"
        )
        if not ruta:
            return

        self._iniciar_exportacion(_generar_pdf_en_hilo_de_fondo, ruta, "PDF")

    def _exportar_word(self) -> None:
        if not self.boton_exportar_word.isEnabled():
            return
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(self._obtener_radicado())}.docx"

        ruta, _filtro = QFileDialog.getSaveFileName(
            self, "Exportar a Word", nombre_sugerido, "Word (*.docx)"
        )
        if not ruta:
            return

        self._iniciar_exportacion(_generar_word_en_hilo_de_fondo, ruta, "Word")

    def _iniciar_exportacion(self, funcion_generadora, ruta: str, etiqueta: str) -> None:
        self._exportando = True
        self._actualizar_botones_exportar()

        self._dialogo_progreso_exportar = QProgressDialog(
            f"Exportando a {etiqueta}...", None, 0, 0, self
        )
        self._dialogo_progreso_exportar.setWindowModality(Qt.WindowModality.WindowModal)
        self._dialogo_progreso_exportar.setCancelButton(None)
        self._dialogo_progreso_exportar.setMinimumDuration(0)
        self._dialogo_progreso_exportar.show()

        self._tarea_exportar = TareaEnHilo(
            funcion_generadora, self._resultado, self._expediente_id, ruta
        )
        self._tarea_exportar.senales.completada.connect(
            lambda ruta_generada: self._on_exportar_completado(ruta_generada, etiqueta)
        )
        self._tarea_exportar.senales.fallo.connect(self._on_exportar_fallo)
        QThreadPool.globalInstance().start(self._tarea_exportar)

    def _finalizar_exportacion_en_curso(self) -> None:
        self._dialogo_progreso_exportar.close()
        self._exportando = False
        self._actualizar_botones_exportar()

    def _on_exportar_completado(self, ruta: str, etiqueta: str) -> None:
        self._finalizar_exportacion_en_curso()
        # Sprint 36: confirmacion de bajo riesgo (exportar con exito no es destructivo
        # ni requiere validar nada mas) -- toast no bloqueante en vez de QMessageBox
        # modal, para no interrumpir al usuario con un dialogo que hay que cerrar a
        # mano. QMessageBox.critical() se mantiene para el caso de error (ver
        # _on_exportar_fallo), que si amerita bloquear hasta que el usuario lo note.
        mostrar_toast(self, f"{etiqueta} guardado en: {ruta}")
        self.exportacion_finalizada.emit()

    def _on_exportar_fallo(self, error: Exception) -> None:
        self._finalizar_exportacion_en_curso()
        QMessageBox.critical(self, "No se pudo exportar", str(error))
        self.exportacion_finalizada.emit()
