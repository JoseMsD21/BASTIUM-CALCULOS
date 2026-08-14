"""
Actualizacion por mora tributaria superior a 3 anios (Estatuto Tributario,
art. 867-1). Respuesta del despacho, docs/Preguntas-Para-Abogado-Respondidas.md Sprint 15
(2026-08-01): la Corte Constitucional (Sentencia C-549 de 1993) considera que
indexacion e interes moratorio tienen naturalezas distintas (la primera
conserva poder adquisitivo, el segundo indemniza la mora) y pueden concurrir
-- siempre que la suma no supere el tope de usura y la correccion monetaria no
se cuente doble.

Regimen (mora > 3 anios desde la fecha de exigibilidad hasta fecha_corte):
- Rubro "Impuesto" (IMPUESTO_A_CARGO): conserva el interes moratorio E.T. 635
  (sin cambios) y ADEMAS se indexa por IPC -- topando la suma
  (interes + indexacion) al interes que produciria la tasa de usura PLENA
  (sin el descuento de 2 puntos del art. 635) sobre el mismo capital y
  periodo, tal como exige el despacho ("Tasa Efectiva Combinada <= Tasa de
  Usura").
- Rubros "Sancion" (SANCION_*): NO se liquida interes moratorio -- se
  reemplaza integramente por la indexacion IPC.
- Mora <= 3 anios: sin cambios para ningun rubro (solo interes E.T. 635, sin
  indexacion) -- ver ComercialStrategy/TributarioStrategy en area_strategy.py
  para el wiring real.
"""

from datetime import date, timedelta
from decimal import Decimal

from app.engine.indexation.historical_index import (
    get_ipc_interpolado_for_date,
    get_tramos_ibc_usura_between,
)
from app.engine.indexation.ipc import IPCIndexation
from app.engine.interest.daily_interest import DailyInterest
from app.engine.interest.rate_conversion import EffectiveRateConverter

UMBRAL_MORA_DIAS = 365 * 3


def aplica_actualizacion_867_1(fecha_origen: date, fecha_corte: date) -> bool:
    """True si la mora (fecha_corte - fecha_origen) supera 3 anios (1095 dias)."""
    return (fecha_corte - fecha_origen).days > UMBRAL_MORA_DIAS


def calcular_indexacion_867_1(capital: Decimal, fecha_origen: date, fecha_corte: date) -> Decimal:
    """Formula estandar de indexacion IPC (misma que Civil/Familia, Sprint 8):
    ValorActual = ValorAIndexar x (IPC_final / IPC_inicial)."""
    return IPCIndexation.calculate(
        capital=capital,
        initial_index=get_ipc_interpolado_for_date(fecha_origen),
        final_index=get_ipc_interpolado_for_date(fecha_corte),
    )


def calcular_interes_usura_plena(
    capital: Decimal, fecha_origen: date, fecha_corte: date
) -> Decimal:
    """Interes que produciria la tasa de usura PLENA (sin el descuento de 2
    puntos del E.T. art. 635) sobre `capital`, dia a dia, desde el dia
    siguiente a `fecha_origen` hasta `fecha_corte` -- mismo patron que
    calcular_interes_moratorio_tributario (moratory_interest.py), pero sin el
    descuento. Se usa unicamente como techo legal para el rubro Impuesto."""
    if capital <= Decimal("0.00"):
        return Decimal("0.00")

    inicio_mora = fecha_origen + timedelta(days=1)
    if fecha_corte < inicio_mora:
        return Decimal("0.00")

    tramos = get_tramos_ibc_usura_between(inicio_mora, fecha_corte)
    tasa_por_dia = {}
    for tramo in tramos:
        inicio_segmento = max(tramo.inicio, inicio_mora)
        fin_segmento = min(tramo.fin, fecha_corte)
        tasa_diaria = EffectiveRateConverter.annual_to_daily(tramo.usura_anual)
        dia = inicio_segmento
        while dia <= fin_segmento:
            tasa_por_dia[dia] = tasa_diaria
            dia += timedelta(days=1)

    total = Decimal("0.00")
    dia = inicio_mora
    while dia <= fecha_corte:
        total += DailyInterest.calculate(capital=capital, daily_rate=tasa_por_dia[dia], days=1)
        dia += timedelta(days=1)
    return total


def calcular_indexacion_867_1_topada(
    capital: Decimal, fecha_origen: date, fecha_corte: date, interes_ya_liquidado: Decimal
) -> Decimal:
    """Indexacion IPC del rubro Impuesto, recortada si (interes_ya_liquidado +
    indexacion) excederia el interes de usura plena para el mismo capital y
    periodo -- la "Restriccion del Sistema" que exige el despacho. Nunca
    retorna un valor negativo (si el interes ya liquidado por si solo ya
    supera el techo, la indexacion topada es cero, no una resta al interes)."""
    indexacion = calcular_indexacion_867_1(capital, fecha_origen, fecha_corte)
    tope = calcular_interes_usura_plena(capital, fecha_origen, fecha_corte)
    indexacion_maxima = max(tope - interes_ya_liquidado, Decimal("0.00"))
    return min(indexacion, indexacion_maxima)
