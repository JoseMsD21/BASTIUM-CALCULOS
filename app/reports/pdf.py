from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

class JudicialPDFGenerator:
    def __init__(self, output_path: str):
        self.output_path = output_path
        self.styles = getSampleStyleSheet()
        self.c_burgundy = colors.HexColor("#ae1c21")
        self.c_black = colors.HexColor("#000000")
        self.c_cream = colors.HexColor("#f5f1e9")
        
        self.styles.add(ParagraphStyle(
            name='BastiumTitle',
            fontSize=16,
            textColor=self.c_burgundy,
            spaceAfter=20,
            alignment=1 # Centro
        ))

    def generar_documento(self, datos_rubros: list, ruta_grafica: str):
        # Crear documento con fondo crema (se simula mediante el canvas)
        doc = SimpleDocTemplate(self.output_path, pagesize=letter)
        elementos = []
        
        # Título
        elementos.append(Paragraph("<b>LIQUIDACIÓN PROVISIONAL DE ALIMENTOS</b>", self.styles['BastiumTitle']))
        
        # Preparar datos para la tabla
        datos_tabla = [["CONCEPTO", "CAPITAL EXIGIBLE", "DÍAS MORA", "INTERESES", "TOTAL"]]
        
        total_capital = 0
        total_intereses = 0
        
        for rubro in datos_rubros:
            datos_tabla.append([
                rubro["concepto"],
                f"${rubro['capital']:,.2f}",
                str(rubro["dias_mora"]),
                f"${rubro['intereses']:,.2f}",
                f"${rubro['total_rubro']:,.2f}"
            ])
            total_capital += float(rubro['capital'])
            total_intereses += float(rubro['intereses'])
            
        # Fila de totales
        datos_tabla.append([
            "TOTALES", 
            f"${total_capital:,.2f}", 
            "-", 
            f"${total_intereses:,.2f}", 
            f"${total_capital + total_intereses:,.2f}"
        ])
        
        # Estilo estricto de la tabla
        tabla = Table(datos_tabla, colWidths=[150, 100, 70, 100, 100])
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.c_black),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.c_cream),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), self.c_cream),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.c_black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, self.c_burgundy),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'), # Fila de totales en negrita
        ]))
        
        elementos.append(tabla)
        elementos.append(Spacer(1, 30))

        # Subtítulo de Gráfica
        elementos.append(Paragraph("<b>DISTRIBUCIÓN ESTADÍSTICA DE CAPITAL ADEUDADO</b>", self.styles['BastiumTitle']))

        # Insertar Gráfica
        if ruta_grafica:
            img = Image(ruta_grafica, width=450, height=225)
            elementos.append(img)

        # Compilar el PDF
        doc.build(elementos)

    def generate(self, title: str, summary: dict, table_data: list):
        """Genera el dictamen a partir de la salida del motor LiquidationCore
        (ReportSummaryBuilder.build_summary + ReportTableBuilder.build_matrix)."""
        doc = SimpleDocTemplate(self.output_path, pagesize=letter)
        elementos = []

        elementos.append(Paragraph(f"<b>{title}</b>", self.styles['BastiumTitle']))

        # Tabla de resumen ejecutivo
        filas_resumen = [
            ("Total Abonos Aplicados", summary["total_abonos"]),
            ("Intereses Generados", summary["total_intereses_generados"]),
            ("Saldo Final Capital", summary["saldo_final_capital"]),
            ("Saldo Final Intereses", summary["saldo_final_intereses"]),
            ("GRAN TOTAL ADEUDADO", summary["gran_total_adeudado"]),
        ]
        datos_resumen = [["Rubro Financiero", "Monto Liquidado"]]
        datos_resumen.extend(list(fila) for fila in filas_resumen)

        tabla_resumen = Table(datos_resumen, colWidths=[250, 150])
        tabla_resumen.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.c_black),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.c_cream),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('BACKGROUND', (0, 1), (-1, -1), self.c_cream),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.c_black),
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 1, self.c_burgundy),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ]))
        elementos.append(tabla_resumen)
        elementos.append(Spacer(1, 30))

        # Tabla de cronología detallada
        elementos.append(Paragraph("<b>Cronología Detallada de Imputaciones y Saldos</b>", self.styles['BastiumTitle']))

        datos_cronologia = [["Fecha", "Concepto", "Base Capital", "Tasa", "Pago", "Saldo Capital", "Saldo Interés", "Saldo Total"]]
        for fila in table_data:
            datos_cronologia.append([
                fila["fecha"],
                fila["concepto"],
                fila["base_capital"],
                fila["tasa"],
                fila["pago"],
                fila["saldo_capital"],
                fila["saldo_interes"],
                fila["saldo_total"],
            ])

        tabla_cronologia = Table(datos_cronologia, repeatRows=1)
        tabla_cronologia.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), self.c_black),
            ('TEXTCOLOR', (0, 0), (-1, 0), self.c_cream),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),
            ('BACKGROUND', (0, 1), (-1, -1), self.c_cream),
            ('TEXTCOLOR', (0, 1), (-1, -1), self.c_black),
            ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),
            ('GRID', (0, 0), (-1, -1), 0.5, self.c_burgundy),
        ]))
        elementos.append(tabla_cronologia)

        doc.build(elementos)