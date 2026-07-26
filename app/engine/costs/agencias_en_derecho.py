"""Tarifas de agencias en derecho (costas judiciales), Acuerdo PSAA16-10554 del
5 de agosto de 2016, Consejo Superior de la Judicatura -- texto oficial
completo verificado durante el Sprint 18 (ver design spec, "Fuentes externas").
La cita "PCSJA20-11556" del PDF de requisitos de BASTIUM no corresponde a
ningun acuerdo real localizable; este es el acuerdo vigente que sí regula la
materia.

Los umbrales de cuantia (minima/menor/mayor) no vienen de este acuerdo sino
del articulo 25 de la Ley 1564 de 2012 (Codigo General del Proceso), tambien
verificado en 2 fuentes independientes durante este sprint."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from enum import Enum

from app.core.exceptions import TarifaNoDisponibleError
from app.engine.indexation.historical_index import get_smlmv_for_year
from app.engine.math.rounding import Rounding


class TipoProceso(str, Enum):
    DECLARATIVO_GENERAL = "declarativo_general"
    EXPROPIACION = "expropiacion"
    DESLINDE_AMOJONAMIENTO = "deslinde_amojonamiento"
    DIVISORIO = "divisorio"
    MONITORIO = "monitorio"
    EJECUTIVO = "ejecutivo"
    SUCESION = "sucesion"
    LIQUIDACION_SOCIEDAD_CONYUGAL = "liquidacion_sociedad_conyugal"
    LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES = "liquidacion_sociedad_conyugal_excepciones"
    LIQUIDACION_SOCIEDADES = "liquidacion_sociedades"
    INSOLVENCIA_PERSONA_NATURAL = "insolvencia_persona_natural"
    INSOLVENCIA_PERSONA_NATURAL_LIQUIDACION_PATRIMONIAL = (
        "insolvencia_persona_natural_liquidacion_patrimonial"
    )
    OTROS_LIQUIDACION = "otros_liquidacion"
    JURISDICCION_VOLUNTARIA = "jurisdiccion_voluntaria"
    RECURSO_CONTRA_AUTOS = "recurso_contra_autos"
    INCIDENTE = "incidente"
    RECURSO_EXTRAORDINARIO = "recurso_extraordinario"
    EXEQUATUR = "exequatur"


class Instancia(str, Enum):
    UNICA = "unica"
    PRIMERA = "primera"
    SEGUNDA = "segunda"


class CuantiaTier(str, Enum):
    MINIMA = "minima"
    MENOR = "menor"
    MAYOR = "mayor"


class UnidadTarifa(str, Enum):
    PORCENTAJE = "porcentaje"
    SMLMV = "smlmv"


@dataclass(frozen=True)
class RangoTarifa:
    minimo: Decimal
    maximo: Decimal
    unidad: UnidadTarifa


UMBRAL_MINIMA_CUANTIA_SMLMV = Decimal("40")   # CGP art. 25: pretensiones <= 40 SMLMV
UMBRAL_MENOR_CUANTIA_SMLMV = Decimal("150")   # CGP art. 25: 40 < pretensiones <= 150 SMLMV
                                                # (mayor cuantia: > 150 SMLMV, sin techo)
TOPE_MAXIMO_SMLMV = Decimal("20")             # Acuerdo PSAA16-10554, Paragrafo 3 art. 3


def resolver_cuantia_tier(pretensiones_reconocidas: Decimal, smlmv_vigente: Decimal) -> CuantiaTier:
    """CGP art. 25: minima <= 40 SMLMV, menor entre 40 y 150 SMLMV, mayor > 150 SMLMV."""
    if pretensiones_reconocidas <= UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente:
        return CuantiaTier.MINIMA
    if pretensiones_reconocidas <= UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente:
        return CuantiaTier.MENOR
    return CuantiaTier.MAYOR


# Clave: (TipoProceso, Instancia, CuantiaTier | None, tiene_pretension_pecuniaria)
# CuantiaTier es None cuando la categoria no distingue por cuantia dentro de esa
# instancia (segunda instancia, recursos, incidentes, y varias categorias de
# liquidacion que el acuerdo tarifa con un solo rango sin importar el monto).
TARIFAS_AGENCIAS_EN_DERECHO: dict[
    tuple[TipoProceso, Instancia, CuantiaTier | None, bool], RangoTarifa
] = {
    # 1. PROCESOS DECLARATIVOS EN GENERAL (art. 5.1)
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.UNICA, None, False):
        RangoTarifa(Decimal("1"), Decimal("8"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.PRIMERA, None, False):
        RangoTarifa(Decimal("1"), Decimal("10"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.DECLARATIVO_GENERAL, Instancia.SEGUNDA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
}
