from decimal import Decimal
from datetime import date

class FamilyLawCalculator:
    """Motor de cálculo para obligaciones de familia (Alimentos, Salud, Educación)."""
    
    def __init__(self):
        # Tasa diaria del 6% anual civil: 0.06 / 365
        self.tasa_diaria = Decimal("0.000159653587")
    
    def calcular_dias_mora(self, fecha_exigibilidad: date, fecha_corte: date) -> int:
        delta = fecha_corte - fecha_exigibilidad
        return max(0, delta.days)
    
    def procesar_rubro(self, concepto: str, capital: Decimal, fecha_exigibilidad: date, fecha_corte: date) -> dict:
        dias_mora = self.calcular_dias_mora(fecha_exigibilidad, fecha_corte)
        
        # Aplicación estricta de la fórmula judicial
        # Intereses = Capital * Tasa Diaria * Días
        interes_generado = capital * self.tasa_diaria * Decimal(dias_mora)
        
        return {
            "concepto": concepto,
            "capital": capital,
            "dias_mora": dias_mora,
            "intereses": round(interes_generado, 2),
            "total_rubro": round(capital + interes_generado, 2)
        }