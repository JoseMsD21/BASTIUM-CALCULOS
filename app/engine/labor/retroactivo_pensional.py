"""Retroactivo y reliquidacion pensional mesada por mesada (Sprint 85).

Genera la serie de mesadas atrasadas de una pension entre su fecha de
causacion (status pensional) y una fecha de corte, y liquida sobre cada
mesada, segun la respuesta del despacho del 16/11/2026
(docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 85):

1. **Intereses moratorios del Art. 141 Ley 100 de 1993** -- "Es la tasa
   maxima de interes moratorio vigente (tasa de usura) certificada por la
   Superfinanciera". Se liquidan dia a dia, con la tasa de usura certificada
   vigente en cada dia de mora (linea Consumo y Ordinario, la misma serie de
   parametros_legales que usan el Art. 65 CST y el E.T. 635), convertida a
   diaria con la formula efectiva compuesta (`annual_to_daily`, "Opcion B":
   la que el motor reserva para tasas certificadas EA como la usura -- ver
   EffectiveRateConverter). Sprint 110 ("NUNCA extrapolar"): la mora solo
   causa interes hasta el ultimo dia con usura certificada; el resto queda
   "Pendiente de Certificacion Oficial" con la alerta de
   `mensaje_pendiente_certificacion_usura`.
2. **Excepcion de buena fe estricta o cambio jurisprudencial** -- "solo
   aplica la indexacion por IPC, sin intereses de usura". Cada mesada se
   indexa desde su exigibilidad hasta el corte (Mesada x IPC final / IPC
   inicial, Art. 21 Ley 100), con el indice IPC mensual del DANE interpolado
   por dias y fallback completo a la interpolacion anual fuera de rango (mismo
   criterio que CivilFamiliaStrategy._evento_indexacion, Sprint 80). Ambos
   conceptos son excluyentes: nunca se liquidan los dos sobre la misma mesada.

**Incremento pensional del 14 %/7 % (plantilla P1A): NO se modela.** El
despacho respondio que "NO sigue vigente. La Corte Constitucional (SU-140 de
2019) determino que no aplican para pensiones causadas con posterioridad a la
Ley 100 de 1993 o al Acto Legislativo 01 de 2005". El sistema nunca lo tuvo
modelado, asi que este motor no lo agrega para ninguna pension; un eventual
soporte para pensiones causadas antes de esas normas queda fuera de alcance
(la respuesta no da la regla de aplicacion para ese caso).

Supuestos de este motor (NO confirmados por el despacho -- documentados para
revision, ver Pendientes.md, Sprint 85):

- **Reajuste anual de la mesada:** no hay regla confirmada del reajuste anual
  de pensiones (Art. 14 Ley 100) en Respondidas. El motor ofrece dos modos:
  `SALARIO_MINIMO` (la mesada de cada año es el SMLMV de ese año -- plantilla
  P1, "mesadas incrementadas a salario minimo", tabla SMLMV de
  parametros_legales) y `PORCENTAJE` (el usuario entrega el porcentaje de
  reajuste de cada año; el motor NO lo deduce del IPC ni de otra fuente). En
  `PORCENTAJE` la mesada del año Y = mesada(Y-1) x (1 + pct(Y)/100),
  redondeada a centavos, aplicada desde el 1 de enero de Y.
- **Exigibilidad:** la mesada de un mes se hace exigible el ultimo dia
  calendario de ese mes; la mora corre desde el dia siguiente hasta el corte
  (inclusive). Solo entran al retroactivo las mesadas ya exigibles al corte.
- **Mesadas adicionales:** `mesadas_por_anio` (12, 13 o 14) es dato de
  entrada. Si no se indican los meses, se usan los del texto de la Ley 100:
  la adicional de 13 en noviembre (Art. 50) y, con 14, tambien la de junio
  (Art. 142). Cada adicional vale una mesada completa del año, es exigible el
  mismo dia que la ordinaria de su mes y solo entra si su mes es igual o
  posterior al de causacion. El motor no decide si la pension tiene derecho a
  la mesada 14 (Acto Legislativo 01 de 2005): eso lo indica el usuario.
- **Primer mes:** si la causacion no es el dia 1, la mesada ordinaria de ese
  mes se prorratea por dias sobre un mes comercial de 30 dias (dias 31 no
  cuentan; un mes de febrero causado el 28 da 3 dias).
- **Prescripcion trienal de mesadas:** no se aplica (no la pide el Sprint 85).
"""

from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum

