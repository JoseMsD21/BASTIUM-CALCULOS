import sys
from datetime import date
from decimal import Decimal
from rich.console import Console
from rich.prompt import Prompt

# Importar nuestros nuevos motores
from app.engine.liquidation.calculator import FamilyLawCalculator
from app.reports.charts import BastiumChartGenerator
from app.reports.pdf import JudicialPDFGenerator

# Evita UnicodeEncodeError en consolas Windows con code page heredada (cp1252)
# al imprimir símbolos como "✓" con rich.
if sys.platform == "win32":
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

console = Console()

def iniciar_consola():
    console.print("[bold white on #ae1c21] BASTIUM - Ecosistema de Liquidación Forense [/bold white on #ae1c21]\n")
    console.print("[bold]Seleccione el módulo jurídico a activar:[/bold]")
    console.print("1. Obligaciones Laborales")
    console.print("2. Obligaciones Alimentarias (Art 1617 CC)")
    
    opcion = Prompt.ask("\n[bold cyan]Opción[/bold cyan]", default="2")
    
    if opcion == "2":
        console.print("\n[bold #ae1c21]--- MÓDULO DE INGESTA DE HECHOS ---[/bold #ae1c21]")
        # Para un novato, en lugar de un NLP complejo, simulamos la ingesta de varios rubros
        # En el futuro, el NLP extraerá esta lista automáticamente del texto del acta
        
        rubros_extraidos = [
            {"concepto": "Gastos Extraordinarios Salud", "capital": Decimal("427900"), "fecha": date(2025, 11, 20)},
            {"concepto": "Cuota Alimentaria Junio", "capital": Decimal("212450"), "fecha": date(2026, 6, 5)},
            {"concepto": "Gastos Educación", "capital": Decimal("110236"), "fecha": date(2025, 11, 20)}
        ]
        
        console.print("\n[bold green]✓ Múltiples rubros identificados y consolidados.[/bold green]")
        
        # 1. Instanciar la Calculadora
        calculadora = FamilyLawCalculator()
        fecha_actual = date(2026, 6, 28) # Fecha de corte del ejemplo
        
        datos_procesados = []
        for rubro in rubros_extraidos:
            resultado = calculadora.procesar_rubro(
                concepto=rubro["concepto"],
                capital=rubro["capital"],
                fecha_exigibilidad=rubro["fecha"],
                fecha_corte=fecha_actual
            )
            datos_procesados.append(resultado)
            
        console.print("\n[italic]Ejecutando motores matemáticos y dibujando gráficas...[/italic]")
        
        # 2. Generar la Gráfica
        graficador = BastiumChartGenerator()
        ruta_imagen = graficador.generar_grafica_distribucion(datos_procesados)
        
        # 3. Ensamblar el PDF
        pdf_maker = JudicialPDFGenerator("Liquidacion_Bastium.pdf")
        pdf_maker.generar_documento(datos_procesados, ruta_imagen)
        
        console.print("\n[bold green]✓ EXITO: Archivo 'Liquidacion_Bastium.pdf' generado correctamente en la carpeta raíz.[/bold green]")

if __name__ == "__main__":
    iniciar_consola()