import re

from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
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
from database.models import Expediente


def _sanitizar_nombre_archivo(texto: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", texto)


class ResultadoLiquidacionView(QWidget):
    def __init__(self):
        super().__init__()

        self._resultado = None
        self._expediente_id = None

        self.tabla = QTableWidget(0, 7)
        self.tabla.setHorizontalHeaderLabels(
            ["Fecha", "Concepto", "Capital base", "Tasa %", "Interes", "Pago", "Saldo"]
        )

        self.etiqueta_interes_total = QLabel("Interes acumulado: 0.00")
        self.etiqueta_pagos_total = QLabel("Pagos aplicados: 0.00")
        self.etiqueta_saldo_final = QLabel("Saldo final: 0.00")

        self.boton_exportar_pdf = QPushButton("Exportar a PDF")
        self.boton_exportar_pdf.clicked.connect(self._exportar_pdf)
        self.boton_exportar_word = QPushButton("Exportar a Word")
        self.boton_exportar_word.clicked.connect(self._exportar_word)

        layout_botones = QHBoxLayout()
        layout_botones.addWidget(self.boton_exportar_pdf)
        layout_botones.addWidget(self.boton_exportar_word)

        layout = QVBoxLayout()
        layout.addWidget(self.tabla)
        layout.addWidget(self.etiqueta_interes_total)
        layout.addWidget(self.etiqueta_pagos_total)
        layout.addWidget(self.etiqueta_saldo_final)
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
            self.tabla.setItem(fila, 5, QTableWidgetItem(str(item.payment_amount)))
            self.tabla.setItem(fila, 6, QTableWidgetItem(str(item.balance.debt.total())))

        self.etiqueta_interes_total.setText(f"Interes acumulado: {resultado.total_interest_accrued()}")
        self.etiqueta_pagos_total.setText(f"Pagos aplicados: {resultado.total_payments_applied()}")
        self.etiqueta_saldo_final.setText(f"Saldo final: {resultado.final_balance().total()}")

    def _construir_datos_reporte(self):
        session = session_module.get_session()
        expediente = session.get(Expediente, self._expediente_id)

        area_label = expediente.area_derecho.value
        for codigo, etiqueta, _habilitada in AREAS_DERECHO:
            if codigo == expediente.area_derecho.value:
                area_label = etiqueta
                break

        title = f"LIQUIDACIÓN DE OBLIGACIONES — ÁREA {area_label.upper()}"
        encabezado = build_encabezado(
            expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado
        )
        radicado = expediente.radicado
        session.close()

        summary = ReportSummaryBuilder().build_summary(self._resultado)
        table_data = ReportTableBuilder().build_matrix(self._resultado)

        return title, encabezado, summary, table_data, radicado

    def _exportar_pdf(self) -> None:
        title, encabezado, summary, table_data, radicado = self._construir_datos_reporte()
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(radicado)}.pdf"

        ruta, _filtro = QFileDialog.getSaveFileName(self, "Exportar a PDF", nombre_sugerido, "PDF (*.pdf)")
        if not ruta:
            return

        try:
            JudicialPDFGenerator(ruta).generate(title, summary, table_data, encabezado)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo exportar", str(error))
            return

        QMessageBox.information(self, "Exportación completa", f"PDF guardado en: {ruta}")

    def _exportar_word(self) -> None:
        title, encabezado, summary, table_data, radicado = self._construir_datos_reporte()
        nombre_sugerido = f"Liquidacion_{_sanitizar_nombre_archivo(radicado)}.docx"

        ruta, _filtro = QFileDialog.getSaveFileName(self, "Exportar a Word", nombre_sugerido, "Word (*.docx)")
        if not ruta:
            return

        try:
            WordReportGenerator(ruta).generate(title, summary, table_data, encabezado)
        except Exception as error:
            QMessageBox.critical(self, "No se pudo exportar", str(error))
            return

        QMessageBox.information(self, "Exportación completa", f"Word guardado en: {ruta}")