from app.core.exceptions import IPCMensualNoDisponibleError
from app.engine.indexation.historical_index import (
    get_ipc_interpolado_for_date,
    get_ipc_interpolado_mensual_for_date,
    get_smlmv_for_year,
    get_tramos_ibc_usura_between,
    get_ultima_fecha_certificada_ibc_usura,
    mensaje_pendiente_certificacion_usura,
)
from app.engine.indexation.ipc import IPCIndexation
from app.engine.interest.rate_conversion import EffectiveRateConverter
from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils

RUBRO_MORA_ART_141 = "Intereses moratorios de mesadas pensionales (Art. 141 Ley 100 de 1993)"

# Texto de la Ley 100 de 1993: Art. 50 (mesada adicional de noviembre) y
# Art. 142 (mesada adicional de junio). Solo se usa si el llamador no indica
# los meses -- ver docstring del modulo.
MESES_MESADAS_ADICIONALES_LEY_100: dict[int, tuple[int, ...]] = {
    12: (),
    13: (11,),
    14: (6, 11),
}

_DIAS_MES_COMERCIAL = 30
_CERO = Decimal("0.00")


class ModoReajusteMesada(Enum):
    SALARIO_MINIMO = "salario_minimo"
    PORCENTAJE = "porcentaje"


class CriterioMoraPensional(Enum):
    INTERES_MORATORIO_ART_141 = "interes_moratorio_art_141"
    INDEXACION_IPC_BUENA_FE = "indexacion_ipc_buena_fe"


class TipoMesada(Enum):
    ORDINARIA = "ordinaria"
    ADICIONAL = "adicional"


@dataclass(frozen=True)
class Mesada:
    periodo: date  # primer dia del mes al que corresponde
    tipo: TipoMesada
    fecha_exigibilidad: date
    valor: Decimal
    dias_causados: int = _DIAS_MES_COMERCIAL


@dataclass(frozen=True)
class InteresMoraPensional:
    interes: Decimal
    dias_mora: int
    dias_pendientes_certificacion: int = 0
    ultima_fecha_usura_certificada: date | None = None


@dataclass(frozen=True)
class MesadaLiquidada:
    periodo: date
    tipo: TipoMesada
    fecha_exigibilidad: date
    valor: Decimal
    dias_causados: int
    dias_mora: int
    dias_mora_pendientes_certificacion: int
    interes_moratorio: Decimal
    indexacion: Decimal


@dataclass(frozen=True)
class RetroactivoPensionalResult:
    criterio: CriterioMoraPensional
    mesadas: tuple[MesadaLiquidada, ...]
    total_mesadas: Decimal
    total_intereses_moratorios: Decimal
    total_indexacion: Decimal
    total: Decimal
    ultima_fecha_usura_certificada: date | None
    alertas: tuple[str, ...]


def _ultimo_dia_del_mes(anio: int, mes: int) -> date:
    return CalendarUtils.safe_create_date(anio, mes, 31)


def _valores_anuales(
    anio_inicio: int,
    anio_fin: int,
    modo_reajuste: ModoReajusteMesada,
    mesada_inicial: Decimal | None,
    reajustes_pct_por_anio: dict[int, Decimal] | None,
) -> dict[int, Decimal]:
    if modo_reajuste == ModoReajusteMesada.SALARIO_MINIMO:
        return {anio: get_smlmv_for_year(anio) for anio in range(anio_inicio, anio_fin + 1)}

    if mesada_inicial is None or mesada_inicial <= _CERO:
        raise ValueError("El modo PORCENTAJE exige una mesada inicial mayor que cero.")
    reajustes = reajustes_pct_por_anio or {}
    valores = {anio_inicio: Rounding.money(mesada_inicial)}
    for anio in range(anio_inicio + 1, anio_fin + 1):
        if anio not in reajustes:
            raise ValueError(
                f"Falta el porcentaje de reajuste de la mesada para el año {anio} "
                "(el motor no lo deduce: debe entregarse como dato)."
            )
        anterior = valores[anio - 1]
        valores[anio] = Rounding.money(anterior + anterior * reajustes[anio] / Decimal("100"))
    return valores


