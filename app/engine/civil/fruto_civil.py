"""Beneficio dejado de percibir como fruto civil (Sprint 100).

Regla del despacho (respuesta al "Sprint 97 (seguimiento)", ver
docs/Preguntas-Para-Abogado-Respondidas.md):

    "El fruto civil se calcula sobre el rendimiento financiero u operativo
    real del activo (ej. canon de arrendamiento de mercado), indexado mes a
    mes por IPC, deduciendo solo gastos ordinarios de conservacion
    (Art. 964 C.C.)."

y expresamente: NO usa la mecanica de cuota recurrente pensional
(IBL x tasa de reemplazo, ni la tasa 0,0048676 de las formulas actuariales
del Sprint 97). Por eso este modulo NO reutiliza `generar_cuotas_mensuales`,
`app/engine/labor/ibl.py` ni `lucro_cesante_actuarial.py`, y NO aplica el
"Incremento Anual" de la plantilla X6 (era parte de esa mecanica pensional).

Funcion AISLADA del area Civil -- sin cablear a ningun `AreaStrategy`, modelo
de datos ni UI todavia.

Convenciones (decisiones de implementacion, documentadas en
docs/specifications/08_motor_civil_fruto_civil.md):

1. Indexacion mes a mes: canon del mes m =
   `canon_mensual x IPC(m) / IPC(fecha_referencia)`, donde IPC(m) es el
   indice mensual DANE del mes m (equivale al interpolado al ultimo dia del
   mes) e IPC(fecha_referencia) es el interpolado por dias dentro del mes
   (`get_ipc_interpolado_mensual_for_date`, misma funcion que usa
   `CivilFamiliaStrategy._evento_indexacion` desde el Sprint 80). Es la razon
   pura de indices: si la fecha de referencia es POSTERIOR a un mes del
   periodo (p. ej. canon de mercado certificado hoy para una privacion
   pasada), el canon de ese mes queda por debajo del canon de referencia --
   se lleva el canon al nivel de precios de cada mes, no se aplica el piso de
   deflacion de `IPCIndexation.calculate` (que protege un capital en mora,
   caso distinto).
2. Fallback de serie: si alguna fecha (referencia o algun mes del periodo) es
   anterior a ene-2003 (primer mes de `_IPC_MENSUAL`), TODAS las fechas pasan
   a la interpolacion anual (`get_ipc_interpolado_for_date`) -- nunca se
   mezclan series de bases distintas (mismo criterio del Sprint 80).
3. Periodo de privacion: `fecha_inicial` y `fecha_final` ambas inclusive. El
   primer y el ultimo mes, si no estan completos, se prorratean por dias
   calendario: `dias_privados_en_el_mes / dias_del_mes_calendario`.
4. Gastos ordinarios de conservacion: (a) un gasto mensual fijo, prorrateado
   con la misma fraccion que el canon; y/o (b) gastos puntuales por fecha,
   descontados completos en el mes en que ocurren (deben caer dentro del
   periodo). Se descuentan por su valor nominal (la respuesta no pide
   indexarlos).
5. Redondeo: canon indexado del mes completo a centavos; canon del periodo,
   gasto mensual prorrateado y neto a centavos; los totales suman los valores
   redondeados de cada mes (lo que ve el usuario en el detalle cuadra con el
   total). El neto de un mes puede ser negativo si los gastos superan el
   canon: se muestra tal cual, sin pisos.

Fuera de alcance (no confirmado por el despacho): intereses sobre los frutos,
distincion poseedor de buena/mala fe del Art. 964 (frutos desde la
contestacion de la demanda vs. desde la posesion, frutos que el dueno
"hubiera podido percibir") -- el usuario fija el periodo de privacion a mano.
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal

from app.core.exceptions import IPCMensualNoDisponibleError
from app.engine.indexation.historical_index import (
    get_ipc_interpolado_for_date,
    get_ipc_interpolado_mensual_for_date,
)
from app.engine.math.rounding import Rounding

SERIE_MENSUAL = "MENSUAL"
SERIE_ANUAL = "ANUAL"


@dataclass(frozen=True)
class GastoConservacion:
    """Gasto ordinario de conservacion puntual (Art. 964 C.C.), descontado
    completo en el mes de `fecha`."""

    fecha: date
    monto: Decimal
    concepto: str = ""


@dataclass(frozen=True)
class FrutoCivilMes:
    anio: int
    mes: int
    desde: date
    hasta: date
    dias: int
    dias_mes: int
    ipc_mes: Decimal
    canon_indexado_mes: Decimal
    canon_periodo: Decimal
    gastos_conservacion: Decimal
    fruto_neto: Decimal


@dataclass(frozen=True)
class ResultadoFrutoCivil:
    canon_mensual: Decimal
    fecha_referencia: date
    ipc_referencia: Decimal
    serie_ipc: str
    meses: list[FrutoCivilMes] = field(default_factory=list)
    total_canon: Decimal = Decimal("0.00")
    total_gastos_conservacion: Decimal = Decimal("0.00")
    total_fruto_civil: Decimal = Decimal("0.00")


def _tramos_mensuales(fecha_inicial: date, fecha_final: date) -> list[tuple[date, date, int]]:
    """Parte [fecha_inicial, fecha_final] (inclusive) en tramos por mes
    calendario: (desde, hasta, dias_del_mes)."""
    tramos = []
    anio, mes = fecha_inicial.year, fecha_inicial.month
    while (anio, mes) <= (fecha_final.year, fecha_final.month):
        dias_mes = calendar.monthrange(anio, mes)[1]
        desde = max(fecha_inicial, date(anio, mes, 1))
        hasta = min(fecha_final, date(anio, mes, dias_mes))
        tramos.append((desde, hasta, dias_mes))
        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return tramos


def _indices_ipc(
    fecha_referencia: date, cierres_mes: list[date]
) -> tuple[Decimal, list[Decimal], str]:
    try:
        ipc_ref = get_ipc_interpolado_mensual_for_date(fecha_referencia)
        ipc_meses = [get_ipc_interpolado_mensual_for_date(f) for f in cierres_mes]
        return ipc_ref, ipc_meses, SERIE_MENSUAL
    except IPCMensualNoDisponibleError:
        ipc_ref = get_ipc_interpolado_for_date(fecha_referencia)
        ipc_meses = [get_ipc_interpolado_for_date(f) for f in cierres_mes]
        return ipc_ref, ipc_meses, SERIE_ANUAL


def calcular_fruto_civil(
    canon_mensual: Decimal,
    fecha_referencia: date,
    fecha_inicial: date,
    fecha_final: date,
    gasto_conservacion_mensual: Decimal = Decimal("0"),
    gastos_conservacion: list[GastoConservacion] | None = None,
) -> ResultadoFrutoCivil:
    """Liquida mes a mes el fruto civil dejado de percibir durante la
    privacion [fecha_inicial, fecha_final] (ambas inclusive).

    `canon_mensual` es el rendimiento real mensual del activo (p. ej. canon
    de arrendamiento de mercado) expresado a precios de `fecha_referencia`.
    Ver el docstring del modulo para las convenciones de indexacion,
    prorrateo, gastos y redondeo."""
    canon_mensual = Decimal(str(canon_mensual))
    gasto_conservacion_mensual = Decimal(str(gasto_conservacion_mensual))
    gastos_conservacion = list(gastos_conservacion or [])

    if canon_mensual < 0:
        raise ValueError("El canon mensual del activo no puede ser negativo.")
    if fecha_final < fecha_inicial:
        raise ValueError("La fecha final de la privacion no puede ser anterior a la inicial.")
    if gasto_conservacion_mensual < 0:
        raise ValueError("El gasto mensual de conservacion no puede ser negativo.")
    for gasto in gastos_conservacion:
        if Decimal(str(gasto.monto)) < 0:
            raise ValueError("Un gasto de conservacion no puede ser negativo.")
        if not fecha_inicial <= gasto.fecha <= fecha_final:
            raise ValueError(
                f"El gasto de conservacion del {gasto.fecha.isoformat()} esta fuera del "
                "periodo de privacion."
            )

    tramos = _tramos_mensuales(fecha_inicial, fecha_final)
    cierres_mes = [date(desde.year, desde.month, dias_mes) for desde, _, dias_mes in tramos]
    ipc_ref, ipc_meses, serie = _indices_ipc(fecha_referencia, cierres_mes)

    meses: list[FrutoCivilMes] = []
    for (desde, hasta, dias_mes), ipc_mes in zip(tramos, ipc_meses, strict=True):
        dias = (hasta - desde).days + 1
        fraccion = Decimal(dias) / Decimal(dias_mes)

        canon_indexado_mes = Rounding.money(canon_mensual * ipc_mes / ipc_ref)
        # Mes completo -> fraccion 1 -> el canon del periodo es el del mes entero.
        canon_periodo = Rounding.money(canon_indexado_mes * fraccion)
        gasto_mensual = Rounding.money(gasto_conservacion_mensual * fraccion)
        gastos_puntuales = sum(
            (
                Decimal(str(g.monto))
                for g in gastos_conservacion
                if (g.fecha.year, g.fecha.month) == (desde.year, desde.month)
            ),
            Decimal("0"),
        )
        gastos_mes = Rounding.money(gasto_mensual + gastos_puntuales)

        meses.append(
            FrutoCivilMes(
                anio=desde.year,
                mes=desde.month,
                desde=desde,
                hasta=hasta,
                dias=dias,
                dias_mes=dias_mes,
                ipc_mes=ipc_mes,
                canon_indexado_mes=canon_indexado_mes,
                canon_periodo=canon_periodo,
                gastos_conservacion=gastos_mes,
                fruto_neto=canon_periodo - gastos_mes,
            )
        )

    total_canon = sum((m.canon_periodo for m in meses), Decimal("0.00"))
    total_gastos = sum((m.gastos_conservacion for m in meses), Decimal("0.00"))
    return ResultadoFrutoCivil(
        canon_mensual=canon_mensual,
        fecha_referencia=fecha_referencia,
        ipc_referencia=ipc_ref,
        serie_ipc=serie,
        meses=meses,
        total_canon=total_canon,
        total_gastos_conservacion=total_gastos,
        total_fruto_civil=total_canon - total_gastos,
    )
