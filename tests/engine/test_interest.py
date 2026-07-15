import pytest
from decimal import Decimal
from app.engine.financial.rate import Rate
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.monthly_interest import MonthlyInterest
from app.engine.interest.compound_interest import CompoundInterest

def test_daily_interest_calculation():
    # Escenario: Capital de $1,000,000 a una tasa diaria del 0.1% durante 15 días.
    capital = Decimal("1000000.00")
    rate = Rate.from_percent(Decimal("0.1")) # 0.1%
    days = 15
    
    interest = DailyInterest.calculate(capital, rate, days)
    
    # Matemáticas: 1,000,000 * 0.001 * 15 = 15,000.00
    assert interest == Decimal("15000.00")

def test_monthly_interest_calculation():
    # Escenario: Capital de $500,000 a una tasa mensual del 1.5% durante 3 meses.
    capital = Decimal("500000.00")
    rate = Rate.from_percent(Decimal("1.5")) # 1.5%
    months = 3
    
    interest = MonthlyInterest.calculate(capital, rate, months)
    
    # Matemáticas: 500,000 * 0.015 * 3 = 22,500.00
    assert interest == Decimal("22500.00")

def test_compound_interest_calculation():
    # Escenario: Capital de $100,000 a una tasa del 5% por periodo, capitalizado 3 veces.
    capital = Decimal("100000.00")
    rate = Rate.from_percent(Decimal("5.0")) # 5%
    periods = 3
    
    interest = CompoundInterest.calculate(capital, rate, periods)
    
    # Matemáticas: 100,000 * (1 + 0.05)^3 = 115,762.50
    # Interés puro = 115,762.50 - 100,000 = 15,762.50
    assert interest == Decimal("15762.50")

def test_interest_with_zero_or_negative_time_returns_zero():
    capital = Decimal("1000000.00")
    rate = Rate.from_percent(Decimal("1.0"))
    
    assert DailyInterest.calculate(capital, rate, 0) == Decimal("0.00")
    assert MonthlyInterest.calculate(capital, rate, -5) == Decimal("0.00")