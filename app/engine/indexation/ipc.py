from decimal import Decimal
from app.engine.math.rounding import Rounding

class IPCIndexation:
    """
    Motor matemático de corrección monetaria.
    Ajusta un capital histórico a valor presente utilizando 
    los Índices de Precios al Consumidor (IPC).
    """

    @staticmethod
    def calculate(capital: Decimal, initial_index: Decimal, final_index: Decimal) -> Decimal:
        if capital <= Decimal("0.00"):
            return Decimal("0.00")
            
        if initial_index <= Decimal("0.00"):
            raise ValueError("El índice inicial del IPC no puede ser cero o negativo.")
            
        # Si hay deflación (índice final es menor), la jurisprudencia dicta que 
        # no se castiga el capital histórico del acreedor. El incremento es cero.
        if final_index <= initial_index:
            return Decimal("0.00")
            
        # Cálculo estricto: (IPC final / IPC inicial)
        # Aquí usamos alta precisión interna, el redondeo solo ocurre al final
        ratio = final_index / initial_index
        
        # Valor actualizado
        actualized_value = capital * ratio
        
        # Extraemos únicamente el delta (la indexación)
        indexation_amount = actualized_value - capital
        
        return Rounding.money(indexation_amount)