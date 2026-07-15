import pytest
from decimal import Decimal
from app.engine.indexation.ipc import IPCIndexation
from app.engine.indexation.smmlv import SMMLVCalculator

def test_ipc_indexation_calculation():
    # Escenario real:
    # Capital base: $1,000,000
    # IPC Inicial (Ej: Enero 2020): 103.54
    # IPC Final (Ej: Diciembre 2023): 138.60
    capital = Decimal("1000000.00")
    ipc_inicial = Decimal("103.54")
    ipc_final = Decimal("138.60")
    
    # La fórmula es: (1000000 * (138.60 / 103.54)) - 1000000
    # 138.60 / 103.54 = 1.338613096...
    # Valor actualizado = 1,338,613.10
    # Indexación pura (solo el incremento) = 338,613.10
    
    indexacion = IPCIndexation.calculate(capital, ipc_inicial, ipc_final)
    
    assert indexacion == Decimal("338613.10")

def test_ipc_indexation_no_inflation_returns_zero():
    # Si el índice inicial y final es el mismo, la indexación debe ser 0.
    capital = Decimal("500000.00")
    ipc = Decimal("120.00")
    
    indexacion = IPCIndexation.calculate(capital, ipc, ipc)
    assert indexacion == Decimal("0.00")

def test_ipc_deflation_does_not_reduce_capital():
    # En derecho colombiano, la deflación (IPC negativo) por regla general 
    # no reduce el capital histórico adeudado en perjuicio del acreedor alimentario.
    capital = Decimal("1000000.00")
    ipc_inicial = Decimal("120.00")
    ipc_final = Decimal("118.00") # Hubo deflación
    
    indexacion = IPCIndexation.calculate(capital, ipc_inicial, ipc_final)
    
    # El incremento por indexación debe ser 0, nunca negativo.
    assert indexacion == Decimal("0.00")

def test_smmlv_to_pesos_conversion():
    # Escenario: Cuota alimentaria pactada en 0.5 SMMLV
    # SMMLV del año: $1,300,000.00
    smmlv_ratio = Decimal("0.5")
    smmlv_value = Decimal("1300000.00")
    
    valor_pesos = SMMLVCalculator.to_pesos(smmlv_ratio, smmlv_value)
    
    # Matemáticas: 1,300,000 * 0.5 = 650,000.00
    assert valor_pesos == Decimal("650000.00")