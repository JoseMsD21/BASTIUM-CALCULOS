import pytest
from datetime import date
from decimal import Decimal
from app.engine.temporal.schedulers.labor import LaborScheduler

def test_labor_scheduler_generates_statutory_events_full_year():
    # Escenario: Trabajador con salario base de $1,500,000 en el año 2025 (trabajó 360 días)
    salario = Decimal("1500000.00")
    dias_trabajados = 360
    anio_causacion = 2025
    
    scheduler = LaborScheduler(salario_base=salario, dias_trabajados=dias_trabajados, anio=anio_causacion)
    events = scheduler.generate()
    
    # Deben generarse 4 eventos ineludibles: 
    # 1. Prima Junio (15 días)
    # 2. Prima Diciembre (15 días)
    # 3. Intereses Cesantías (12% sobre el saldo)
    # 4. Cesantías (30 días)
    assert len(events) == 4
    
    # Verificación de fechas de exigibilidad estáticas y montos exactos
    prima_junio = next(e for e in events if e.event_type == "PRIMA_JUNIO")
    assert prima_junio.date == date(2025, 6, 30)
    assert prima_junio.payload["amount"] == Decimal("750000.00") # Mitad del salario
    
    prima_dic = next(e for e in events if e.event_type == "PRIMA_DICIEMBRE")
    assert prima_dic.date == date(2025, 12, 20)
    assert prima_dic.payload["amount"] == Decimal("750000.00")
    
    int_cesantias = next(e for e in events if e.event_type == "INTERESES_CESANTIAS")
    assert int_cesantias.date == date(2026, 1, 31) # Exigibles al año siguiente
    assert int_cesantias.payload["amount"] == Decimal("180000.00") # 1.5M * 12%
    
    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    assert cesantias.date == date(2026, 2, 14) # Límite de consignación en fondo
    assert cesantias.payload["amount"] == Decimal("1500000.00")

def test_labor_scheduler_proportional_days():
    # Escenario: Trabajo parcial de 180 días
    scheduler = LaborScheduler(Decimal("1000000.00"), 180, 2025)
    events = scheduler.generate()
    
    cesantias = next(e for e in events if e.event_type == "CESANTIAS")
    # (1M * 180) / 360 = 500,000
    assert cesantias.payload["amount"] == Decimal("500000.00")