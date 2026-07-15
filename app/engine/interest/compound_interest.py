from decimal import Decimal
from app.engine.financial.rate import Rate
from app.engine.math.rounding import Rounding

class CompoundInterest:
    """
    Motor de cálculo para interés compuesto.
    Calcula la capitalización de intereses sobre el saldo adeudado.
    Fórmula: Monto = Capital * (1 + tasa)^periodos
    """
    
    @staticmethod
    def calculate(capital: Decimal, period_rate: Rate, periods: int) -> Decimal:
        if periods <= 0 or capital <= Decimal("0.00"):
            return Decimal("0.00")
            
        base = Decimal("1.00") + period_rate.decimal()
        exponent = Decimal(str(periods))
        
        # Elevamos la base a la cantidad de periodos
        multiplier = base ** exponent
        total_amount = capital * multiplier
        
        # Extraemos únicamente la porción correspondiente a los intereses
        raw_interest = total_amount - capital
        
        return Rounding.money(raw_interest)