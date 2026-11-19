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

Division lineal 365/366 dias (Sprint 84, respuesta del despacho 22/08/2026):
"a diferencia del sistema financiero NIIF, el Estatuto Tributario exige la
liquidacion por interes simple y division lineal para igualar los calculos
oficiales de la DIAN y evitar el anatocismo tributario" -- tasa_diaria =
tasa_anual_tributaria / dias_del_anio (365, o 366 en año bisiesto), SIN
exponente, a diferencia de EffectiveRateConverter.annual_to_daily (formula
compuesta) que usa el resto del motor para el interes civil del 6%. Antes de
esta respuesta el motor usaba por error la formula compuesta -- ver el
historial de este docstring para la discrepancia ya documentada desde el
primer cierre del Sprint 84.

La misma respuesta trajo ademas dos reglas nuevas que quedan FUERA de
alcance de este cambio (no implementadas, documentadas como seguimiento en
docs/Preguntas-Para-Abogado-Abiertas.md, Sprint 84 (seguimiento)): (1)
"Imputacion Proporcional" (Art. 804 E.T.) -- un abono se reparte
proporcionalmente entre capital/sancion/interes en vez de la regla civil de
intereses primero, y (2) un "Tope Suspensivo" que congela el interes 24
meses despues de admitida una demanda contenciosa hasta 11 dias despues de
la sentencia. Ninguna de las dos es la pregunta que motivo este sprint (la
convencion de dias del año), y ambas requieren datos (fecha de admision de
demanda, fecha de sentencia, reglas de imputacion propias de Tributario) que
el modelo actual no captura -- se documentan para no perderlas, no se
implementan a ciegas.
"""

import calendar
from datetime import date, timedelta
from decimal import Decimal

from app.engine.financial.rate import Rate
from app.engine.indexation.historical_index import (
    PENDIENTE_CERTIFICACION_OFICIAL,
    get_tramos_ibc_usura_between,
    get_ultima_fecha_certificada_ibc_usura,
)
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.provider import MemoryRateProvider
from app.services.parametro_service import get_parametro

PUNTOS_DESCUENTO_ET_635 = Decimal("2")

FUENTE_MORATORIO_TRIBUTARIO = (
    "Interes moratorio tributario (E.T. art. 635): usura vigente - 2 puntos"
)

FUENTE_PENDIENTE_CERTIFICACION_USURA = (
    f"{PENDIENTE_CERTIFICACION_OFICIAL}: sin tasa de usura certificada por la "
    "Superfinanciera para este dia -- interes suspendido (Art. 338 C.P.)"
)


def fecha_fin_mora_certificada(fecha_corte: date) -> date:
    """Sprint 110 (respuesta del despacho, 26/08/2026: "NUNCA extrapolar"):
    ultimo dia hasta el que puede causarse interes que dependa de la tasa de
    usura -- `fecha_corte`, o el ultimo dia certificado si la tabla
    (parametros_legales, USURA_CONSUMO_ORDINARIO) no llega hasta el corte. Si
    no hay ningun tramo cargado retorna `fecha_corte` sin tocar (los motores
    lanzan el ValueError de configuracion incompleta de siempre)."""
    ultima = get_ultima_fecha_certificada_ibc_usura()
    if ultima is None or fecha_corte <= ultima:
        return fecha_corte
    return ultima


def mora_pendiente_de_certificacion(fecha_exigibilidad: date, fecha_corte: date) -> date | None:
    """Sprint 110: si parte de la mora [fecha_exigibilidad + 1 dia, fecha_corte]
    cae despues del ultimo dia con tasa de usura certificada, retorna ese
    ultimo dia certificado (para la alerta "Pendiente de Certificación
    Oficial"); None si toda la mora esta cubierta o si no hay mora."""
    inicio_mora = fecha_exigibilidad + timedelta(days=1)
    if fecha_corte < inicio_mora:
        return None
    fin_certificado = fecha_fin_mora_certificada(fecha_corte)
    if fin_certificado >= fecha_corte:
        return None
    return fin_certificado


def tasa_diaria_lineal_tributaria(tasa_anual_pct: Decimal, anio: int) -> Rate:
    """Division lineal simple (Sprint 84, respuesta del despacho 22/08/2026):
    tasa_anual / dias_del_anio, sin capitalizacion. `anio` determina si el
    divisor es 365 o 366 (calendar.isleap) -- cada tramo de usura vive
    íntegramente dentro de un solo año calendario (los tramos son mensuales,
    nunca cruzan el 31 de diciembre), así que basta un año por tramo."""
    dias_del_anio = 366 if calendar.isleap(anio) else 365
    return Rate(Rate.from_percent(tasa_anual_pct).value / Decimal(dias_del_anio))


def construir_rate_provider_moratorio_tributario(
    fecha_exigibilidad: date, fecha_corte: date
) -> MemoryRateProvider:
    """Un RatePeriod diario por cada tramo historico de usura que se solape
    con el rango de mora [fecha_exigibilidad + 1 dia, fecha_corte] (la mora
    empieza el dia siguiente a la exigibilidad, mismo criterio que
    R-CIV-003). Si fecha_corte no supera ese inicio de mora, no hay mora:
    retorna un provider vacio.

    Sprint 110 (respuesta del despacho, 26/08/2026: "NUNCA extrapolar. Opcion
    (b)"): los tramos solo cubren hasta el ultimo dia con tasa de usura
    certificada (`fecha_fin_mora_certificada`). Los dias posteriores, hasta
    fecha_corte, quedan a 0% con la fuente FUENTE_PENDIENTE_CERTIFICACION_USURA
    -- el interes de ese periodo queda suspendido, no se infiere. La alerta
    no bloqueante la agrega el llamador (TributarioStrategy) con
    `mora_pendiente_de_certificacion`."""
    provider = MemoryRateProvider()

    inicio_mora = fecha_exigibilidad + timedelta(days=1)
    if fecha_corte < inicio_mora:
        return provider

    fin_certificado = fecha_fin_mora_certificada(fecha_corte)
    if fin_certificado < fecha_corte:
        provider.add_rate_period(
            start=max(inicio_mora, fin_certificado + timedelta(days=1)),
            end=fecha_corte,
            rate=Rate(Decimal("0")),
            source=FUENTE_PENDIENTE_CERTIFICACION_USURA,
        )
        if fin_certificado < inicio_mora:
            return provider

    tramos = get_tramos_ibc_usura_between(inicio_mora, fin_certificado)
    for tramo in tramos:
        inicio_segmento = max(tramo.inicio, inicio_mora)
        fin_segmento = min(tramo.fin, fin_certificado)
        puntos_descuento = get_parametro("ET635_PUNTOS_DESCUENTO", inicio_segmento)
        tasa_anual_tributaria = tramo.usura_anual - puntos_descuento
        tasa_diaria = tasa_diaria_lineal_tributaria(tasa_anual_tributaria, inicio_segmento.year)
        provider.add_rate_period(
            start=inicio_segmento,
            end=fin_segmento,
            rate=tasa_diaria,
            source=FUENTE_MORATORIO_TRIBUTARIO,
        )
    return provider


def calcular_interes_moratorio_tributario(
    capital: Decimal, fecha_exigibilidad: date, fecha_corte: date
) -> Decimal:
    """Suma el interes moratorio tributario dia a dia (mismo patron que
    LiquidationCore._accrue_time_passage en app/engine/liquidation/engine.py)
    desde el dia siguiente a fecha_exigibilidad hasta fecha_corte. Capital
    fijo, sin abonos ni imputacion de pagos -- eso es Sprint 11b. Sprint 110:
    los dias posteriores al ultimo tramo de usura certificado no causan
    interes (ver construir_rate_provider_moratorio_tributario)."""
    if capital <= Decimal("0.00"):
        return Decimal("0.00")

    provider = construir_rate_provider_moratorio_tributario(fecha_exigibilidad, fecha_corte)

    total = Decimal("0.00")
    current_day = fecha_exigibilidad + timedelta(days=1)
    while current_day <= fecha_corte:
        daily_rate = provider.get_rate(current_day)
        total += DailyInterest.calculate(capital=capital, daily_rate=daily_rate, days=1)
        current_day += timedelta(days=1)
    return total
