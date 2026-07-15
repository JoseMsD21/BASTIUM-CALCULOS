from decimal import Decimal
from app.engine.math.rounding import Rounding

class SMMLVCalculator:
    """
    Conversor de fracciones o múltiplos de Salario Mínimo Legal Mensual Vigente
    a pesos colombianos líquidos para un año específico.
    """

    @staticmethod
    def to_pesos(smmlv_quantity: Decimal, current_year_smmlv: Decimal) -> Decimal:
        """
        Convierte una cantidad de SMMLV a moneda circulante.
        Ejemplo: 0.5 SMMLV a 1,300,000 = 650,000.00
        """
        if smmlv_quantity <= Decimal("0.00") or current_year_smmlv <= Decimal("0.00"):
            return Decimal("0.00")
            
        raw_value = smmlv_quantity * current_year_smmlv
        
        return Rounding.money(raw_value)