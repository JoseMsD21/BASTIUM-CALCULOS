from datetime import date
from decimal import Decimal

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.indexation.smmlv import SMMLVCalculator

FECHA_CORTE_SMLMV_A_UVT = date(2020, 1, 1)


def resolver_base_sancion(fecha_hecho: date, cantidad: Decimal) -> Decimal:
    """
    Convierte una cantidad de SMLMV o UVT a pesos, segun la fecha del hecho sancionatorio
    (Ley 1955 de 2019, art. 49): antes del 2020-01-01 la base es el SMLMV del año del
    hecho; desde esa fecha, la base es la UVT vigente de la DIAN.

    La tabla historica de UVT aun no existe (ver Pendientes.md Sprint 5 -- el PDF de
    requisitos no trae una serie completa por año, solo menciones dispersas). Por eso,
    fechas posteriores al corte lanzan UVTNoDisponibleError en vez de inventar un valor.
    """
    if fecha_hecho < FECHA_CORTE_SMLMV_A_UVT:
        smlmv_del_anio = get_smlmv_for_year(fecha_hecho.year)
        return SMMLVCalculator.to_pesos(cantidad, smlmv_del_anio)

    raise UVTNoDisponibleError(
        f"No hay tabla historica de UVT cargada para calcular el hecho sancionatorio "
        f"del {fecha_hecho} (posterior a 2020-01-01). Ver Pendientes.md, Sprint 5."
    )
