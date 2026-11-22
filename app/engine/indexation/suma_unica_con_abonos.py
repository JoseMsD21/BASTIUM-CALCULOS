"""Liquidacion tramo por tramo de una obligacion con indexacion IPC y abonos
parciales (Sprint 104, respuesta del despacho 22/08/2026, registrada bajo la
pregunta ampliada del Sprint 102): "la indexacion global restando abonos al
final es un error matematico y juridico que genera enriquecimiento sin causa
... debe liquidarse tramo por tramo", con imputacion legal del Art. 1653
C.C. (cada abono paga primero los intereses adeudados del tramo, el
remanente reduce capital).

Algoritmo (traduccion literal del pseudocodigo Python que aporto el
despacho, adaptado a Decimal y a las utilidades ya existentes del motor):
por cada abono, en orden ascendente de fecha: (1) indexa el capital vigente
desde el corte anterior hasta la fecha del abono (coeficiente IPC_abono/
IPC_anterior); (2) calcula el interes compuesto generado en ese tramo sobre
el capital ya indexado; (3) imputa el abono primero a los intereses
adeudados (los del tramo mas los pendientes de tramos previos que el abono
anterior no alcanzo a cubrir), y el remanente (si lo hay) a capital. Al
final, un tramo adicional desde el ultimo abono (o el origen, si no hubo
abonos) hasta `fecha_liquidacion_final`.

Dos sustituciones documentadas frente al pseudocodigo del despacho (que
referenciaba una funcion `calcular_dias_comerciales_reales` sin definirla):
- Conteo de dias por tramo (`dias_comerciales_tramo`): convencion 30/360
  ("mes de 30 dias, año de 360", el propio comentario del despacho) como
  DIFERENCIA entre las dos fechas -- `CalendarUtils.dias_comerciales_360`
  menos su +1 inclusivo. Ese +1 solo fue confirmado para prestaciones
  sociales en Laboral (Sprint 78); en una cadena de tramos contaria dos veces
  cada fecha pivote (el dia del abono cerraria un tramo y abriria el
  siguiente), y con la diferencia pura la suma de los tramos es igual al
  tramo unico origen->corte. Ejemplo: 2024-07-01 -> 2025-01-01 = 180 dias = 6
  meses comerciales. (Sprint 104, 2026-11-19: hasta esta fecha la funcion
  llamaba `dias_comerciales_360` con el +1 pese a que este docstring ya decia
  "sin el +1" -- corregido al cablearla a produccion.)
- Indice IPC: se recibe como funcion `indice_ipc_fn(fecha)` (default
  `get_ipc_interpolado_for_date`, Sprint 8) en vez de la serie del
  pseudocodigo.

Cableado a produccion (Sprint 104, 2026-11-19): `CivilFamiliaStrategy` ya no
usa esta funcion directamente, sino sus piezas (`dias_comerciales_tramo`,
`interes_compuesto_tramo` y `CausacionTramoATramo`), que `LiquidationCore`
aplica en cada abono para producir la cronologia auditable fila por fila
(con costas procesales, Sprint 79, pagadas primero y sin interes). Esta
funcion sigue como referencia literal del algoritmo del despacho (sin costas,
redondeo solo al final). Tasa: `TASA_INTERES_MENSUAL_PURA` (0,0048676),
confirmada por el despacho para "algoritmos de suma unica con abonos" (ver
docs/Preguntas-Para-Abogado-Respondidas.md, "Sprint 104 (seguimiento)").
"""

from collections.abc import Callable
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, localcontext

from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils
from config.decimal_config import CONTEXTO_FORENSE

DIAS_MES_COMERCIAL = Decimal("30")

# Respuesta del despacho (Sprint 104 seguimiento, 16/11/2026): "la
# tasa_interes_mensual_pura del algoritmo tramo a tramo es exactamente la misma
# pieza (0.0048676) ... la tasa pura mensual (0.0048676) para cuantificacion de
# perjuicios y algoritmos de suma unica con abonos". Equivale a (1,06)^(1/12) - 1
# (6 % EA, Art. 1617/2232 C.C.) redondeada a 7 decimales; se usa el literal.
TASA_INTERES_MENSUAL_PURA = Decimal("0.0048676")


