"""
Tope suspensivo del interes moratorio tributario por demanda ante lo
contencioso administrativo (Sprint 84, seguimiento).

Contexto de la pregunta (docs/Preguntas-Para-Abogado-Respondidas.md, "Sprint
84 (seguimiento)"): "a los 24 meses de admitida una demanda contenciosa, el
interes deja de causarse hasta 11 dias despues de la sentencia".

Respuesta del despacho (16/11/2026): "Ambas reglas aplican de forma general a
toda obligacion tributaria. [...] Campos nuevos obligatorios en el formulario:
fecha_admision_demanda, fecha_tope_24m (calculado: admision + 24 meses),
fecha_notificacion_sentencia y fecha_reanudacion_interes (calculado:
notificacion + 11 dias)."

Decisiones de implementacion (documentadas en
docs/specifications/02_motor_financiero.md):

- Solo fecha_admision_demanda y fecha_notificacion_sentencia se guardan en la
  BD; fecha_tope_24m y fecha_reanudacion_interes se CALCULAN siempre a partir
  de ellas (nunca quedan desincronizadas).
- "+ 24 meses" es calendario: mismo dia del mes 24 meses despues; si ese dia
  no existe (29 de febrero), se topa al ultimo dia del mes. Sin corrimiento a
  dia habil (no lo pide la respuesta).
- "+ 11 dias" son dias calendario (la respuesta no dice "habiles").
- Periodo suspendido: los dias estrictamente POSTERIORES a fecha_tope_24m y
  estrictamente ANTERIORES a fecha_reanudacion_interes. El dia del tope todavia
  causa interes (completa los 24 meses) y el dia de reanudacion vuelve a
  causarlo ("reanudacion").
- Si hay admision pero aun no hay sentencia notificada, el interes queda
  suspendido desde el tope hasta la fecha de corte (la sentencia, y por lo
  tanto la reanudacion, todavia no existe).
- Si la reanudacion cae en o antes del tope (sentencia notificada antes de
  cumplirse los 24 meses), no hay suspension.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.engine.financial.rate import Rate
from app.engine.interest.provider import RateProvider
from app.engine.time.calendar import CalendarUtils

MESES_TOPE_SUSPENSIVO = 24
DIAS_REANUDACION_INTERES = 11

FUENTE_TOPE_SUSPENSIVO = (
    "Interés suspendido: tope de 24 meses desde la admisión de la demanda "
    "contencioso administrativa, hasta 11 días después de notificada la sentencia"
)

_TASA_CERO = Rate(Decimal("0"))


def calcular_fecha_tope_24m(fecha_admision_demanda: date) -> date:
    """fecha_admision_demanda + 24 meses calendario (dia topado al fin de mes)."""
    total_meses = fecha_admision_demanda.month - 1 + MESES_TOPE_SUSPENSIVO
    return CalendarUtils.safe_create_date(
        fecha_admision_demanda.year + total_meses // 12,
        total_meses % 12 + 1,
        fecha_admision_demanda.day,
    )


def calcular_fecha_reanudacion_interes(fecha_notificacion_sentencia: date) -> date:
    """fecha_notificacion_sentencia + 11 dias calendario."""
    return fecha_notificacion_sentencia + timedelta(days=DIAS_REANUDACION_INTERES)


class RateProviderConTopeSuspensivo(RateProvider):
    """Decorador de un RateProvider: devuelve 0% (con FUENTE_TOPE_SUSPENSIVO)
    para cada dia del periodo suspendido y delega en `base` para el resto.
    Se usa un decorador (y no periodos extra en el MemoryRateProvider) porque
    MemoryRateProvider asume periodos no solapados."""

    def __init__(
        self,
        base: RateProvider,
        fecha_tope_24m: date,
        fecha_reanudacion_interes: date | None,
    ):
        self._base = base
        self._fecha_tope_24m = fecha_tope_24m
        self._fecha_reanudacion_interes = fecha_reanudacion_interes

    def esta_suspendido(self, target_date: date) -> bool:
        if target_date <= self._fecha_tope_24m:
            return False
        return (
            self._fecha_reanudacion_interes is None
            or target_date < self._fecha_reanudacion_interes
        )

    def get_rate(self, target_date: date) -> Rate:
        if self.esta_suspendido(target_date):
            return _TASA_CERO
        return self._base.get_rate(target_date)

    def get_rate_source(self, target_date: date) -> str:
        if self.esta_suspendido(target_date):
            return FUENTE_TOPE_SUSPENSIVO
        return self._base.get_rate_source(target_date)
