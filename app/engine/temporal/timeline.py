from datetime import date, timedelta
from decimal import Decimal

class TimelineEngine:

    def __init__(self, events, interest_rate):

        self.events = sorted(events, key=lambda e: e.date)
        self.interest_rate = Decimal(str(interest_rate))

        self.balance = Decimal("0.00")
        self.interest = Decimal("0.00")

        self.ledger = []

    def run(self, start: date, end: date):

        current = start
        event_index = 0

        while current <= end:

            # 1. aplicar eventos del día
            while (
                event_index < len(self.events)
                and self.events[event_index].date == current
            ):
                event = self.events[event_index]

                self._apply_event(event)

                event_index += 1

            # 2. causación diaria de interés
            self._accrue_interest()

            # 3. registrar estado diario
            self._snapshot(current)

            current += timedelta(days=1)

        return self.ledger

    def _apply_event(self, event):

        if event.event_type in ["CHILD_SUPPORT", "CLOTHING", "BIRTHDAY"]:

            self.balance += Decimal(str(event.payload["amount"]))

        elif event.event_type == "PAYMENT":

            amount = Decimal(str(event.payload["amount"]))

            # imputación primero intereses
            if amount >= self.interest:
                amount -= self.interest
                self.interest = Decimal("0.00")
            else:
                self.interest -= amount
                return

            # luego capital
            self.balance -= amount

    def _accrue_interest(self):

        if self.balance <= 0:
            return

        daily = self.balance * self.interest_rate

        self.interest += daily.quantize(Decimal("0.01"))

    def _snapshot(self, current_date):

        self.ledger.append({
            "date": current_date,
            "balance": float(self.balance),
            "interest": float(self.interest),
            "total": float(self.balance + self.interest)
        })