def dias_comerciales_tramo(fecha_inicio: date, fecha_fin: date) -> int:
    """Dias 30/360 transcurridos entre dos fechas (diferencia, sin +1 inclusivo):
    dia 31 se topa a 30, febrero cuenta sus dias reales -- misma regla de
    `CalendarUtils.dias_comerciales_360`, de la que se reutiliza el calculo."""
    return CalendarUtils.dias_comerciales_360(fecha_inicio, fecha_fin) - 1


def meses_comerciales_tramo(fecha_inicio: date, fecha_fin: date) -> Decimal:
    return Decimal(dias_comerciales_tramo(fecha_inicio, fecha_fin)) / DIAS_MES_COMERCIAL


def interes_compuesto_tramo(
    capital: Decimal, tasa_interes_mensual: Decimal, n_meses: Decimal
) -> Decimal:
    """`capital x ((1 + tasa)^meses - 1)`, sin redondear (formula del despacho)."""
    return capital * ((Decimal("1") + tasa_interes_mensual) ** n_meses - Decimal("1"))


@dataclass(frozen=True)
class CausacionTramoATramo:
    """Configuracion que activa en `LiquidationCore` la causacion tramo a tramo
    del despacho (Sprint 104): en cada evento (abono) y al corte, el capital
    vigente (`principal + indexation`) se reindexa desde el evento anterior y
    causa interes compuesto con `tasa_interes_mensual` en meses comerciales.

    `indexacion_fn(capital, desde, hasta)` devuelve el MONTO de indexacion (ya
    redondeado a centavos) de `capital` entre las dos fechas -- la estrategia
    del area inyecta su propia serie IPC (Civil/Familia: indice mensual DANE con
    fallback anual, ver `CivilFamiliaStrategy._monto_indexacion`)."""

    indexacion_fn: Callable[[Decimal, date, date], Decimal]
    tasa_interes_mensual: Decimal = TASA_INTERES_MENSUAL_PURA
    fuente: str = (
        "Tasa pura mensual 0,48676 % (Suma Única con abonos, tramo a tramo, "
        "meses comerciales 30/360)"
    )

    def causar(
        self, capital_base: Decimal, desde: date, hasta: date
    ) -> tuple[Decimal, Decimal]:
        """Retorna `(indexacion_del_tramo, interes_del_tramo)`, ambos redondeados
        a centavos. El interes se calcula sobre el capital YA indexado del tramo."""
        if hasta <= desde or capital_base <= Decimal("0.00"):
            return Decimal("0.00"), Decimal("0.00")
        indexacion = self.indexacion_fn(capital_base, desde, hasta)
        capital_indexado = capital_base + indexacion
        with localcontext(CONTEXTO_FORENSE):
            interes = Rounding.money(
                interes_compuesto_tramo(
                    capital_indexado,
                    self.tasa_interes_mensual,
                    meses_comerciales_tramo(desde, hasta),
                )
            )
        return indexacion, interes


@dataclass(frozen=True)
class ResultadoLiquidacionTramoPorTramo:
    capital_insoluto_indexado: Decimal
    intereses_pendientes_cobro: Decimal
    gran_total_adeudado: Decimal


