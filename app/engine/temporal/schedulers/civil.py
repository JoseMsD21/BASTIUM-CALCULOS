from datetime import date
from decimal import Decimal
from typing import List, Dict
from app.engine.temporal.schedulers.base import Scheduler, Event

class CivilIndemnityScheduler(Scheduler):
    """
    Generador de eventos para sentencias de Responsabilidad Civil Extracontractual.
    Agrupa los rubros indemnizatorios y los consolida en la fecha del siniestro
    o fecha de exigibilidad fijada por el juez, preparándolos para la indexación.
    """
    
    def __init__(self, fecha_hecho_danoso: date):
        self.fecha_hecho = fecha_hecho_danoso
        self._indemnizaciones: Dict[str, Decimal] = {}

    def add_indemnity(self, concept: str, amount: Decimal):
        if concept in self._indemnizaciones:
            self._indemnizaciones[concept] += amount
        else:
            self._indemnizaciones[concept] = amount

    def generate(self, start: date = None, end: date = None) -> List[Event]:
        events = []
        for concept, amount in self._indemnizaciones.items():
            if amount > Decimal("0.00"):
                events.append(Event(
                    date=self.fecha_hecho,
                    payload={"amount": amount},
                    event_type=concept
                ))
                
        return sorted(events, key=lambda e: e.date)