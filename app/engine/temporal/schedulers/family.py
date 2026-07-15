from datetime import date
from decimal import Decimal
from typing import List
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.recurring import RecurringRule, RecurringScheduler

class FamilyScheduler:
    """
    Orquestador especializado para Derecho de Familia.
    Transforma autos interlocutorios y sentencias en una cronología
    estricta de eventos procesables por el motor de liquidación[cite: 1].
    """
    def __init__(self):
        self.schedulers: List[RecurringScheduler] = []

    def add_monthly_obligation(self, amount: Decimal, concept: str, due_day: int, category: str = "CHILD_SUPPORT"):
        rule = RecurringRule(
            amount=amount,
            frequency="monthly",
            day=due_day
        )
        self.schedulers.append(RecurringScheduler(rule, category, concept))

    def add_yearly_obligation(self, amount: Decimal, concept: str, month: int, day: int, category: str = "CHILD_SUPPORT"):
        rule = RecurringRule(
            amount=amount,
            frequency="yearly",
            month=month,
            day=day
        )
        self.schedulers.append(RecurringScheduler(rule, category, concept))

    def generate(self, start: date, end: date) -> List[Event]:
        events = []
        for scheduler in self.schedulers:
            events.extend(scheduler.generate(start, end))
            
        # El motor de liquidación exige orden cronológico absoluto
        return sorted(events, key=lambda e: e.date)