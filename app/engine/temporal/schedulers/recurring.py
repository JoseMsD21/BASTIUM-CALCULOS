from datetime import date
from decimal import Decimal
from typing import List
from dataclasses import dataclass
from app.engine.temporal.schedulers.base import Scheduler, Event
from app.engine.time.calendar import CalendarUtils

@dataclass
class RecurringRule:
    amount: Decimal
    frequency: str  # "monthly", "yearly"
    day: int
    month: int = 1

class RecurringScheduler(Scheduler):
    """
    Generador de eventos recurrentes determinista.
    Aplica matemáticas de fechas seguras y previene bucles infinitos.
    """
    def __init__(self, rule: RecurringRule, event_type: str, label: str = None):
        self.rule = rule
        self.event_type = event_type
        self.label = label

    def generate(self, start: date, end: date) -> List[Event]:
        events = []
        current_year = start.year
        current_month = start.month

        while True:
            # 1. Proyectar la fecha teórica
            if self.rule.frequency == "monthly":
                event_date = CalendarUtils.safe_create_date(current_year, current_month, self.rule.day)
            elif self.rule.frequency == "yearly":
                event_date = CalendarUtils.safe_create_date(current_year, self.rule.month, self.rule.day)
            else:
                raise ValueError("Frecuencia no soportada por el motor.")

            # 2. Condición de salida estricta: El tiempo solo avanza. 
            # Si superamos la fecha final, rompemos inmediatamente.
            if event_date > end:
                break

            # 3. Si la fecha está dentro de la ventana, la causamos.
            if event_date >= start:
                payload = {"amount": self.rule.amount}
                if self.label:
                    payload["label"] = self.label
                events.append(
                    Event(
                        date=event_date,
                        payload=payload,
                        event_type=self.event_type
                    )
                )

            # 4. Avanzar los engranajes del tiempo
            if self.rule.frequency == "monthly":
                current_month += 1
                if current_month > 12:
                    current_month = 1
                    current_year += 1
            elif self.rule.frequency == "yearly":
                current_year += 1

        return events