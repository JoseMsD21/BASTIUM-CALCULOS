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
- Conteo de dias por tramo: se reutiliza `CalendarUtils.dias_comerciales_360`
  (mismo criterio "mes de 30 dias, año de 360" que el propio despacho
  describe en su comentario, y que el motor ya usa en otros contextos desde
  el Sprint 30) -- SIN el +1 inclusivo que Laboral confirmo especificamente
  para prestaciones sociales (Sprint 78): ese +1 no fue confirmado para este
  contexto.
- Indice IPC: se reutiliza `get_ipc_interpolado_for_date` (Sprint 8), en vez
  de recibir la serie como parametro -- mismo patron de composicion con
  infraestructura ya existente que otras funciones aisladas de esta rutina
  (ej. condena_administrativa_dtf.py, Sprint 82).

Funcion AISLADA -- deliberadamente sin cablear a `AreaStrategy`/
`_evento_indexacion_ipc` (ver docs/Pendientes.md, Sprint 104): cablearla
exige que `_eventos_de_obligacion` conozca las fechas de los abonos al
momento de generar los eventos de causacion (hoy no lo hace, es un cambio de
arquitectura del pipeline de liquidacion, no una correccion mecanica), y
ademas se solapa con la pregunta todavia abierta del Sprint 76/83 sobre que
formula de interes aplica junto con la indexacion en Suma Unica (que hoy no
esta conectada a ningun area real). Verificar la formula con tests y dejarla
sin conectar evita tocar codigo de calculo juridico que ya esta en
produccion sin haber resuelto esas dos piezas. Ver
docs/Preguntas-Para-Abogado-Abiertas.md, "Sprint 104 (seguimiento)".
"""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils

DIAS_MES_COMERCIAL = Decimal("30")


@dataclass(frozen=True)
class ResultadoLiquidacionTramoPorTramo:
    capital_insoluto_indexado: Decimal
    intereses_pendientes_cobro: Decimal
    gran_total_adeudado: Decimal


def _dias_y_meses_tramo(fecha_inicio: date, fecha_fin: date) -> Decimal:
    dias_tramo = Decimal(CalendarUtils.dias_comerciales_360(fecha_inicio, fecha_fin))
    return dias_tramo / DIAS_MES_COMERCIAL


def _interes_compuesto_tramo(
    capital: Decimal, tasa_interes_mensual: Decimal, n_meses: Decimal
) -> Decimal:
    return capital * ((Decimal("1") + tasa_interes_mensual) ** n_meses - Decimal("1"))


def liquidar_obligacion_con_abonos_tramo_por_tramo(
    capital_historico_inicial: Decimal,
    fecha_origen: date,
    abonos: list[tuple[date, Decimal]],
    fecha_liquidacion_final: date,
    tasa_interes_mensual: Decimal,
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
        ipc_anterior = get_ipc_interpolado_for_date(fecha_corte_anterior)
        ipc_abono = get_ipc_interpolado_for_date(fecha_abono)
        capital_indexado = capital_base * (ipc_abono / ipc_anterior)

        meses_tramo = _dias_y_meses_tramo(fecha_corte_anterior, fecha_abono)
        intereses_del_tramo = _interes_compuesto_tramo(
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
            # despacho (ver docs/Preguntas-Para-Abogado-Abiertas.md, "Sprint
            # 104 (seguimiento)") -- esta funcion sigue deliberadamente sin
            # cablear a ningun AreaStrategy (Sprint 104), asi que este tope
            # no afecta ninguna liquidacion real hoy.
            capital_base = max(Decimal("0.00"), capital_indexado - remanente_para_capital)
        else:
            intereses_acumulados_pendientes = total_intereses_adeudados - monto_abono
            capital_base = capital_indexado

        fecha_corte_anterior = fecha_abono

    ipc_ultimo_corte = get_ipc_interpolado_for_date(fecha_corte_anterior)
    ipc_final = get_ipc_interpolado_for_date(fecha_liquidacion_final)
    capital_indexado_final = capital_base * (ipc_final / ipc_ultimo_corte)

    meses_tramo_final = _dias_y_meses_tramo(fecha_corte_anterior, fecha_liquidacion_final)
    intereses_tramo_final = _interes_compuesto_tramo(
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
