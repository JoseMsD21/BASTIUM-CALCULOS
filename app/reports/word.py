from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt, RGBColor

# Peso relativo de cada columna de la tabla de cronologia -- mismo criterio y
# mismos pesos que _PESO_COLUMNA_CRONOLOGIA en app/reports/pdf.py (mantener
# ambos en sync si se ajusta uno). "Concepto" pesa mas por ser la unica columna
# con texto largo.
_PESO_COLUMNA_CRONOLOGIA = {
    "Fecha": 0.7,
    "Concepto": 2.0,
    "Base Capital": 0.95,
    "Tasa": 0.55,
    "Interés": 0.85,
    "Indexación/Sanciones": 1.05,
    "Pago": 0.85,
    "Saldo Capital": 0.95,
    "Saldo Interés": 0.9,
    "Saldo Total": 0.95,
    "Saldo a favor": 0.85,
}


class WordReportGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.c_burgundy = RGBColor(0xAE, 0x1C, 0x21)
        self.c_prescrita = RGBColor(0xC0, 0x00, 0x00)

    def _anchos_columnas_cronologia(self, encabezados: list[str], ancho_disponible: Cm) -> list[Cm]:
        pesos = [_PESO_COLUMNA_CRONOLOGIA.get(encabezado, 0.85) for encabezado in encabezados]
        total_pesos = sum(pesos)
        return [Cm((peso / total_pesos) * ancho_disponible.cm) for peso in pesos]

    def _fijar_ancho_columna(self, tabla, indice: int, ancho: Cm) -> None:
        # Quirk conocido de python-docx: asignar solo `table.columns[i].width` no
        # es suficiente para que Word respete el ancho al abrir el documento --
        # hay que fijarlo tambien celda por celda de esa columna.
        tabla.columns[indice].width = ancho
        for fila in tabla.rows:
            fila.cells[indice].width = ancho

    def generate(
        self,
        title: str,
        summary: dict,
        table_data: list,
        encabezado: dict | None = None,
        renta_liquida: dict | None = None,
    ) -> None:
        documento = Document()

        # Horizontal (Sprint 50, hallazgo de la prueba practica Civil/Familia): la
        # tabla de cronologia tiene 10-11 columnas -- en vertical (Letter portrait,
        # ~15.9cm utiles) no cabe; en horizontal (~24.9cm utiles con margenes de
        # 1.5cm) si. Ademas de girar la pagina, hay que fijar el ancho de cada
        # columna explicitamente (ver _fijar_ancho_columna) porque el estilo
        # "Table Grid" por defecto usa autofit-to-contents, que ignora los margenes
        # de la pagina cuando el contenido es ancho -- esa era la causa real del
        # desborde, no la orientacion en si.
        seccion = documento.sections[0]
        seccion.orientation = WD_ORIENT.LANDSCAPE
        # python-docx no intercambia el ancho/alto de pagina automaticamente al
        # cambiar `orientation` -- hay que hacerlo a mano.
        seccion.page_width, seccion.page_height = seccion.page_height, seccion.page_width
        seccion.left_margin = Cm(1.5)
        seccion.right_margin = Cm(1.5)
        seccion.top_margin = Cm(1.5)
        seccion.bottom_margin = Cm(1.5)
        ancho_disponible = Cm(
            seccion.page_width.cm - seccion.left_margin.cm - seccion.right_margin.cm
        )

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
        # Sprint 46: el saldo a favor de un sobrepago (Sprint 23) solo se muestra
        # cuando ReportSummaryBuilder.build_summary lo agrego al diccionario (es
        # decir, cuando efectivamente hubo un sobrepago).
        if "saldo_a_favor" in summary:
            filas_resumen.append(("Saldo a favor del deudor", summary["saldo_a_favor"]))
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

        # Sprint 46: la columna "Saldo a favor" solo se agrega cuando el resumen
        # ya indico que hubo un sobrepago (mismo criterio que la linea del
        # resumen ejecutivo) -- asi el layout de las 6 areas no cambia para la
        # inmensa mayoria de liquidaciones, que nunca tienen sobrepago.
        mostrar_saldo_a_favor = "saldo_a_favor" in summary

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
        if mostrar_saldo_a_favor:
            columnas_cronologia.append("Saldo a favor")
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
            if mostrar_saldo_a_favor:
                valores_fila.append(fila_datos.get("saldo_a_favor", "$0.00"))
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

        # Fijar ancho por columna (Sprint 50): "Table Grid" por defecto usa
        # autofit-to-contents, que Word resuelve al abrir el documento sin
        # respetar el ancho de pagina cuando el contenido es ancho (esa era la
        # causa real del desborde). `autofit = False` cambia la tabla a layout
        # fijo para que los anchos de abajo se respeten.
        tabla_cronologia.autofit = False
        anchos_cronologia = self._anchos_columnas_cronologia(
            columnas_cronologia, ancho_disponible
        )
        for indice, ancho in enumerate(anchos_cronologia):
            self._fijar_ancho_columna(tabla_cronologia, indice, ancho)

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
