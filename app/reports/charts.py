import matplotlib.pyplot as plt
import os

class BastiumChartGenerator:
    """Generador de evidencia gráfica inmutable para anexar a demandas."""
    
    def __init__(self):
        self.color_burgundy = "#ae1c21"
        self.color_black = "#000000"
        self.color_cream = "#f5f1e9"
        
    def generar_grafica_distribucion(self, datos_rubros: list, output_filename: str = "distribucion.png"):
        # Extraer nombres y valores para la gráfica
        conceptos = [r["concepto"] for r in datos_rubros]
        capitales = [float(r["capital"]) for r in datos_rubros]
        
        # Configurar el estilo gráfico
        fig, ax = plt.subplots(figsize=(8, 4))
        fig.patch.set_facecolor(self.color_cream)
        ax.set_facecolor(self.color_cream)
        
        # Dibujar barras horizontales (La barra más grande en Borgoña, el resto en Negro)
        colores = [self.color_burgundy if i == 0 else self.color_black for i in range(len(conceptos))]
        barras = ax.barh(conceptos, capitales, color=colores, height=0.6)
        
        # Añadir las etiquetas de valor al final de cada barra
        total_capital = sum(capitales)
        for barra in barras:
            ancho = barra.get_width()
            porcentaje = (ancho / total_capital) * 100 if total_capital > 0 else 0
            etiqueta = f"${ancho:,.0f}\n({porcentaje:.0f}%)".replace(",", ".")
            ax.text(ancho + (total_capital * 0.02), barra.get_y() + barra.get_height()/2, 
                    etiqueta, va='center', ha='left', color=self.color_burgundy, fontsize=10, fontweight='bold')
            
        # Limpiar bordes innecesarios para un look elegante
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_color(self.color_black)
        ax.spines['left'].set_color(self.color_black)
        
        # Invertir el eje Y para que el rubro mayor quede arriba
        ax.invert_yaxis()
        plt.tight_layout()
        
        ruta_grafica = os.path.join(os.getcwd(), output_filename)
        plt.savefig(ruta_grafica, dpi=300, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close()
        
        return ruta_grafica