def liquidar_obligacion_con_abonos_tramo_por_tramo(
    capital_historico_inicial: Decimal,
    fecha_origen: date,
    abonos: list[tuple[date, Decimal]],
    fecha_liquidacion_final: date,
    tasa_interes_mensual: Decimal,
    indice_ipc_fn: Callable[[date], Decimal] = get_ipc_interpolado_for_date,
) -> ResultadoLiquidacionTramoPorTramo:
    """`abonos`: lista de (fecha, monto) ordenada ascendente por fecha -- el
    llamador es responsable del orden (no se reordena aqui para no ocultar un
    error de captura). `tasa_interes_mensual` es la tasa mensual pura
    (fraccion, no porcentaje -- ver `EffectiveRateConverter.annual_to_monthly`
    para derivarla del 6% EA del Art. 2232 C.C. si aplica)."""
    if capital_historico_inicial <= Decimal("0.00"):
        raise ValueError("El capital historico inicial debe ser mayor que cero.")
    if fecha_liquidacion_final <= fecha_origen:
        raise ValueError("fecha_liquidacion_final debe ser posterior a fecha_origen.")
    if tasa_interes_mensual < 0:
        raise ValueError("La tasa de interes mensual no puede ser negativa.")
    for fecha_abono, monto_abono in abonos:
        if not (fecha_origen <= fecha_abono <= fecha_liquidacion_final):
            raise ValueError(
                f"El abono del {fecha_abono} cae fuera del rango [{fecha_origen}, "
                f"{fecha_liquidacion_final}]."
            )
        if monto_abono <= Decimal("0.00"):
            raise ValueError(f"El abono del {fecha_abono} debe ser mayor que cero.")

    capital_base = capital_historico_inicial
    fecha_corte_anterior = fecha_origen
    intereses_acumulados_pendientes = Decimal("0.00")

    for fecha_abono, monto_abono in abonos:
        ipc_anterior = indice_ipc_fn(fecha_corte_anterior)
        ipc_abono = indice_ipc_fn(fecha_abono)
        capital_indexado = capital_base * (ipc_abono / ipc_anterior)

        meses_tramo = meses_comerciales_tramo(fecha_corte_anterior, fecha_abono)
        intereses_del_tramo = interes_compuesto_tramo(
            capital_indexado, tasa_interes_mensual, meses_tramo
        )
        total_intereses_adeudados = intereses_acumulados_pendientes + intereses_del_tramo

        if monto_abono >= total_intereses_adeudados:
            remanente_para_capital = monto_abono - total_intereses_adeudados
            intereses_acumulados_pendientes = Decimal("0.00")
            # Sprint 110: si el remanente del abono supera la deuda de
            # capital de este tramo, no se acota -- el sobrante se arrastraba
            # como un "capital_base" negativo a los tramos siguientes,
            # produciendo un gran_total_adeudado final absurdo (negativo). Se
            # topa en cero; que hacer con el sobrante (¿reduce tramos
            # futuros? ¿saldo a favor, Sprint 23?) sigue sin decidir con el
            # despacho. Esta funcion no la usa ninguna AreaStrategy: en
            # produccion (LiquidationCore + CausacionTramoATramo, Sprint 104)
            # el sobrante de un abono se registra como saldo a favor
            # (Sprint 23), igual que en cualquier otra liquidacion.
            capital_base = max(Decimal("0.00"), capital_indexado - remanente_para_capital)
        else:
            intereses_acumulados_pendientes = total_intereses_adeudados - monto_abono
            capital_base = capital_indexado

        fecha_corte_anterior = fecha_abono

    ipc_ultimo_corte = indice_ipc_fn(fecha_corte_anterior)
    ipc_final = indice_ipc_fn(fecha_liquidacion_final)
    capital_indexado_final = capital_base * (ipc_final / ipc_ultimo_corte)

    meses_tramo_final = meses_comerciales_tramo(fecha_corte_anterior, fecha_liquidacion_final)
    intereses_tramo_final = interes_compuesto_tramo(
        capital_indexado_final, tasa_interes_mensual, meses_tramo_final
    )
    intereses_totales_al_cierre = intereses_acumulados_pendientes + intereses_tramo_final

    capital_final = Rounding.money(capital_indexado_final)
    intereses_final = Rounding.money(intereses_totales_al_cierre)
    return ResultadoLiquidacionTramoPorTramo(
        capital_insoluto_indexado=capital_final,
        intereses_pendientes_cobro=intereses_final,
        gran_total_adeudado=capital_final + intereses_final,
    )
