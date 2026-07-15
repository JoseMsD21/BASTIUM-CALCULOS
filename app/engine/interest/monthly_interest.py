from decimal import Decimal
from app.engine.financial.rate import Rate
from app.engine.math.rounding import Rounding

class MonthlyInterest:
    """
    Motor de cálculo para interés simple mensual.
    Ideal para obligaciones de familia (alimentos) donde la mora
    se suele pactar o calcular por meses completos.
    """
    
    @staticmethod
    def calculate(capital: Decimal, monthly_rate: Rate, months: int) -> Decimal:
        if months <= 0 or capital <= Decimal("0.00"):
            return Decimal("0.00")
            
        # Fórmula: I = C * i * t
        raw_interest = capital * monthly_rate.decimal() * Decimal(str(months))
        return Rounding.money(raw_interest)