import re

from PySide6.QtCore import Qt, QThreadPool, Signal
from PySide6.QtWidgets import (
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
from app.core.constants import AREAS_DERECHO
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from app.views.concurrency import TareaEnHilo
from app.views.icons import icon
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
        title, summary, table_data, encabezado, renta_liquida=renta_liquida
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
        title, summary, table_data, encabezado, renta_liquida=renta_liquida
    )
    return ruta


class ResultadoLiquidacionView(QWidget):
    exportacion_finalizada = Signal()

    def __init__(self):
        super().__init__()

        self._resultado = None
        self._expediente_id = None

        self.tabla = QTableWidget(0, 8)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Indexacion/Sanciones", "Pago", "Saldo"]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: 0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: 0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: 0.00")

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

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_saldo_final)
        layout.addWidget(self.grupo_renta_liquida)
        layout.addLayout(layout_botones)
        self.setLayout(layout)

    def mostrar(self, resultado: LiquidationResult, expediente_id: int) -> None:
        self._resultado = resultado
        self._expediente_id = expediente_id

        self.tabla.setRowCount(len(resultado.items))
        for fila, item in enumerate(resultado.items):
            self.tabla.setItem(fila, 0, QTableWidgetItem(item.date.isoformat()))
            self.tabla.setItem(fila, 1, QTableWidgetItem(item.concept))
            self.tabla.setItem(fila, 2, QTableWidgetItem(str(item.capital_base)))
            self.tabla.setItem(fila, 3, QTableWidgetItem(str(item.interest_rate)))
            self.tabla.setItem(fila, 4, QTableWidgetItem(str(item.interest_amount)))
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.indexation_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 7, QTableWidgetItem(str(item.balance.debt.total())))

        self.etiqueta_interes_total.setText(f"Interes acumulado: {resultado.total_interest_accrued()}")
        self.etiqueta_pagos_total.setText(f"Pagos aplicados: {resultado.total_payments_applied()}")
        self.etiqueta_saldo_final.setText(f"Saldo final: {resultado.final_balance().total()}")

        if resultado.renta_liquida is not None:
            rl = resultado.renta_liquida
            self.etiqueta_ingresos_netos.setText(f"Ingresos netos: {rl.ingresos_netos}")
            self.etiqueta_renta_bruta.setText(f"Renta bruta: {rl.renta_bruta}")
            self.etiqueta_renta_liquida.setText(f"Renta líquida: {rl.renta_liquida}")
            self.etiqueta_hubo_perdida.setText(
                f"¿Hubo pérdida líquida?: {'Sí' if rl.hubo_perdida_liquida else 'No'}"
            )
            self.etiqueta_renta_liquida_gravable.setText(
                f"Renta líquida gravable: {rl.renta_liquida_gravable}"
            )
            self.grupo_renta_liquida.setVisible(True)
        else:
            self.grupo_renta_liquida.setVisible(False)

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
        self.boton_exportar_pdf.setEnabled(False)
        self.boton_exportar_word.setEnabled(False)

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
        self.boton_exportar_pdf.setEnabled(True)
        self.boton_exportar_word.setEnabled(True)

    def _on_exportar_completado(self, ruta: str, etiqueta: str) -> None:
        self._finalizar_exportacion_en_curso()
        QMessageBox.information(self, "Exportación completa", f"{etiqueta} guardado en: {ruta}")
        self.exportacion_finalizada.emit()

    def _on_exportar_fallo(self, error: Exception) -> None:
        self._finalizar_exportacion_en_curso()
        QMessageBox.critical(self, "No se pudo exportar", str(error))
        self.exportacion_finalizada.emit()
