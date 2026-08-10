import bisect
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date

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
        self._periods: list[RatePeriod] = []
        self._start_dates: list[date] = []

    def add_rate_period(self, start: date, end: date, rate: Rate, source: str = "N/A"):
        self._periods.append(RatePeriod(start, end, rate, source))
        # Mantener la lista estrictamente ordenada para optimizar la búsqueda
        self._periods.sort(key=lambda p: p.start_date)
        self._start_dates = [period.start_date for period in self._periods]

    def _buscar_periodo(self, target_date: date) -> RatePeriod | None:
        """Búsqueda binaria (bisect) sobre self._periods, que add_rate_period
        mantiene ordenada por start_date: localiza el último periodo cuyo
        start_date es <= target_date en O(log n) en vez del scan lineal O(n)
        anterior (Sprint 25, hallazgo 1 -- _accrue_time_passage llama a
        get_rate una vez por cada día de mora, miles de llamadas para
        procesos con años de mora). Asume periodos no solapados -- ninguno de
        los productores actuales (area_strategy.py, moratory_interest.py) los
        solapa; si algún día se necesitan periodos solapados, esta búsqueda ya
        no sería correcta y habría que volver al scan lineal o agregar
        desempate explícito."""
        indice = bisect.bisect_right(self._start_dates, target_date) - 1
        if indice < 0:
            return None
        periodo = self._periods[indice]
        if periodo.start_date <= target_date <= periodo.end_date:
            return periodo
        return None

    def get_rate(self, target_date: date) -> Rate:
        periodo = self._buscar_periodo(target_date)
        if periodo is None:
            raise ValueError(
                "No se encontró una tasa configurada para la fecha "
                f"{target_date.strftime('%Y-%m-%d')}"
            )
        return periodo.rate

    def get_rate_source(self, target_date: date) -> str:
        periodo = self._buscar_periodo(target_date)
        if periodo is None:
            raise ValueError(
                "No se encontró una tasa configurada para la fecha "
                f"{target_date.strftime('%Y-%m-%d')}"
            )
        return periodo.source
