from datetime import date
from decimal import Decimal
from typing import List
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.engine.temporal.schedulers.base import Event
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.result import LiquidationResult
from app.engine.financial.rate import Rate
from app.domain.obligation.payment import Payment

class AlimentosLiquidationService:
    """
    Fachada de Orquestación.
    Convierte los parámetros jurídicos de una demanda de familia en 
    una liquidación matemática estructurada y lista para presentación judicial.
    """
    
    def liquidar(
        self,
        fecha_inicio: date,
        fecha_corte: date,
        cuota_mensual: Decimal,
        dia_pago: int,
        tasa_diaria_porcentaje: Decimal,
        pagos: List[Payment]
    ) -> LiquidationResult:
        
        # 1. Configurar la Tasa de Interés Moratorio Legal/Pactada
        tasa_mora = Rate.from_percent(tasa_diaria_porcentaje)
        
        # 2. Motor Temporal: Proyectar las obligaciones fijas en el tiempo
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=cuota_mensual,
            concept="Cuota Alimentaria",
            due_day=dia_pago
        )
        
        # Extraer los eventos de deuda (el calendario ideal)
        eventos_deuda = scheduler.generate(start=fecha_inicio, end=fecha_corte)
        
        # 3. Mapear los Abonos/Pagos a la estructura de Eventos del Motor
        eventos_pago = []
        for pago in pagos:
            # Descartamos pagos fuera del rango de la liquidación actual
            if fecha_inicio <= pago.date <= fecha_corte:
                evt = Event(
                    date=pago.date,
                    payload={"amount": pago.amount, "reference": pago.reference},
                    event_type="PAYMENT"
                )
                eventos_pago.append(evt)
                
        # 4. Fusión de la Realidad (Deudas + Pagos)
        historia_completa = eventos_deuda + eventos_pago
        
        # 5. Iniciar la máquina de estados determinista
        motor_calculo = LiquidationCore(default_daily_rate=tasa_mora)
        
        # 6. Procesar y retornar la verdad jurídica absoluta
        resultado_final = motor_calculo.process(
            chronological_events=historia_completa,
            cutoff_date=fecha_corte
        )
        
        return resultado_final