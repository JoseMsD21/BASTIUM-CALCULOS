from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal


class TRMProvider(ABC):
    """
    Contrato para cualquier fuente de TRM (Tasa Representativa del Mercado,
    Art. 874 C.Co.) usada para convertir obligaciones en moneda extranjera a
    pesos colombianos. Mismo patron que RateProvider (app/engine/interest/provider.py).
    """

    @abstractmethod
    def get_trm(self, fecha_referencia: date) -> Decimal:
        pass


class ManualTRMProvider(TRMProvider):
    """
    Proveedor MVP (Sprint 12): la TRM ya viene decidida por el abogado
    (Obligacion.trm_aplicable) -- no se busca en ninguna serie historica,
    porque el PDF fuente de BASTIUM no trae una (a diferencia de SMLMV/IPC/IBC,
    ver docs/superpowers/specs/2026-07-20-sprint12-trm-moneda-extranjera-design.md).
    Reemplazable por un HistoricalTRMProvider el dia que exista una serie real,
    sin tocar ComercialStrategy.
    """

    def __init__(self, trm: Decimal):
        self._trm = trm

    def get_trm(self, fecha_referencia: date) -> Decimal:
        return self._trm
