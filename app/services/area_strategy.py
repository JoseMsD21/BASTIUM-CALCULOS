from abc import ABC, abstractmethod
from datetime import date, timedelta
from decimal import Decimal
from typing import List

from app.core.exceptions import AreaNoImplementadaError
from app.domain.obligation.payment import Payment
from app.engine.financial.rate import Rate
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.schedulers.base import Event
from app.engine.temporal.schedulers.family import FamilyScheduler
from app.services.motor_universal import UniversalLiquidationService


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError


class CivilFamiliaStrategy(AreaStrategy):
    """
    Unica area operable en este sprint.
    Interes fijo por obligacion (tasa efectiva anual pactada/legal, Art. 1617 C.C.),
    convertido a tasa diaria. No aplica indexacion IPC en este sprint (Ver Pendientes.md:
    depende de la carga de series historicas de IPC, que aun no existe).
    """

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        if not obligaciones:
            raise ValueError("Un expediente necesita al menos una obligacion para liquidar.")

        eventos_causacion: List[Event] = []
        for obligacion in obligaciones:
            eventos_causacion.extend(self._eventos_de_obligacion(obligacion, fecha_corte))

        pagos = [
            Payment(date=abono.fecha, amount=abono.monto, reference=abono.referencia or "")
            for abono in abonos
        ]

        rate_provider = self._construir_rate_provider(obligaciones, fecha_corte)

        service = UniversalLiquidationService()
        return service.liquidar(
            eventos_causacion=eventos_causacion,
            pagos=pagos,
            fecha_corte=fecha_corte,
            rate_provider=rate_provider,
        )

    def _eventos_de_obligacion(self, obligacion, fecha_corte: date) -> List[Event]:
        if obligacion.tipo.value == "PUNTUAL":
            return [
                Event(
                    date=obligacion.fecha_origen,
                    payload={"amount": obligacion.valor, "label": obligacion.concepto},
                    event_type=obligacion.categoria,
                )
            ]

        # RECURRENTE
        scheduler = FamilyScheduler()
        scheduler.add_monthly_obligation(
            amount=obligacion.valor,
            concept=obligacion.concepto,
            due_day=obligacion.dia_pago,
            category=obligacion.categoria,
        )
        fin = obligacion.fecha_fin or fecha_corte
        return scheduler.generate(start=obligacion.fecha_inicio, end=fin)

    def _construir_rate_provider(self, obligaciones: List, fecha_corte: date) -> MemoryRateProvider:
        fecha_mas_antigua = min(
            o.fecha_origen if o.tipo.value == "PUNTUAL" else o.fecha_inicio for o in obligaciones
        )
        # Usamos la tasa de la primera obligacion como tasa unica del expediente.
        # (Multiples tasas simultaneas por obligacion quedan fuera de alcance de este sprint.)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(obligaciones[0].tasa_efectiva_anual)

        provider = MemoryRateProvider()
        provider.add_rate_period(
            start=fecha_mas_antigua - timedelta(days=1), end=fecha_corte, rate=tasa_diaria
        )
        return provider


class ComercialStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Comercial (interes 1.5x IBC + validacion de usura) esta pendiente. Ver Pendientes.md."
        )


class LaboralStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Laboral (Art. 65 CST, vacaciones) esta pendiente. Ver Pendientes.md."
        )


class SancionatorioStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Sancionatorio (conversion SMLMV a UVT) esta pendiente. Ver Pendientes.md."
        )


class HonorariosStrategy(AreaStrategy):
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise AreaNoImplementadaError(
            "El area Honorarios (cuota litis) esta pendiente. Ver Pendientes.md."
        )
