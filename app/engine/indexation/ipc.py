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

    @staticmethod
    def deflactar(capital: Decimal, initial_index: Decimal, final_index: Decimal) -> Decimal:
        """
        Desindexa (deflacta) una cantidad única a valor de una fecha anterior:
        VA = VH * IPC_Inicial / IPC_Final (X7.INDEXACION-CANTIDAD-UNICA.md,
        Sprint 101 en docs/Pendientes.md). Es el inverso matematico de la
        razon que usa calculate() (IPC_Final/IPC_Inicial), pero a diferencia
        de calculate() -- que devuelve solo el delta/incremento y nunca un
        valor negativo (por el guard de deflacion del art. 21 Ley 100) --
        deflactar() devuelve el VALOR ACTUALIZADO COMPLETO (VA), sin ningun
        guard: es una calculadora distinta, para un caso de uso distinto
        (retrotraer intencionalmente una cifra a una fecha anterior, no
        protegerse de una deflacion real durante la mora). No conectada
        todavia a ningun flujo de captura/liquidacion real.
        """
        if capital <= Decimal("0.00"):
            return Decimal("0.00")

        if final_index <= Decimal("0.00"):
            raise ValueError("El índice final del IPC no puede ser cero o negativo.")

        ratio = initial_index / final_index
        actualized_value = capital * ratio

        return Rounding.money(actualized_value)