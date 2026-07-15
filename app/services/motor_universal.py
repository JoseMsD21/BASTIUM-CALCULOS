from datetime import date
from decimal import Decimal
from typing import List, Optional
from app.engine.temporal.schedulers.base import Event
from app.engine.liquidation.engine import LiquidationCore
from app.engine.liquidation.result import LiquidationResult
from app.engine.financial.rate import Rate
from app.engine.interest.provider import RateProvider
from app.domain.obligation.payment import Payment

class UniversalLiquidationService:
    """
    Fachada de Integración Universal.
    Acepta eventos jurídicos de cualquier rama del derecho (Laboral, Civil, Comercial, Familia)
    los fusiona con pagos realizados en la vida real, y acciona el núcleo determinista.
    """
    
    def liquidar(
        self,
        eventos_causacion: List[Event],
        pagos: List[Payment],
        fecha_corte: date,
        tasa_estatica: Decimal = Decimal("0.0"),
        rate_provider: Optional[RateProvider] = None
    ) -> LiquidationResult:
        
        # 1. Configurar la política de mora
        tasa_mora = Rate.from_percent(tasa_estatica)
        
        # 2. Conversión de abonos físicos a eventos financieros inmutables
        eventos_pago = []
        for pago in pagos:
            if pago.date <= fecha_corte:
                eventos_pago.append(Event(
                    date=pago.date,
                    payload={"amount": pago.amount, "reference": pago.reference},
                    event_type="PAYMENT"
                ))
                
        # 3. Fusión del historial: Nacimiento de la deuda + Amortizaciones
        historia_completa = eventos_causacion + eventos_pago
        
        # 4. Instanciación del Motor Core con inyección de dependencias
        motor_calculo = LiquidationCore(
            default_daily_rate=tasa_mora,
            rate_provider=rate_provider
        )
        
        # 5. Ejecución del procesamiento temporal implacable
        return motor_calculo.process(
            chronological_events=historia_completa,
            cutoff_date=fecha_corte
        )