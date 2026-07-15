from datetime import date
from decimal import Decimal
from typing import List
from app.engine.temporal.schedulers.base import Scheduler, Event
from app.engine.math.rounding import Rounding

class LaborScheduler(Scheduler):
    """
    Generador de obligaciones estatutarias del Derecho Laboral Colombiano.
    Calcula prestaciones sociales y asigna fechas de exigibilidad inflexibles.
    """
    
    def __init__(self, salario_base: Decimal, dias_trabajados: int, anio: int):
        self.salario = salario_base
        self.dias = Decimal(str(dias_trabajados))
        self.anio = anio
        self.base_anual = Decimal("360")

    def generate(self, start: date = None, end: date = None) -> List[Event]:
        events = []
        
        # 1. Cesantías (Exigibles a 14 de Febrero del año siguiente)
        monto_cesantias = Rounding.money((self.salario * self.dias) / self.base_anual)
        events.append(Event(
            date=date(self.anio + 1, 2, 14),
            payload={"amount": monto_cesantias},
            event_type="CESANTIAS"
        ))
        
        # 2. Intereses a las Cesantías (Exigibles a 31 de Enero del año siguiente)
        monto_intereses = Rounding.money((monto_cesantias * self.dias * Decimal("0.12")) / self.base_anual)
        events.append(Event(
            date=date(self.anio + 1, 1, 31),
            payload={"amount": monto_intereses},
            event_type="INTERESES_CESANTIAS"
        ))
        
        # 3. Primas (Corrección matemática implacable: Denominador 360)
        dias_semestre = self.dias / Decimal("2")
        monto_prima_semestral = Rounding.money((self.salario * dias_semestre) / self.base_anual)
        
        if self.dias > Decimal("0.00"):
            events.append(Event(
                date=date(self.anio, 6, 30),
                payload={"amount": monto_prima_semestral},
                event_type="PRIMA_JUNIO"
            ))
            events.append(Event(
                date=date(self.anio, 12, 20),
                payload={"amount": monto_prima_semestral},
                event_type="PRIMA_DICIEMBRE"
            ))
            
        return sorted(events, key=lambda e: e.date)