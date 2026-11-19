"""Motor de vigencia del regimen pensional por fecha de causacion (Sprint 70/91).

Selecciona la formula de tasa de reemplazo de vejez segun la fecha del hecho
generador (no la fecha actual del sistema), con las fechas exactas de entrada
en vigencia confirmadas por el despacho el 16/11/2026
(docs/Preguntas-Para-Abogado-Abiertas.md, "Sprint 70/91 (seguimiento)"):

- Ley 33 de 1985: 13/02/1985.
- Ley 71 de 1988: 28/01/1989.
- Acuerdo 049 de 1990 (Dec. 758/1990): 18/04/1990.
- Ley 100 de 1993: 01/04/1994 (sector privado/nacional).
- Ley 797 de 2003: 29/01/2003.

Cada regimen rige desde su fecha hasta el dia anterior a la fecha del
siguiente (orden cronologico, el mismo con el que el despacho dio las
formulas el 22/08/2026).

Limites deliberados (no se adivinaron):
- Ley 100 de 1993, orden territorial: el despacho indico que entro a regir
  "hasta el 30 de junio de 1995". BASTIUM no tiene hoy ningun dato del caso
  que distinga orden nacional de territorial, asi que el router usa siempre
  la fecha nacional (01/04/1994).
- Regimen de transicion (Art. 36 Ley 100/1993): segun el despacho NO es un
  regimen aparte, solo preserva edad, semanas y tasa de reemplazo del
  regimen anterior. Este router no lo modela: elige el regimen por la fecha
  de causacion que se le pase.
- Ley 2381 de 2024: sin fecha ni formula confirmadas; no esta en la tabla.
- Causaciones anteriores al 13/02/1985: sin regimen confirmado -> ValueError.
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from app.engine.labor.ibl import (
    calcular_tasa_reemplazo,
    calcular_tasa_reemplazo_iss_pre_ley_100,
    calcular_tasa_reemplazo_ley_100_original,
    calcular_tasa_reemplazo_regimen_1985_1989,
)


class RegimenPensional(Enum):
    LEY_33_1985_LEY_71_1988 = "ley_33_1985_ley_71_1988"
    ISS_ACUERDO_049_1990 = "iss_acuerdo_049_1990"
    LEY_100_1993_ORIGINAL = "ley_100_1993_original"
    LEY_797_2003 = "ley_797_2003"


@dataclass(frozen=True)
class VigenciaRegimen:
    fecha_desde: date
    regimen: RegimenPensional
    norma: str


# Ordenada por fecha_desde ascendente. La Ley 71 de 1988 comparte formula
# (tasa fija 75%) con la Ley 33 de 1985, pero se lista aparte para que el
# resultado cite la norma vigente en la fecha consultada.
VIGENCIAS_REGIMEN_PENSIONAL: tuple[VigenciaRegimen, ...] = (
    VigenciaRegimen(date(1985, 2, 13), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 33 de 1985"),
    VigenciaRegimen(date(1989, 1, 28), RegimenPensional.LEY_33_1985_LEY_71_1988, "Ley 71 de 1988"),
    VigenciaRegimen(
        date(1990, 4, 18), RegimenPensional.ISS_ACUERDO_049_1990, "Acuerdo 049 de 1990"
    ),
    VigenciaRegimen(date(1994, 4, 1), RegimenPensional.LEY_100_1993_ORIGINAL, "Ley 100 de 1993"),
    VigenciaRegimen(date(2003, 1, 29), RegimenPensional.LEY_797_2003, "Ley 797 de 2003"),
)


def regimen_por_fecha(fecha_causacion: date) -> VigenciaRegimen:
    """Regimen pensional vigente en `fecha_causacion` (la ultima norma cuya
    fecha de entrada en vigencia es <= a esa fecha)."""
    vigente: VigenciaRegimen | None = None
    for vigencia in VIGENCIAS_REGIMEN_PENSIONAL:
        if vigencia.fecha_desde <= fecha_causacion:
            vigente = vigencia
        else:
            break
    if vigente is None:
        primera = VIGENCIAS_REGIMEN_PENSIONAL[0]
        raise ValueError(
            f"No hay regimen pensional confirmado para causaciones anteriores al "
            f"{primera.fecha_desde.isoformat()} ({primera.norma})."
        )
    return vigente


def calcular_tasa_reemplazo_por_fecha(
    fecha_causacion: date,
    semanas_cotizadas: int,
    ibl: Decimal | None = None,
    smlmv_vigente: Decimal | None = None,
) -> Decimal:
    """Tasa de reemplazo de vejez (en %) con la formula del regimen vigente en
    `fecha_causacion`. `ibl` y `smlmv_vigente` solo son obligatorios para la
    Ley 797 de 2003 (su formula depende de s = IBL / SMLMV)."""
    regimen = regimen_por_fecha(fecha_causacion).regimen
    if regimen is RegimenPensional.LEY_33_1985_LEY_71_1988:
        return calcular_tasa_reemplazo_regimen_1985_1989()
    if regimen is RegimenPensional.ISS_ACUERDO_049_1990:
        return calcular_tasa_reemplazo_iss_pre_ley_100(semanas_cotizadas)
    if regimen is RegimenPensional.LEY_100_1993_ORIGINAL:
        return calcular_tasa_reemplazo_ley_100_original(semanas_cotizadas)
    if ibl is None or smlmv_vigente is None:
        raise ValueError("La formula de la Ley 797 de 2003 requiere el IBL y el SMLMV vigente.")
    return calcular_tasa_reemplazo(
        ibl=ibl,
        smlmv_vigente=smlmv_vigente,
        semanas_cotizadas=semanas_cotizadas,
        anio_causacion=fecha_causacion.year,
    )
