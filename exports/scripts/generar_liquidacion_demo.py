import os
import sys
from datetime import date
from decimal import Decimal

# Evita UnicodeEncodeError en consolas Windows con code page heredada (cp1252)
# al imprimir símbolos como "✓".
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

# Garantizar resolución de rutas desde la raíz del proyecto
# (este script vive en exports/scripts/, dos niveles bajo la raíz)
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.schedulers.base import Event
from app.engine.liquidation.engine import LiquidationCore
from app.engine.financial.rate import Rate
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.pdf import JudicialPDFGenerator

def ejecutar_prueba_maestra():
    print("Iniciando orquestación de liquidación forense...")

    # 1. Definición del Escenario Jurídico
    fecha_inicio = date(2024, 1, 1)
    fecha_corte = date(2025, 3, 15)
    tasa_mora = Rate.from_percent(Decimal("0.1")) # 0.1% diario

    # 2. Generación Cronológica (Obligación de $800,000 mensuales los días 5)
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(Decimal("800000.00"), "Cuota Ordinaria", 5)
    eventos_deuda = scheduler.generate(fecha_inicio, fecha_corte)

    # 3. Inyección de Hechos Externos (El demandado consignó $2,000,000 en diciembre)
    abono = Event(
        date=date(2024, 12, 10),
        payload={"amount": Decimal("2000000.00")},
        event_type="PAYMENT"
    )
    eventos_historicos = eventos_deuda + [abono]

    # 4. Procesamiento Matemático Estricto
    print("Calculando matriz de estado inmutable...")
    motor = LiquidationCore(default_daily_rate=tasa_mora)
    resultado = motor.process(eventos_historicos, fecha_corte)

    # 5. Transformación y Formateo (Adaptadores de Presentación)
    print("Estructurando matrices de reporte...")
    resumen = ReportSummaryBuilder().build_summary(resultado)
    tabla = ReportTableBuilder().build_matrix(resultado)

    # 6. Materialización Física (PDF)
    # __file__ ya está dentro de exports/scripts/, así que subir un nivel basta
    export_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.makedirs(export_dir, exist_ok=True)
    pdf_path = os.path.join(export_dir, "Dictamen_Liquidacion_001.pdf")
    
    print(f"Renderizando documento tipográfico en: {pdf_path}")
    pdf_generator = JudicialPDFGenerator(pdf_path)
    pdf_generator.generate(
        title="Liquidación Judicial de Obligaciones Alimentarias",
        summary=resumen,
        table_data=tabla
    )
    
    print("✓ Proceso completado con éxito. El sistema es operativo.")

if __name__ == "__main__":
    ejecutar_prueba_maestra()