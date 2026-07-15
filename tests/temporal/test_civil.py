import pytest
from datetime import date
from decimal import Decimal
from app.engine.temporal.schedulers.civil import CivilIndemnityScheduler

def test_civil_indemnity_scheduler():
    # Escenario: Una sentencia condena al pago de perjuicios por un siniestro
    # ocurrido en una fecha específica.
    fecha_siniestro = date(2023, 5, 10)
    dano_emergente = Decimal("50000000.00")
    lucro_cesante = Decimal("120000000.00")
    danos_morales = Decimal("30000000.00")
    
    scheduler = CivilIndemnityScheduler(fecha_siniestro)
    scheduler.add_indemnity("DANO_EMERGENTE", dano_emergente)
    scheduler.add_indemnity("LUCRO_CESANTE_CONSOLIDADO", lucro_cesante)
    scheduler.add_indemnity("DANOS_MORALES", danos_morales)
    
    events = scheduler.generate()
    
    # Las tres obligaciones deben nacer exactamente en la fecha del siniestro 
    # para que el motor central las indexe y cause intereses desde ese día.
    assert len(events) == 3
    for e in events:
        assert e.date == fecha_siniestro
        
    lucro = next(e for e in events if e.event_type == "LUCRO_CESANTE_CONSOLIDADO")
    assert lucro.payload["amount"] == Decimal("120000000.00")