from datetime import date
from decimal import Decimal

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year, get_uvt_for_year
from app.engine.indexation.smmlv import SMMLVCalculator

FECHA_CORTE_SMLMV_A_UVT = date(2020, 1, 1)


def resolver_base_sancion(fecha_hecho: date, cantidad: Decimal) -> Decimal:
    """
    Convierte una cantidad de SMLMV o UVT a pesos, segun la fecha del hecho sancionatorio
    (Ley 1955 de 2019, art. 49): antes del 2020-01-01 la base es el SMLMV del año del
    hecho; desde esa fecha, la base es la UVT vigente de la DIAN (tabla historica
    2006-2026, ver docs/superpowers/specs/2026-07-21-tabla-historica-uvt-design.md).
    """
    if fecha_hecho < FECHA_CORTE_SMLMV_A_UVT:
        smlmv_del_anio = get_smlmv_for_year(fecha_hecho.year)
        return SMMLVCalculator.to_pesos(cantidad, smlmv_del_anio)

    try:
        uvt_del_anio = get_uvt_for_year(fecha_hecho.year)
    except ValueError as error:
        raise UVTNoDisponibleError(
            f"No hay UVT publicada por la DIAN para calcular el hecho sancionatorio "
            f"del {fecha_hecho}. {error}"
        ) from error

    # SMMLVCalculator.to_pesos es un conversor generico "cantidad x valor de unidad,
    # redondeado a moneda" pese a su nombre -- no tiene logica especifica de SMLMV,
    # asi que se reutiliza tal cual para UVT en vez de crear una clase paralela.
    return SMMLVCalculator.to_pesos(cantidad, uvt_del_anio)
