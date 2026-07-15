from abc import ABC, abstractmethod
from datetime import date
from typing import List

from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.result import LiquidationResult


class AreaStrategy(ABC):
    """Contrato comun para el calculo de liquidacion por area del derecho."""

    @abstractmethod
    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError


class CivilFamiliaStrategy(AreaStrategy):
    """Unica estrategia operable en este sprint. Implementada en una tarea posterior."""

    def liquidar(self, obligaciones: List, abonos: List, fecha_corte: date) -> LiquidationResult:
        raise NotImplementedError("Se implementa en una tarea posterior del plan.")


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
