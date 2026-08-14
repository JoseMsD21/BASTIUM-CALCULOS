from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

# Peso relativo de cada columna de la tabla de cronologia -- "Concepto" pesa mas
# porque es la unica columna con texto largo (ej. "Indexacion IPC -- Reparacion
# vehiculo por accidente de transito"); el resto son fechas/montos cortos. Usado
# por _anchos_columnas_cronologia para repartir el ancho disponible de la pagina
# proporcionalmente, en vez de dejar que reportlab infiera el ancho de cada
# columna del contenido sin wrap (causaba que la tabla se saliera de los margenes
# -- ver docs/Pendientes.md, hallazgo de la prueba practica Civil/Familia).
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


class JudicialPDFGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.c_burgundy = colors.HexColor("#ae1c21")
        self.c_black = colors.HexColor("#000000")
        self.c_cream = colors.HexColor("#f5f1e9")

        self.styles.add(
            ParagraphStyle(
                name="BastiumTitle",
                fontSize=16,
                textColor=self.c_burgundy,
                spaceAfter=20,
                alignment=1,  # Centro
            )
        )
        self.styles.add(
            ParagraphStyle(
                name="CeldaConcepto",
                fontSize=8,
                leading=9.5,
                textColor=self.c_black,
            )
        )

    def _anchos_columnas_cronologia(self, encabezados: list[str], ancho_disponible: float) -> list[float]:
        pesos = [_PESO_COLUMNA_CRONOLOGIA.get(encabezado, 0.85) for encabezado in encabezados]
        total_pesos = sum(pesos)
        return [(peso / total_pesos) * ancho_disponible for peso in pesos]

    def generar_documento(self, datos_rubros: list, ruta_grafica: str):
        # Crear documento con fondo crema (se simula mediante el canvas)
        doc = SimpleDocTemplate(self.output_path, pagesize=letter)
        elementos = []

        # Título
        elementos.append(
            Paragraph("<b>LIQUIDACIÓN PROVISIONAL DE ALIMENTOS</b>", self.styles["BastiumTitle"])
        )

        # Preparar datos para la tabla
        datos_tabla = [["CONCEPTO", "CAPITAL EXIGIBLE", "DÍAS MORA", "INTERESES", "TOTAL"]]

        total_capital = 0
        total_intereses = 0

        for rubro in datos_rubros:
            datos_tabla.append(
                [
                    rubro["concepto"],
                    f"${rubro['capital']:,.2f}",
                    str(rubro["dias_mora"]),
                    f"${rubro['intereses']:,.2f}",
                    f"${rubro['total_rubro']:,.2f}",
                ]
            )
            total_capital += float(rubro["capital"])
            total_intereses += float(rubro["intereses"])

        # Fila de totales
        datos_tabla.append(
            [
                "TOTALES",
                f"${total_capital:,.2f}",
                "-",
                f"${total_intereses:,.2f}",
                f"${total_capital + total_intereses:,.2f}",
            ]
        )

        # Estilo estricto de la tabla
        tabla = Table(datos_tabla, colWidths=[150, 100, 70, 100, 100])
        tabla.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.c_black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.c_cream),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("BACKGROUND", (0, 1), (-1, -1), self.c_cream),
                    ("TEXTCOLOR", (0, 1), (-1, -1), self.c_black),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 1, self.c_burgundy),
                    (
                        "FONTNAME",
                        (0, -1),
                        (-1, -1),
                        "Helvetica-Bold",
                    ),  # Fila de totales en negrita
                ]
            )
        )

        elementos.append(tabla)
        elementos.append(Spacer(1, 30))

        # Subtítulo de Gráfica
        elementos.append(
            Paragraph(
                "<b>DISTRIBUCIÓN ESTADÍSTICA DE CAPITAL ADEUDADO</b>", self.styles["BastiumTitle"]
            )
        )

        # Insertar Gráfica
        if ruta_grafica:
            img = Image(ruta_grafica, width=450, height=225)
            elementos.append(img)

        # Compilar el PDF
        doc.build(elementos)

    def generate(
        self,
        title: str,
        summary: dict,
        table_data: list,
        encabezado: dict | None = None,
        renta_liquida: dict | None = None,
    ):
        """Genera el dictamen a partir de la salida del motor LiquidationCore
        (ReportSummaryBuilder.build_summary + ReportTableBuilder.build_matrix)."""
        # Horizontal (Sprint 50, hallazgo de la prueba practica Civil/Familia): la
        # tabla de cronologia tiene 10-11 columnas de fechas/montos/texto -- en
        # vertical (Letter portrait, ~468pt utiles) no cabe ni con wrap; en
        # horizontal (~720pt utiles con margenes de 36pt) si.
        doc = SimpleDocTemplate(
            self.output_path,
            pagesize=landscape(letter),
            leftMargin=36,
            rightMargin=36,
            topMargin=36,
            bottomMargin=36,
        )
        ancho_disponible = doc.width
        elementos = []

        elementos.append(Paragraph(f"<b>{title}</b>", self.styles["BastiumTitle"]))

        if encabezado:
            if encabezado.get("radicado"):
                elementos.append(
                    Paragraph(f"Radicado: {encabezado['radicado']}", self.styles["Normal"])
                )
            if encabezado.get("partes"):
                elementos.append(Paragraph(encabezado["partes"], self.styles["Normal"]))
            if encabezado.get("juzgado"):
                elementos.append(
                    Paragraph(f"Juzgado: {encabezado['juzgado']}", self.styles["Normal"])
                )
            elementos.append(Spacer(1, 12))

        # Tabla de resumen ejecutivo
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
        datos_resumen = [["Rubro Financiero", "Monto Liquidado"]]
        datos_resumen.extend(list(fila) for fila in filas_resumen)

        tabla_resumen = Table(datos_resumen, colWidths=[250, 150])
        tabla_resumen.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), self.c_black),
                    ("TEXTCOLOR", (0, 0), (-1, 0), self.c_cream),
                    ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                    ("BACKGROUND", (0, 1), (-1, -1), self.c_cream),
                    ("TEXTCOLOR", (0, 1), (-1, -1), self.c_black),
                    ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                    ("GRID", (0, 0), (-1, -1), 1, self.c_burgundy),
                    ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ]
            )
        )
        elementos.append(tabla_resumen)
        elementos.append(Spacer(1, 30))

        # Tabla de cronología detallada
        elementos.append(
            Paragraph(
                "<b>Cronología Detallada de Imputaciones y Saldos</b>", self.styles["BastiumTitle"]
            )
        )

        # Sprint 46: la columna "Saldo a favor" solo se agrega cuando el resumen
        # ya indico que hubo un sobrepago (mismo criterio que la linea del
        # resumen ejecutivo) -- asi el layout de las 6 areas no cambia para la
        # inmensa mayoria de liquidaciones, que nunca tienen sobrepago.
        mostrar_saldo_a_favor = "saldo_a_favor" in summary

        encabezados_cronologia = [
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
            encabezados_cronologia.append("Saldo a favor")
        datos_cronologia = [encabezados_cronologia]
        for fila in table_data:
            # "Concepto" envuelto en Paragraph (Sprint 50): a diferencia de las demas
            # columnas (fechas/montos cortos), el concepto puede ser texto largo (ej.
            # "Indexación IPC — Reparación vehículo por accidente de tránsito") -- una
            # celda con texto plano no hace word-wrap en reportlab y reportlab
            # ensancha la columna para que quepa en una sola linea, lo que era la
            # causa real de que la tabla se saliera de los margenes de la pagina.
            fila_cronologia = [
                fila["fecha"],
                Paragraph(fila["concepto"], self.styles["CeldaConcepto"]),
                fila["base_capital"],
                fila["tasa"],
                fila["interes"],
                fila["indexacion"],
                fila["pago"],
                fila["saldo_capital"],
                fila["saldo_interes"],
                fila["saldo_total"],
            ]
            if mostrar_saldo_a_favor:
                fila_cronologia.append(fila.get("saldo_a_favor", "$0.00"))
            datos_cronologia.append(fila_cronologia)

        anchos_cronologia = self._anchos_columnas_cronologia(
            encabezados_cronologia, ancho_disponible
        )
        tabla_cronologia = Table(datos_cronologia, colWidths=anchos_cronologia, repeatRows=1)
        estilo_cronologia = [
            ("BACKGROUND", (0, 0), (-1, 0), self.c_black),
            ("TEXTCOLOR", (0, 0), (-1, 0), self.c_cream),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("BACKGROUND", (0, 1), (-1, -1), self.c_cream),
            ("TEXTCOLOR", (0, 1), (-1, -1), self.c_black),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.5, self.c_burgundy),
            ("LEFTPADDING", (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Sprint 42: indicador visual (texto en rojo/negrita) para las filas cuya
        # obligacion de origen ya vencio su plazo de prescripcion/caducidad
        # (ReportTableBuilder.build_matrix ya expone "prescrita" por fila) -- no
        # se excluyen de la tabla, solo se resaltan.
        for indice_fila, fila in enumerate(table_data, start=1):
            if fila.get("prescrita"):
                estilo_cronologia.append(
                    ("TEXTCOLOR", (0, indice_fila), (-1, indice_fila), colors.red)
                )
                estilo_cronologia.append(
                    ("FONTNAME", (0, indice_fila), (-1, indice_fila), "Helvetica-Bold")
                )
        tabla_cronologia.setStyle(TableStyle(estilo_cronologia))
        elementos.append(tabla_cronologia)

        if renta_liquida is not None:
            elementos.append(Spacer(1, 30))
            elementos.append(
                Paragraph(
                    "<b>Depuración de Renta Líquida Gravable</b>", self.styles["BastiumTitle"]
                )
            )
            datos_renta_liquida = [
                ["Rubro", "Monto"],
                ["Ingresos Netos", renta_liquida["ingresos_netos"]],
                ["Renta Bruta", renta_liquida["renta_bruta"]],
                ["Renta Líquida", renta_liquida["renta_liquida"]],
                ["¿Hubo Pérdida Líquida?", renta_liquida["hubo_perdida_liquida"]],
                ["RENTA LÍQUIDA GRAVABLE", renta_liquida["renta_liquida_gravable"]],
            ]
            tabla_renta_liquida = Table(datos_renta_liquida, colWidths=[250, 150])
            tabla_renta_liquida.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), self.c_black),
                        ("TEXTCOLOR", (0, 0), (-1, 0), self.c_cream),
                        ("ALIGN", (0, 0), (-1, 0), "CENTER"),
                        ("BACKGROUND", (0, 1), (-1, -1), self.c_cream),
                        ("TEXTCOLOR", (0, 1), (-1, -1), self.c_black),
                        ("ALIGN", (1, 1), (-1, -1), "RIGHT"),
                        ("GRID", (0, 0), (-1, -1), 1, self.c_burgundy),
                        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                    ]
                )
            )
            elementos.append(tabla_renta_liquida)

        doc.build(elementos)
