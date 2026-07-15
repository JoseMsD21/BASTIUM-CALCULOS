import pytest
from datetime import date
from decimal import Decimal
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.recurring import RecurringRule, RecurringScheduler
from app.engine.temporal.schedulers.family import FamilyScheduler

def test_monthly_scheduler_handles_end_of_month():
    rule = RecurringRule(
        amount=Decimal("300000.00"), 
        frequency="monthly", 
        day=31
    )
    scheduler = RecurringScheduler(rule, "INSTALLMENT")
    
    # CORRECCIÓN: Ampliamos la ventana hasta el 31 de marzo.
    events = scheduler.generate(date(2024, 1, 1), date(2024, 3, 31))
    
    assert len(events) == 3
    assert events[0].date == date(2024, 1, 31)
    assert events[1].date == date(2024, 2, 29) # Bisiesto procesado correctamente
    assert events[2].date == date(2024, 3, 31)

def test_family_scheduler_facade():
    scheduler = FamilyScheduler()
    scheduler.add_monthly_obligation(Decimal("500000.00"), "CHILD_SUPPORT", 5)
    scheduler.add_yearly_obligation(Decimal("500000.00"), "CLOTHING", month=6, day=15)
    
    events = scheduler.generate(date(2025, 1, 1), date(2025, 12, 31))
    
    assert len(events) == 13
    june_events = [e for e in events if e.date.month == 6]
    assert len(june_events) == 2
    assert june_events[0].date == date(2025, 6, 5)
    assert june_events[1].date == date(2025, 6, 15)