def generar_mesadas(
    fecha_causacion: date,
    fecha_corte: date,
    mesadas_por_anio: int,
    modo_reajuste: ModoReajusteMesada,
    mesada_inicial: Decimal | None = None,
    reajustes_pct_por_anio: dict[int, Decimal] | None = None,
    meses_mesadas_adicionales: tuple[int, ...] | None = None,
) -> list[Mesada]:
    """Serie cronologica de mesadas (ordinarias y adicionales) exigibles al
    `fecha_corte`, desde el mes de `fecha_causacion`. Ver supuestos en el
    docstring del modulo."""
    if mesadas_por_anio not in MESES_MESADAS_ADICIONALES_LEY_100:
        raise ValueError("El numero de mesadas al año debe ser 12, 13 o 14.")
    if fecha_corte < fecha_causacion:
        raise ValueError("La fecha de corte no puede ser anterior a la fecha de causacion.")
    if meses_mesadas_adicionales is None:
        meses_mesadas_adicionales = MESES_MESADAS_ADICIONALES_LEY_100[mesadas_por_anio]
    elif len(meses_mesadas_adicionales) != mesadas_por_anio - 12:
        raise ValueError(
            "La cantidad de meses de mesadas adicionales no coincide con el numero de "
            "mesadas al año."
        )

    # Año de la ultima mesada exigible al corte (el mes del corte solo cuenta
    # si el corte es su ultimo dia): no se exige reajuste de un año sin mesadas.
    anio_ultima = fecha_corte.year
    if fecha_corte < _ultimo_dia_del_mes(fecha_corte.year, fecha_corte.month) and (
        fecha_corte.month == 1
    ):
        anio_ultima -= 1
    if anio_ultima < fecha_causacion.year:
        return []
    valores = _valores_anuales(
        fecha_causacion.year, anio_ultima, modo_reajuste, mesada_inicial,
        reajustes_pct_por_anio,
    )

    mesadas: list[Mesada] = []
    anio, mes = fecha_causacion.year, fecha_causacion.month
    while True:
        exigibilidad = _ultimo_dia_del_mes(anio, mes)
        if exigibilidad > fecha_corte:
            break
        valor_mes = valores[anio]
        periodo = date(anio, mes, 1)

        dias = _DIAS_MES_COMERCIAL
        valor_ordinaria = valor_mes
        if periodo < fecha_causacion:
            dias = _DIAS_MES_COMERCIAL - min(fecha_causacion.day, _DIAS_MES_COMERCIAL) + 1
            valor_ordinaria = Rounding.money(
                valor_mes * Decimal(dias) / Decimal(_DIAS_MES_COMERCIAL)
            )
        mesadas.append(Mesada(periodo, TipoMesada.ORDINARIA, exigibilidad, valor_ordinaria, dias))
        if mes in meses_mesadas_adicionales:
            mesadas.append(Mesada(periodo, TipoMesada.ADICIONAL, exigibilidad, valor_mes))

        anio, mes = (anio + 1, 1) if mes == 12 else (anio, mes + 1)
    return mesadas


def interes_mora_pensional(
    valor_mesada: Decimal, fecha_exigibilidad: date, fecha_corte: date
) -> InteresMoraPensional:
    """Interes moratorio del Art. 141 Ley 100 sobre una mesada: dia a dia,
    desde el dia siguiente a `fecha_exigibilidad` hasta `fecha_corte`, con la
    tasa de usura certificada vigente cada dia (efectiva compuesta a diaria).
    Se suma C x i_diaria x dias por tramo de usura a precision completa y se
    redondea una sola vez, al final. Sprint 110: los dias posteriores al
    ultimo tramo certificado no causan interes y se reportan aparte."""
    inicio_mora = fecha_exigibilidad + timedelta(days=1)
    dias_mora = max((fecha_corte - fecha_exigibilidad).days, 0)
    if dias_mora == 0 or valor_mesada <= _CERO:
        return InteresMoraPensional(_CERO, dias_mora)

    ultima_certificada = get_ultima_fecha_certificada_ibc_usura()
    fin_certificado = fecha_corte
    if ultima_certificada is not None and ultima_certificada < fecha_corte:
        fin_certificado = ultima_certificada
    dias_pendientes = (fecha_corte - max(fin_certificado, fecha_exigibilidad)).days

    interes = Decimal("0")
    if fin_certificado >= inicio_mora:
        for tramo in get_tramos_ibc_usura_between(inicio_mora, fin_certificado):
            desde = max(tramo.inicio, inicio_mora)
            hasta = min(tramo.fin, fin_certificado)
            dias = (hasta - desde).days + 1
            tasa_diaria = EffectiveRateConverter.annual_to_daily(tramo.usura_anual).decimal()
            interes += valor_mesada * tasa_diaria * Decimal(dias)

    return InteresMoraPensional(
        interes=Rounding.money(interes),
        dias_mora=dias_mora,
        dias_pendientes_certificacion=dias_pendientes,
        ultima_fecha_usura_certificada=ultima_certificada if dias_pendientes else None,
    )


