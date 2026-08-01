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

from app.core.exceptions import CostasFueraDeRangoError, TarifaNoDisponibleError
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


# Rango simple de validacion para el porcentaje MANUAL de costas (costas_pct_manual),
# respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 18, 2026-08-01) -- distinto
# (mas simple, y con numeros propios) de la tabla granular por tipo de proceso de
# TARIFAS_AGENCIAS_EN_DERECHO arriba. Se usa solo para RECHAZAR un porcentaje manual
# fuera de rango, nunca para calcular un monto automatico -- si de verdad reemplaza (en
# vez de complementar) la tabla granular es una pregunta de seguimiento abierta en
# Preguntas-Para-Abogado.md, sin asumir.
RANGO_COSTAS_MANUAL_POR_TIER: dict[CuantiaTier, RangoTarifa] = {
    CuantiaTier.MINIMA: RangoTarifa(Decimal("0"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    CuantiaTier.MENOR: RangoTarifa(Decimal("3"), Decimal("7"), UnidadTarifa.PORCENTAJE),
    CuantiaTier.MAYOR: RangoTarifa(Decimal("1"), Decimal("5"), UnidadTarifa.PORCENTAJE),
}


def validar_costas_pct_manual(
    costas_pct_manual: Decimal, pretensiones_reconocidas: Decimal, fecha: date
) -> None:
    """Rechaza (no trunca) un porcentaje manual de costas fuera del rango permitido
    para la cuantia del proceso -- respuesta del despacho, Sprint 18: "si el proceso
    es de Mayor Cuantía, el usuario no podrá ingresar un 8% de agencias en derecho
    (el sistema debe lanzar un error de validación)"."""
    smlmv_vigente = get_smlmv_for_year(fecha.year)
    tier = resolver_cuantia_tier(pretensiones_reconocidas, smlmv_vigente)
    rango = RANGO_COSTAS_MANUAL_POR_TIER[tier]
    if not (rango.minimo <= costas_pct_manual <= rango.maximo):
        raise CostasFueraDeRangoError(
            f"El porcentaje de costas manual ({costas_pct_manual}%) está fuera del rango "
            f"permitido para {tier.value} cuantía ({rango.minimo}%-{rango.maximo}%, CGP art. 25)."
        )


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

    # 2.1. PROCESOS DE EXPROPIACION (art. 5.2.1)
    (TipoProceso.EXPROPIACION, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EXPROPIACION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 2.2. PROCESOS DE DESLINDE Y AMOJONAMIENTO (art. 5.2.2)
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DESLINDE_AMOJONAMIENTO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 2.3. PROCESOS DIVISORIOS (art. 5.2.3)
    (TipoProceso.DIVISORIO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.DIVISORIO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 3. PROCESO MONITORIO (art. 5.3): "hasta el 5%" -- sin piso explicito en
    # el texto, se modela con piso 0 (lectura razonable de "hasta").
    (TipoProceso.MONITORIO, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0"), Decimal("5"), UnidadTarifa.PORCENTAJE),

    # 4. PROCESOS EJECUTIVOS (art. 5.4). El acuerdo agrupa "unica y primera
    # instancia" bajo el mismo encabezado con 3 tiers explicitos; los dos
    # resultados posibles (sentencia sigue adelante / excepciones favorables)
    # dan el mismo porcentaje por tier, se registra una sola vez por tier.
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.EJECUTIVO, Instancia.UNICA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.PRIMERA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.EJECUTIVO, Instancia.SEGUNDA, None, False):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.1. PROCESOS DE SUCESION (art. 5.5.1). Objeciones a inventarios/avaluos
    # y objeciones a la particion tienen identico rango por tier -- se
    # registran una sola vez.
    (TipoProceso.SUCESION, Instancia.UNICA, CuantiaTier.MINIMA, True):
        RangoTarifa(Decimal("5"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MENOR, True):
        RangoTarifa(Decimal("4"), Decimal("10"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.PRIMERA, CuantiaTier.MAYOR, True):
        RangoTarifa(Decimal("3"), Decimal("7.5"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.SUCESION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.2. LIQUIDACION DE SOCIEDADES CONYUGALES O PATRIMONIALES (art. 5.5.2).
    # "Objeciones a inventarios/avaluos" y "objeciones a la particion" (ambas
    # 3%-15%) se registran juntas como LIQUIDACION_SOCIEDAD_CONYUGAL; "cuando
    # prosperan o fracasan las excepciones" (1-6 SMLMV, un resultado distinto
    # del mismo epigrafe del acuerdo) es LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES.
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.LIQUIDACION_SOCIEDAD_CONYUGAL_EXCEPCIONES, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.3. LIQUIDACION DE SOCIEDADES (art. 5.5.3). Objeciones al inventario y
    # objeciones a la propuesta de distribucion, ambas 3%-15% -- se registran juntas.
    (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.LIQUIDACION_SOCIEDADES, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 5.4. INSOLVENCIA DE PERSONA NATURAL NO COMERCIANTE (art. 5.5.4). El
    # acuerdo no indica instancia para esta categoria -- se usa Instancia.UNICA
    # por convencion de modelado (el valor y el texto legal son exactos, solo
    # la etiqueta de instancia es una convencion, ver design spec).
    (TipoProceso.INSOLVENCIA_PERSONA_NATURAL, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.INSOLVENCIA_PERSONA_NATURAL_LIQUIDACION_PATRIMONIAL, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),

    # 5.5. OTROS PROCESOS DE LIQUIDACION (art. 5.5.5).
    (TipoProceso.OTROS_LIQUIDACION, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("3"), Decimal("15"), UnidadTarifa.PORCENTAJE),
    (TipoProceso.OTROS_LIQUIDACION, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 6. JURISDICCION VOLUNTARIA Y ASIMILABLES (art. 5.6, cuando hay oposicion).
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.PRIMERA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("6"), UnidadTarifa.SMLMV),
    (TipoProceso.JURISDICCION_VOLUNTARIA, Instancia.SEGUNDA, None, True):
        RangoTarifa(Decimal("1"), Decimal("6"), UnidadTarifa.SMLMV),

    # 7. RECURSOS CONTRA AUTOS (art. 5.7). Instancia no distinguida en el texto.
    (TipoProceso.RECURSO_CONTRA_AUTOS, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV),

    # 8. INCIDENTES Y ASUNTOS ASIMILABLES (art. 5.8). Instancia no distinguida.
    (TipoProceso.INCIDENTE, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("0.5"), Decimal("4"), UnidadTarifa.SMLMV),

    # 9. RECURSOS EXTRAORDINARIOS (art. 5.9). Instancia no distinguida.
    (TipoProceso.RECURSO_EXTRAORDINARIO, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV),

    # 10. EXEQUATUR (art. 5.10). Instancia no distinguida.
    (TipoProceso.EXEQUATUR, Instancia.UNICA, None, True):
        RangoTarifa(Decimal("1"), Decimal("20"), UnidadTarifa.SMLMV),
}


def _interpolar_dentro_de_rango(
    minimo: Decimal, maximo: Decimal, valor: Decimal, floor: Decimal, ceiling: Decimal | None
) -> Decimal:
    """Paragrafo 3, articulo 3, Acuerdo PSAA16-10554: 'a mayor valor menor
    porcentaje, a menor valor mayor porcentaje'. Interpolacion lineal entre
    los limites del tier de cuantia -- el acuerdo exige el principio pero no
    da la formula matematica exacta (aproximacion documentada, ver design
    spec). Si el tier no tiene techo (mayor cuantia), no hay base para
    interpolar: se devuelve el minimo del rango."""
    if ceiling is None:
        return minimo
    posicion = (valor - floor) / (ceiling - floor)
    posicion = max(Decimal("0"), min(Decimal("1"), posicion))
    return maximo - posicion * (maximo - minimo)


def _limites_pesos_tier(tier: CuantiaTier, smlmv_vigente: Decimal) -> tuple[Decimal, Decimal | None]:
    if tier == CuantiaTier.MINIMA:
        return Decimal("0"), UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente
    if tier == CuantiaTier.MENOR:
        return UMBRAL_MINIMA_CUANTIA_SMLMV * smlmv_vigente, UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente
    return UMBRAL_MENOR_CUANTIA_SMLMV * smlmv_vigente, None  # MAYOR: sin techo


def calcular_agencias_en_derecho(
    tipo_proceso: TipoProceso,
    instancia: Instancia,
    pretensiones_reconocidas: Decimal,
    fecha_radicacion: date,
    tiene_pretension_pecuniaria: bool = True,
) -> Decimal:
    """Calcula agencias en derecho segun el Acuerdo PSAA16-10554. Busca primero
    la tarifa especifica del tier de cuantia resuelto; si la categoria no
    distingue por cuantia (la mayoria de segundas instancias, recursos,
    incidentes, y varias categorias de liquidacion), cae al registro sin tier.
    Lanza TarifaNoDisponibleError si ninguna de las dos claves esta registrada
    -- nunca inventa un rango."""
    if pretensiones_reconocidas is None or pretensiones_reconocidas <= Decimal("0.00"):
        raise ValueError("pretensiones_reconocidas debe ser mayor que cero.")

    smlmv_vigente = get_smlmv_for_year(fecha_radicacion.year)
    tier = resolver_cuantia_tier(pretensiones_reconocidas, smlmv_vigente) if tiene_pretension_pecuniaria else None

    rango = TARIFAS_AGENCIAS_EN_DERECHO.get((tipo_proceso, instancia, tier, tiene_pretension_pecuniaria))
    tier_aplicable = tier
    if rango is None and tier is not None:
        rango = TARIFAS_AGENCIAS_EN_DERECHO.get((tipo_proceso, instancia, None, tiene_pretension_pecuniaria))
        tier_aplicable = None  # la tarifa encontrada no distingue por cuantia
    if rango is None:
        raise TarifaNoDisponibleError(
            f"No hay tarifa de agencias en derecho (Acuerdo PSAA16-10554) registrada para "
            f"{tipo_proceso.value}/{instancia.value} (pecuniaria={tiene_pretension_pecuniaria})."
        )

    if rango.unidad == UnidadTarifa.PORCENTAJE and tier_aplicable is not None:
        floor, ceiling = _limites_pesos_tier(tier_aplicable, smlmv_vigente)
        porcentaje = _interpolar_dentro_de_rango(rango.minimo, rango.maximo, pretensiones_reconocidas, floor, ceiling)
        monto = pretensiones_reconocidas * porcentaje / Decimal("100")
    elif rango.unidad == UnidadTarifa.PORCENTAJE:
        porcentaje = (rango.minimo + rango.maximo) / Decimal("2")
        monto = pretensiones_reconocidas * porcentaje / Decimal("100")
    else:  # SMLMV, sin tier de cuantia aplicable -> punto medio del rango
        cantidad_smlmv = (rango.minimo + rango.maximo) / Decimal("2")
        monto = cantidad_smlmv * smlmv_vigente

    tope = TOPE_MAXIMO_SMLMV * smlmv_vigente
    return Rounding.money(min(monto, tope))
