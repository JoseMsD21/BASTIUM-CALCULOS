from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Pt, RGBColor


class WordReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.c_burgundy = RGBColor(0xAE, 0x1C, 0x21)
        self.c_prescrita = RGBColor(0xC0, 0x00, 0x00)

    def generate(
        self,
        title: str,
        summary: dict,
        table_data: list,
        encabezado: dict | None = None,
        renta_liquida: dict | None = None,
    ) -> None:
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
            ("Saldo Final Indexación/Sanciones", summary["saldo_final_indexacion"]),
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
            "Fecha",
            "Concepto",
            "Base Capital",
            "Tasa",
            "Interés",
            "Indexación/Sanciones",
            "Pago",
            "Saldo Capital",
            "Saldo Interés",
            "Saldo Total",
        ]
        tabla_cronologia = documento.add_table(rows=1, cols=len(columnas_cronologia))
        tabla_cronologia.style = "Table Grid"
        for celda, texto in zip(tabla_cronologia.rows[0].cells, columnas_cronologia, strict=True):
            celda.text = texto
        for fila_datos in table_data:
            celdas_fila = tabla_cronologia.add_row().cells
            valores_fila = [
                fila_datos["fecha"],
                fila_datos["concepto"],
                fila_datos["base_capital"],
                fila_datos["tasa"],
                fila_datos["interes"],
                fila_datos["indexacion"],
                fila_datos["pago"],
                fila_datos["saldo_capital"],
                fila_datos["saldo_interes"],
                fila_datos["saldo_total"],
            ]
            # Sprint 42: indicador visual (texto en rojo) para las filas cuya
            # obligacion de origen ya vencio su plazo de prescripcion/caducidad
            # (ReportTableBuilder.build_matrix ya expone "prescrita" por fila) --
            # no se excluyen de la tabla, solo se resaltan. Se usa un run
            # explicito (en vez de `celda.text = ...`) para poder colorear el
            # texto: el setter `.text` de python-docx no expone color de fuente.
            es_prescrita = bool(fila_datos.get("prescrita"))
            for celda, texto in zip(celdas_fila, valores_fila, strict=True):
                run = celda.paragraphs[0].add_run(texto)
                if es_prescrita:
                    run.font.color.rgb = self.c_prescrita
                    run.bold = True

        if renta_liquida is not None:
            documento.add_paragraph()
            parrafo_renta_liquida = documento.add_paragraph()
            run_renta_liquida = parrafo_renta_liquida.add_run(
                "Depuración de Renta Líquida Gravable"
            )
            run_renta_liquida.bold = True
            run_renta_liquida.font.color.rgb = self.c_burgundy

            filas_renta_liquida = [
                ("Ingresos Netos", renta_liquida["ingresos_netos"]),
                ("Renta Bruta", renta_liquida["renta_bruta"]),
                ("Renta Líquida", renta_liquida["renta_liquida"]),
                ("¿Hubo Pérdida Líquida?", renta_liquida["hubo_perdida_liquida"]),
                ("RENTA LÍQUIDA GRAVABLE", renta_liquida["renta_liquida_gravable"]),
            ]
            tabla_renta_liquida = documento.add_table(rows=1, cols=2)
            tabla_renta_liquida.style = "Table Grid"
            celdas_encabezado_rl = tabla_renta_liquida.rows[0].cells
            celdas_encabezado_rl[0].text = "Rubro"
            celdas_encabezado_rl[1].text = "Monto"
            for etiqueta, valor in filas_renta_liquida:
                celdas_fila_rl = tabla_renta_liquida.add_row().cells
                celdas_fila_rl[0].text = etiqueta
                celdas_fila_rl[1].text = valor

        documento.save(self.output_path)
