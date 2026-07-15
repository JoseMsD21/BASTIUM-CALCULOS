from typing import List, Optional
from datetime import date, timedelta
from decimal import Decimal
from app.engine.temporal.schedulers.base import Event
from app.engine.liquidation.models import PendingDebt, RunningBalance, LiquidationItem
from app.engine.liquidation.balance import BalanceEngine
from app.engine.liquidation.allocation import AllocationEngine
from app.engine.liquidation.result import LiquidationResult
from app.engine.interest.daily_interest import DailyInterest
from app.engine.financial.rate import Rate
from app.engine.interest.provider import RateProvider

class LiquidationCore:
    """
    Orquestador determinista de liquidaciones.
    Procesa eventos temporales secuenciales de cualquier dominio jurídico
    (Familia, Laboral, Civil, Comercial) e inyecta automáticamente 
    causaciones de interés por el paso del tiempo.
    """
    def __init__(self, default_daily_rate: Rate = Rate(Decimal("0.0")), rate_provider: Optional[RateProvider] = None):
        self._current_debt = PendingDebt(Decimal("0.00"), Decimal("0.00"), Decimal("0.00"))
        self._history: List[LiquidationItem] = []
        self._default_rate = default_daily_rate
        self._rate_provider = rate_provider
        self._last_event_date: Optional[date] = None

        # Diccionario de rubros jurídicos reconocidos como Capital Base
        self._capital_concepts = {
            "INSTALLMENT", "CHILD_SUPPORT", "CLOTHING", "MULTA",
            "CESANTIAS", "INTERESES_CESANTIAS", "PRIMA_JUNIO", "PRIMA_DICIEMBRE", "SANCION_MORATORIA",
            "DANO_EMERGENTE", "LUCRO_CESANTE_CONSOLIDADO", "DANOS_MORALES", "CAPITAL_PAGARE"
        }

    def process(self, chronological_events: List[Event], cutoff_date: date) -> LiquidationResult:
        sorted_events = sorted(chronological_events, key=lambda e: e.date)

        for event in sorted_events:
            if event.date > cutoff_date:
                break
                
            self._accrue_time_passage(event.date)
            item = self._process_event(event)
            self._history.append(item)
            self._last_event_date = event.date

        self._accrue_time_passage(cutoff_date)
        
        if self._last_event_date and self._last_event_date < cutoff_date:
             closing_rb = RunningBalance(
                 date=cutoff_date, 
                 debt=self._current_debt, 
                 event_type="LIQUIDATION_CUTOFF"
             )
             closing_item = LiquidationItem(
                 date=cutoff_date,
                 concept="Corte final de liquidación",
                 capital_base=self._current_debt.principal,
                 interest_rate=self._get_rate_for_date(cutoff_date).percent(),
                 interest_amount=Decimal("0.00"),
                 indexation_amount=Decimal("0.00"),
                 payment_amount=Decimal("0.00"),
                 balance=closing_rb
             )
             self._history.append(closing_item)

        return LiquidationResult(self._history)

    def _get_rate_for_date(self, target_date: date) -> Rate:
        if self._rate_provider:
            return self._rate_provider.get_rate(target_date)
        return self._default_rate

    def _accrue_time_passage(self, target_date: date):
        if not self._last_event_date or target_date <= self._last_event_date:
            return
            
        if self._current_debt.principal <= Decimal("0.00"):
            return

        current_day = self._last_event_date + timedelta(days=1)
        total_interest_accumulated = Decimal("0.00")
        
        while current_day <= target_date:
            daily_rate = self._get_rate_for_date(current_day)
            daily_interest = DailyInterest.calculate(
                capital=self._current_debt.principal, 
                daily_rate=daily_rate, 
                days=1
            )
            total_interest_accumulated += daily_interest
            current_day += timedelta(days=1)

        if total_interest_accumulated > Decimal("0.00"):
            self._current_debt = BalanceEngine.add_interest(self._current_debt, total_interest_accumulated)

    def _process_event(self, event: Event) -> LiquidationItem:
        concept = event.payload.get("label", event.event_type)
        payment_amount = Decimal("0.00")
        interest_amount = Decimal("0.00")
        indexation_amount = Decimal("0.00")

        # Enrutador de impacto patrimonial
        if event.event_type in self._capital_concepts:
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            self._current_debt = BalanceEngine.add_principal(self._current_debt, amount)

        elif event.event_type == "INTEREST":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            interest_amount = amount
            self._current_debt = BalanceEngine.add_interest(self._current_debt, amount)

        elif event.event_type == "INDEXATION":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            indexation_amount = amount
            self._current_debt = BalanceEngine.add_indexation(self._current_debt, amount)

        elif event.event_type == "PAYMENT":
            amount = Decimal(str(event.payload.get("amount", "0.00")))
            payment_amount = amount
            allocation, new_debt, remainder = AllocationEngine.allocate(amount, self._current_debt, event.date)
            self._current_debt = new_debt

        else:
            raise ValueError(
                f"Tipo de evento no reconocido: '{event.event_type}'. "
                "Debe ser uno de los conceptos de capital registrados en "
                "_capital_concepts, o bien 'INTEREST', 'INDEXATION' o 'PAYMENT'."
            )

        rb = RunningBalance(date=event.date, debt=self._current_debt, event_type=event.event_type)

        return LiquidationItem(
            date=event.date,
            concept=concept,
            capital_base=self._current_debt.principal, 
            interest_rate=self._get_rate_for_date(event.date).percent(),
            interest_amount=interest_amount,
            indexation_amount=indexation_amount,
            payment_amount=payment_amount,
            balance=rb
        )