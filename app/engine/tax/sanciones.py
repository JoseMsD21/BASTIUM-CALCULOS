"""
Sanciones tributarias (Estatuto Tributario, PDF pag. 39): extemporaneidad,
inexactitud y error aritmetico. Las tres comparten un piso legal -- ninguna
sancion puede ser inferior a 10 UVT (aplicar_piso_sancion_minima) -- que se
aplica una sola vez, aqui, en vez de repetir la logica en cada funcion.

Ver docs/superpowers/specs/2026-07-24-sprint15-tributario-11b-design.md.
"""

from datetime import date
from decimal import Decimal

from app.engine.indexation.historical_index import get_uvt_for_year
from app.engine.math.rounding import Rounding
from app.services.parametro_service import get_parametro


def aplicar_piso_sancion_minima(monto_sancion: Decimal, fecha_referencia: date) -> Decimal:
    """Ninguna sancion tributaria puede ser inferior a 10 UVT del año de referencia."""
    piso = Decimal("10") * get_uvt_for_year(fecha_referencia.year)
    return max(monto_sancion, piso)


def calcular_sancion_extemporaneidad(
    impuesto_a_cargo: Decimal, meses_o_fraccion: int, fecha_referencia: date
) -> Decimal:
    """5% mensual (o fraccion de mes) del impuesto a cargo, tope 100% del impuesto a cargo."""
    pct_mensual = get_parametro("EXTEMPORANEIDAD_PCT_MENSUAL", fecha_referencia)
    monto = impuesto_a_cargo * pct_mensual / Decimal("100") * Decimal(meses_o_fraccion)
    monto = min(monto, impuesto_a_cargo)
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)


def calcular_sancion_inexactitud(diferencia: Decimal, agravada: bool, fecha_referencia: date) -> Decimal:
    """160% (o 200% si agravada -- omision de activos o inclusion de pasivos inexistentes) de la
    diferencia entre el saldo determinado y el declarado."""
    clave = "INEXACTITUD_AGRAVADA_PCT" if agravada else "INEXACTITUD_PCT"
    pct = get_parametro(clave, fecha_referencia)
    monto = diferencia * pct / Decimal("100")
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)


def calcular_sancion_error_aritmetico(diferencia: Decimal, fecha_referencia: date) -> Decimal:
    """30% de la diferencia generada por el error aritmetico."""
    pct = get_parametro("ERROR_ARITMETICO_PCT", fecha_referencia)
    monto = diferencia * pct / Decimal("100")
    monto = aplicar_piso_sancion_minima(monto, fecha_referencia)
    return Rounding.money(monto)