def indexacion_mesada_ipc(
    valor_mesada: Decimal, fecha_exigibilidad: date, fecha_corte: date
) -> Decimal:
    """Indexacion IPC de una mesada (excepcion de buena fe / cambio
    jurisprudencial): solo el delta Mesada x (IPC final / IPC inicial - 1).
    Indice mensual interpolado por dias; si alguna de las dos fechas no tiene
    indice mensual, ambas pasan a la interpolacion anual (nunca se mezclan
    series de bases distintas)."""
    try:
        inicial = get_ipc_interpolado_mensual_for_date(fecha_exigibilidad)
        final = get_ipc_interpolado_mensual_for_date(fecha_corte)
    except IPCMensualNoDisponibleError:
        inicial = get_ipc_interpolado_for_date(fecha_exigibilidad)
        final = get_ipc_interpolado_for_date(fecha_corte)
    return IPCIndexation.calculate(valor_mesada, inicial, final)


def calcular_retroactivo_pensional(
    fecha_causacion: date,
    fecha_corte: date,
    mesadas_por_anio: int,
    modo_reajuste: ModoReajusteMesada,
    mesada_inicial: Decimal | None = None,
    reajustes_pct_por_anio: dict[int, Decimal] | None = None,
    buena_fe_o_cambio_jurisprudencial: bool = False,
    meses_mesadas_adicionales: tuple[int, ...] | None = None,
) -> RetroactivoPensionalResult:
    """Retroactivo pensional completo: serie de mesadas + intereses
    moratorios del Art. 141 (o, con `buena_fe_o_cambio_jurisprudencial`,
    solo indexacion IPC). Si alguna mesada tiene mora posterior al ultimo dia
    de usura certificada, agrega una unica alerta "Pendiente de Certificacion
    Oficial" (Sprint 110)."""
    mesadas = generar_mesadas(
        fecha_causacion, fecha_corte, mesadas_por_anio, modo_reajuste, mesada_inicial,
        reajustes_pct_por_anio, meses_mesadas_adicionales,
    )
    criterio = (
        CriterioMoraPensional.INDEXACION_IPC_BUENA_FE
        if buena_fe_o_cambio_jurisprudencial
        else CriterioMoraPensional.INTERES_MORATORIO_ART_141
    )

    liquidadas: list[MesadaLiquidada] = []
    ultima_certificada: date | None = None
    for mesada in mesadas:
        dias_mora = max((fecha_corte - mesada.fecha_exigibilidad).days, 0)
        interes = _CERO
        indexacion = _CERO
        pendientes = 0
        if criterio == CriterioMoraPensional.INDEXACION_IPC_BUENA_FE:
            if dias_mora > 0:
                indexacion = indexacion_mesada_ipc(
                    mesada.valor, mesada.fecha_exigibilidad, fecha_corte
                )
        else:
            mora = interes_mora_pensional(mesada.valor, mesada.fecha_exigibilidad, fecha_corte)
            interes = mora.interes
            pendientes = mora.dias_pendientes_certificacion
            if mora.ultima_fecha_usura_certificada is not None:
                ultima_certificada = mora.ultima_fecha_usura_certificada
        liquidadas.append(
            MesadaLiquidada(
                periodo=mesada.periodo,
                tipo=mesada.tipo,
                fecha_exigibilidad=mesada.fecha_exigibilidad,
                valor=mesada.valor,
                dias_causados=mesada.dias_causados,
                dias_mora=dias_mora,
                dias_mora_pendientes_certificacion=pendientes,
                interes_moratorio=interes,
                indexacion=indexacion,
            )
        )

    total_mesadas = sum((m.valor for m in liquidadas), _CERO)
    total_intereses = sum((m.interes_moratorio for m in liquidadas), _CERO)
    total_indexacion = sum((m.indexacion for m in liquidadas), _CERO)
    alertas: tuple[str, ...] = ()
    if ultima_certificada is not None:
        alertas = (mensaje_pendiente_certificacion_usura(RUBRO_MORA_ART_141, ultima_certificada),)

    return RetroactivoPensionalResult(
        criterio=criterio,
        mesadas=tuple(liquidadas),
        total_mesadas=total_mesadas,
        total_intereses_moratorios=total_intereses,
        total_indexacion=total_indexacion,
        total=total_mesadas + total_intereses + total_indexacion,
        ultima_fecha_usura_certificada=ultima_certificada,
        alertas=alertas,
    )
