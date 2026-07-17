from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


class WordReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.c_burgundy = RGBColor(0xAE, 0x1C, 0x21)

    def generate(self, title: str, summary: dict, table_data: list, encabezado: dict | None = None) -> None:
        documento = Document()

        parrafo_titulo = documento.add_paragraph()
        parrafo_titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        run_titulo = parrafo_titulo.add_run(title)
        run_titulo.bold = True
        run_titulo.font.size = Pt(16)
        run_titulo.font.color.rgb = self.c_burgundy

        if encabezado:
            if encabezado.get("radicado"):
                documento.add_paragraph(f"Radicado: {encabezado['radicado']}")
            if encabezado.get("partes"):
                documento.add_paragraph(encabezado["partes"])
            if encabezado.get("juzgado"):
                documento.add_paragraph(f"Juzgado: {encabezado['juzgado']}")

        documento.add_paragraph()

        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
        tabla_resumen = documento.add_table(rows=1, cols=2)
        tabla_resumen.style = "Table Grid"
        celdas_encabezado = tabla_resumen.rows[0].cells
        celdas_encabezado[0].text = "Rubro Financiero"
        celdas_encabezado[1].text = "Monto Liquidado"
        for etiqueta, valor in filas_resumen:
            celdas_fila = tabla_resumen.add_row().cells
            celdas_fila[0].text = etiqueta
            celdas_fila[1].text = valor

        documento.add_paragraph()
        parrafo_subtitulo = documento.add_paragraph()
        run_subtitulo = parrafo_subtitulo.add_run("Cronología Detallada de Imputaciones y Saldos")
        run_subtitulo.bold = True
        run_subtitulo.font.color.rgb = self.c_burgundy

        columnas_cronologia = [
            "Fecha", "Concepto", "Base Capital", "Tasa", "Interés", "Pago",
            "Saldo Capital", "Saldo Interés", "Saldo Total",
        ]
        tabla_cronologia = documento.add_table(rows=1, cols=len(columnas_cronologia))
        tabla_cronologia.style = "Table Grid"
        for celda, texto in zip(tabla_cronologia.rows[0].cells, columnas_cronologia):
            celda.text = texto
        for fila_datos in table_data:
            celdas_fila = tabla_cronologia.add_row().cells
            celdas_fila[0].text = fila_datos["fecha"]
            celdas_fila[1].text = fila_datos["concepto"]
            celdas_fila[2].text = fila_datos["base_capital"]
            celdas_fila[3].text = fila_datos["tasa"]
            celdas_fila[4].text = fila_datos["interes"]
            celdas_fila[5].text = fila_datos["pago"]
            celdas_fila[6].text = fila_datos["saldo_capital"]
            celdas_fila[7].text = fila_datos["saldo_interes"]
            celdas_fila[8].text = fila_datos["saldo_total"]

        documento.save(self.output_path)
