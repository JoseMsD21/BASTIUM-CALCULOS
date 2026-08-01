import json
import urllib.error
import urllib.parse
import urllib.request
from abc import ABC, abstractmethod
from datetime import date
from decimal import Decimal

from app.core.exceptions import TRMNoDisponibleError


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


class SFCTRMProvider(TRMProvider):
    """
    Proveedor de TRM en vivo (Sprint 12, correccion 2026-08-01): respuesta del
    despacho (Preguntas-Para-Abogado.md) exige "consumir la TRM de la API de la
    Superintendencia Financiera correspondiente a la Fecha_de_Pago" en vez de
    una TRM fija digitada por el abogado -- reemplaza a ManualTRMProvider como
    proveedor por defecto de ComercialStrategy.

    Consulta el dataset abierto que datos.gov.co (portal de datos abiertos del
    Estado colombiano) publica como espejo REST del servicio web SOAP oficial
    de la SFC (mismo dato certificado, formato JSON mas simple de consumir) --
    no se agrega una dependencia HTTP nueva, se usa `urllib` de la libreria
    estandar. ManualTRMProvider se conserva para tests (sin red) y como
    referencia del contrato `TRMProvider`.
    """

    _ENDPOINT = "https://www.datos.gov.co/resource/32sa-8pi3.json"

    def __init__(self, timeout_segundos: int = 10):
        self._timeout_segundos = timeout_segundos

    def get_trm(self, fecha_referencia: date) -> Decimal:
        fecha_iso = fecha_referencia.isoformat()
        query = urllib.parse.urlencode({
            "$where": (
                f"vigenciadesde<='{fecha_iso}T23:59:59' AND "
                f"vigenciahasta>='{fecha_iso}T00:00:00'"
            ),
            "$order": "vigenciadesde DESC",
            "$limit": "1",
        })
        url = f"{self._ENDPOINT}?{query}"
        try:
            with urllib.request.urlopen(url, timeout=self._timeout_segundos) as response:
                datos = json.loads(response.read())
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
            raise TRMNoDisponibleError(
                f"No se pudo consultar la TRM de la Superintendencia Financiera "
                f"para {fecha_referencia}: {error}"
            ) from error

        if not datos:
            raise TRMNoDisponibleError(
                f"La Superintendencia Financiera no tiene TRM certificada para {fecha_referencia}."
            )

        return Decimal(datos[0]["valor"])
