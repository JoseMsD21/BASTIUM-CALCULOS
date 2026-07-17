from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal
from dataclasses import dataclass
from typing import List
from app.engine.financial.rate import Rate

class RateProvider(ABC):
    """
    Contrato estricto para cualquier repositorio de tasas de interés.
    Garantiza que el motor matemático pueda aislarse de la base de datos.
    """
    @abstractmethod
    def get_rate(self, target_date: date) -> Rate:
        pass

    def get_rate_source(self, target_date: date) -> str:
        """
        Fuente/vigencia de la tasa aplicada en target_date, para trazabilidad de auditoría.
        Método concreto con default "N/A" -- los proveedores que no la modelan no están
        obligados a implementarlo.
        """
        return "N/A"

@dataclass(frozen=True)
class RatePeriod:
    start_date: date
    end_date: date
    rate: Rate
    source: str = "N/A"

class MemoryRateProvider(RateProvider):
    """
    Proveedor en memoria para inyección en pruebas unitarias y casos estáticos.
    """
    def __init__(self):
        self._periods: List[RatePeriod] = []

    def add_rate_period(self, start: date, end: date, rate: Rate, source: str = "N/A"):
        self._periods.append(RatePeriod(start, end, rate, source))
        # Mantener la lista estrictamente ordenada para optimizar la búsqueda
        self._periods.sort(key=lambda p: p.start_date)

    def get_rate(self, target_date: date) -> Rate:
        for period in self._periods:
            if period.start_date <= target_date <= period.end_date:
                return period.rate
        raise ValueError(f"No se encontró una tasa configurada para la fecha {target_date.strftime('%Y-%m-%d')}")

    def get_rate_source(self, target_date: date) -> str:
        for period in self._periods:
            if period.start_date <= target_date <= period.end_date:
                return period.source
        raise ValueError(f"No se encontró una tasa configurada para la fecha {target_date.strftime('%Y-%m-%d')}")
