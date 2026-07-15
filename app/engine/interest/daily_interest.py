from decimal import Decimal
from app.engine.financial.rate import Rate
from app.engine.math.rounding import Rounding

class DailyInterest:
    """
    Motor de cálculo para interés simple diario.
    Garantiza precisión absoluta utilizando la política de redondeo del sistema.
    """
    
    @staticmethod
    def calculate(capital: Decimal, daily_rate: Rate, days: int) -> Decimal:
        if days <= 0 or capital <= Decimal("0.00"):
            return Decimal("0.00")
            
        # Fórmula: I = C * i * t
        raw_interest = capital * daily_rate.decimal() * Decimal(str(days))
        
        # Nunca devolvemos floats ni Decimales con colas infinitas,
        # obligamos a pasar por el embudo de redondeo legal a 2 decimales.
        return Rounding.money(raw_interest)