"""
Interes moratorio tributario (Estatuto Tributario, art. 635): tasa de usura
vigente (linea Consumo y Ordinario) menos dos puntos porcentuales. A
diferencia del interes moratorio comercial (que puede pactarse), esta tasa
nunca se pacta -- se deriva mecanicamente de la serie historica de usura de
la SFC. Por eso este motor resuelve la tasa automaticamente por tramos
historicos en vez de recibir una tasa manual (comparar con
ComercialStrategy._construir_rate_provider en app/services/area_strategy.py,
que sí usa una tasa pactada).

Ver docs/superpowers/specs/2026-07-20-sprint11a-tributario-interes-renta-liquida-design.md.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import get_tramos_ibc_usura_between
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.provider import MemoryRateProvider
from app.engine.interest.rate_conversion import EffectiveRateConverter

PUNTOS_DESCUENTO_ET_635 = Decimal("2")

FUENTE_MORATORIO_TRIBUTARIO = "Interes moratorio tributario (E.T. art. 635): usura vigente - 2 puntos"


def construir_rate_provider_moratorio_tributario(
    fecha_exigibilidad: date, fecha_corte: date
) -> MemoryRateProvider:
    """Un RatePeriod diario por cada tramo historico de usura que se solape
    con el rango de mora [fecha_exigibilidad + 1 dia, fecha_corte] (la mora
    empieza el dia siguiente a la exigibilidad, mismo criterio que
    R-CIV-003). Si fecha_corte no supera ese inicio de mora, no hay mora:
    retorna un provider vacio."""
    provider = MemoryRateProvider()

    inicio_mora = fecha_exigibilidad + timedelta(days=1)
    if fecha_corte < inicio_mora:
        return provider

    tramos = get_tramos_ibc_usura_between(inicio_mora, fecha_corte)
    for tramo in tramos:
        inicio_segmento = max(tramo.inicio, inicio_mora)
        fin_segmento = min(tramo.fin, fecha_corte)
        tasa_anual_tributaria = tramo.usura_anual - PUNTOS_DESCUENTO_ET_635
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tasa_anual_tributaria)
        provider.add_rate_period(
            start=inicio_segmento,
            end=fin_segmento,
            rate=tasa_diaria,
            source=FUENTE_MORATORIO_TRIBUTARIO,
        )
    return provider
