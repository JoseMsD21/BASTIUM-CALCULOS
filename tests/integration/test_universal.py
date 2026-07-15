import pytest
from datetime import date
from decimal import Decimal
from app.services.motor_universal import UniversalLiquidationService
from app.engine.temporal.schedulers.civil import CivilIndemnityScheduler
from app.engine.temporal.schedulers.base import Event
from app.domain.obligation.payment import Payment

def test_liquidar_pagare_comercial_con_abonos():
    # Caso 1: Derecho Comercial (Pagaré)
    # Deuda de 50 millones, vencida el 1 de enero. Corte a 10 de enero (10 días de mora).
    # Tasa: 0.15% diaria. Abono de 5 millones el 5 de enero.
    
    # El capital nace como un evento singular
    evento_pagare = Event(date=date(2026, 1, 1), payload={"amount": Decimal("50000000.00")}, event_type="CAPITAL_PAGARE")
    
    # Abono de rescate
    abonos = [Payment(date=date(2026, 1, 5), amount=Decimal("5000000.00"), reference="Transferencia parcial")]
    
    servicio = UniversalLiquidationService()
    resultado = servicio.liquidar(
        eventos_causacion=[evento_pagare],
        pagos=abonos,
        fecha_corte=date(2026, 1, 10),
        tasa_estatica=Decimal("0.15") # Tasa alta comercial
    )
    
    # AUDITORÍA MATEMÁTICA ESTRICTA:
    # Día 1 al 5 (4 días): 50M * 0.0015 * 4 = $300,000 de interés.
    # Día 5 (Abono): 5M matan los 300k de interés, y 4.7M de capital. Nuevo capital = 45.3M.
    # Día 5 al 10 (5 días): 45.3M * 0.0015 * 5 = $339,750 de interés.
    # Saldo final capital esperado = 45,300,000.00
    # Saldo final interés esperado = 339,750.00
    
    balance = resultado.final_balance()
    assert balance.principal == Decimal("45300000.00")
    assert balance.interest == Decimal("339750.00")

def test_liquidar_responsabilidad_civil_extracontractual():
    # Caso 2: Derecho Civil
    # Un accidente genera 3 rubros dictados en sentencia el 1 de mayo. Se liquida a 31 de mayo.
    scheduler = CivilIndemnityScheduler(fecha_hecho_danoso=date(2026, 5, 1))
    scheduler.add_indemnity("DANO_EMERGENTE", Decimal("10000000.00"))
    scheduler.add_indemnity("DANOS_MORALES", Decimal("20000000.00"))
    
    # 30 millones en total. Tasa legal comercial del 0.05% diario durante 30 días.
    eventos = scheduler.generate()
    
    servicio = UniversalLiquidationService()
    resultado = servicio.liquidar(
        eventos_causacion=eventos,
        pagos=[], # No hay pagos
        fecha_corte=date(2026, 5, 31),
        tasa_estatica=Decimal("0.05")
    )
    
    # AUDITORÍA MATEMÁTICA:
    # 30M * 0.0005 * 30 días = $450,000
    balance = resultado.final_balance()
    assert balance.principal == Decimal("30000000.00")
    assert balance.interest == Decimal("450000.00")
    assert balance.total() == Decimal("30450000.00")