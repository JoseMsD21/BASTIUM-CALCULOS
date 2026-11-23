"""Contrato realidad (Sprint 94): liquidacion indexada, año por año, de las
prestaciones sociales y los aportes que un trabajador disfrazado de
contratista nunca recibio.

Reproduce las formulas de las plantillas del despacho
`L7.LIQUIDACIONDEPRESTACIONESSOCIALESENCONTRATOREALIDAD` (privado) y
`L8.LIQUIDACIONDEPRESTACIONESSOCIALESPUBLICOCONTRATOREALIDAD` (sector
publico), con dos correcciones dadas por el despacho (respuesta del
16/11/2026, `docs/Preguntas-Para-Abogado-Respondidas.md`, "Sprint 94" y
"Sprint 94 (seguimiento)"):

1. Aportes a salud/pension: "el empleador sancionado debe cubrir el 100 % del
   calculo actuarial o de la cotizacion omisa. No puede descontar
   retroactivamente la porcion del 4 % a cargo del trabajador". Las
   plantillas usaban solo la porcion del empleador (8,5 %/12 % en L7,
   8 %/12 % en L8); aqui se usa el porcentaje TOTAL ya parametrizado
   (`SS_SALUD_PCT` = 12,5 %, `SS_PENSION_PCT` = 16 %, los mismos del Sprint
   16). Alternativamente, la pension se puede reclamar por el valor del
   calculo actuarial (`calculo_actuarial.py`, Sprints 86/87): en ese caso
   reemplaza la columna de aporte a pension (no se suman ambas).
2. Bonificacion por servicio del Decreto 0320/2026: exclusiva del sector
   publico; NUNCA aplica al privado (donde rigen las reglas del CST). Desde
   el 01/01/2026: 53 % si Asignacion Basica + Gastos de Representacion <=
   $2.968.262, 38 % si lo supera; desde 2027, 54 %/39 %. Para años anteriores
   a 2026 se usa el porcentaje que el usuario escribe, igual que la casilla
   de la plantilla L8 ("corresponde al 35 %, pero hasta 2 smmlv, escriba
   50 %") -- el despacho no confirmo una regla automatica para esos años.

Indexacion: la plantilla toma como "IPC" del año Y el indice de cierre del
año Y-1 (su tabla trae 2019 = 100,00 y 2020 = 103,80, cierre de 2019), y
indexa cada valor por `IPC(año final) / IPC(año)`. Aqui se usa la serie
`IPC_INDICE_ACUMULADO` de `parametros_legales` (`get_ipc_for_date`).

Limites deliberados (no se adivinaron):
- El tope del Decreto 0320 solo se conoce para 2026; para 2027+ el llamador
  debe dar `tope_decreto_0320` (si no, ValueError).
- `SS_SALUD_PCT`/`SS_PENSION_PCT` se resuelven por fecha (1 de enero de
  cada año) contra `parametros_legales`; hoy la tabla trae un solo valor
  sin vigencia historica.
- Las formulas de L7/L8 se reproducen tal cual (incluidos los auxilios de
  transporte/alimentacion de L8, que la plantilla indexa como un solo valor
  por año y usa como valor mensual en la base de vacaciones); no se
  corrigen por criterio propio.

Sin conectar a la UI ni a `LaboralStrategy` todavia.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from enum import Enum

from app.engine.labor.calculo_actuarial import ReservaActuarial
from app.engine.math.rounding import Rounding

_CERO = Decimal("0")
_CIEN = Decimal("100")

# Decreto 0320 de 2026 (respuesta del despacho 22/08/2026, confirmada
# 16/11/2026): bonificacion por servicio de servidores publicos/territoriales.
ANIO_INICIO_DECRETO_0320 = 2026
TOPE_DECRETO_0320_2026 = Decimal("2968262")
_PORCENTAJES_DECRETO_0320 = {
    # año desde: (hasta el tope, sobre el tope)
    2026: (Decimal("53"), Decimal("38")),
    2027: (Decimal("54"), Decimal("39")),
}


class SectorContratoRealidad(Enum):
    PRIVADO = "privado"  # plantilla L7, reglas del CST
    PUBLICO = "publico"  # plantilla L8, empleo publico


# --------------------------------------------------------------------------
# Piezas aritmeticas (avance parcial 2026-08-21)
# --------------------------------------------------------------------------


def calcular_aporte_contrato_realidad(base, porcentaje) -> Decimal:
    """`base x porcentaje/100`, redondeado a centavos.

    El consolidado (`liquidar_contrato_realidad_*`) usa el porcentaje TOTAL
    (empleador + trabajador) por instruccion del despacho; esta funcion no
    trae ningun porcentaje hardcodeado."""
    base = Decimal(str(base))
    porcentaje = Decimal(str(porcentaje))
    if base < 0:
        raise ValueError("La base no puede ser negativa.")
    if porcentaje < 0:
        raise ValueError("El porcentaje no puede ser negativo.")

    return Rounding.money(base * porcentaje / _CIEN)


def calcular_bonificacion_por_servicio_escalonada(
    base, aplica_porcentaje_elevado, porcentaje_estandar, porcentaje_elevado
) -> Decimal:
    """`base x porcentaje/100`, con `porcentaje_elevado` si
    `aplica_porcentaje_elevado` o `porcentaje_estandar` si no. Estructura
    generica "porcentaje condicionado a un tope"; la regla concreta del
    Decreto 0320/2026 esta en `porcentaje_bonificacion_por_servicio`."""
    base = Decimal(str(base))
    porcentaje_estandar = Decimal(str(porcentaje_estandar))
    porcentaje_elevado = Decimal(str(porcentaje_elevado))
    if base < 0:
        raise ValueError("La base no puede ser negativa.")
    if porcentaje_estandar < 0 or porcentaje_elevado < 0:
        raise ValueError("El porcentaje no puede ser negativo.")

    porcentaje = porcentaje_elevado if aplica_porcentaje_elevado else porcentaje_estandar
    return Rounding.money(base * porcentaje / _CIEN)


def porcentaje_bonificacion_por_servicio(
    sector: SectorContratoRealidad,
    anio: int,
    asignacion_basica,
    gastos_representacion=_CERO,
    porcentaje_usuario=None,
    tope_decreto_0320=None,
) -> Decimal:
    """Porcentaje de la bonificacion por servicio para `anio`.

    - Sector privado: ValueError (el Decreto 0320/2026 no aplica al privado y
      la plantilla L7 no tiene este concepto).
    - Sector publico, año >= 2026: Decreto 0320/2026. Si
      `asignacion_basica + gastos_representacion <= tope` -> 53 % (54 % desde
      2027); si lo supera -> 38 % (39 % desde 2027). El tope de 2026 es
      $2.968.262; para 2027+ el llamador debe dar `tope_decreto_0320`.
      `porcentaje_usuario` se ignora: el decreto prevalece.
    - Sector publico, año < 2026: `porcentaje_usuario` (la casilla de la
      plantilla L8); si falta, ValueError.
    """
    if sector is SectorContratoRealidad.PRIVADO:
        raise ValueError(
            "La bonificacion por servicio (Decreto 0320/2026) es exclusiva del sector "
            "publico; no aplica a contratos realidad del sector privado."
        )
    if anio < ANIO_INICIO_DECRETO_0320:
        if porcentaje_usuario is None:
            raise ValueError(
                f"Para {anio} (antes del Decreto 0320/2026) debe indicarse el porcentaje "
                "de bonificacion por servicio."
            )
        porcentaje = Decimal(str(porcentaje_usuario))
        if porcentaje < 0:
            raise ValueError("El porcentaje no puede ser negativo.")
        return porcentaje

    if tope_decreto_0320 is None:
        if anio != ANIO_INICIO_DECRETO_0320:
            raise ValueError(
                f"El despacho solo dio el tope del Decreto 0320 para 2026; para {anio} "
                "debe indicarse `tope_decreto_0320`."
            )
        tope = TOPE_DECRETO_0320_2026
    else:
        tope = Decimal(str(tope_decreto_0320))
    base = Decimal(str(asignacion_basica)) + Decimal(str(gastos_representacion))
    desde = max(a for a in _PORCENTAJES_DECRETO_0320 if a <= anio)
    hasta_tope, sobre_tope = _PORCENTAJES_DECRETO_0320[desde]
    return hasta_tope if base <= tope else sobre_tope


# --------------------------------------------------------------------------
# Consolidado multi-año
# --------------------------------------------------------------------------


def _ipc_cierre_parametro(anio: int) -> Decimal:
    from app.engine.indexation.historical_index import get_ipc_for_date

    return get_ipc_for_date(date(anio, 12, 31))


def _pct_parametro(clave: str) -> Callable[[int], Decimal]:
    def resolver(anio: int) -> Decimal:
        from app.services.parametro_service import get_parametro

        return get_parametro(clave, date(anio, 1, 1))

    return resolver


def _factor_ipc(anio: int, anio_final: int, ipc_cierre: Callable[[int], Decimal]) -> Decimal:
    """`IPC(final)/IPC(año)`, con IPC(Y) = indice de cierre de Y-1."""
    if anio == anio_final:
        return Decimal("1")
    return ipc_cierre(anio_final - 1) / ipc_cierre(anio - 1)


def _monto_calculo_actuarial(valor) -> Decimal | None:
    if valor is None:
        return None
    monto = valor.vr if isinstance(valor, ReservaActuarial) else Decimal(str(valor))
    if monto < 0:
        raise ValueError("El calculo actuarial de pension no puede ser negativo.")
    return Rounding.money(monto)


def _no_negativo(valor: Decimal, nombre: str) -> Decimal:
    valor = Decimal(str(valor))
    if valor < 0:
        raise ValueError(f"{nombre} no puede ser negativo.")
    return valor


def _validar_comunes(filas: Sequence, anio_final: int) -> None:
    if not filas:
        raise ValueError("Debe haber al menos un año a liquidar.")
    for fila in filas:
        if fila.anio > anio_final:
            raise ValueError(
                f"El año {fila.anio} es posterior al año final de indexacion {anio_final}."
            )


def _suma(valores) -> Decimal:
    return sum(valores, Rounding.money(_CERO))


# ---- Privado (L7) --------------------------------------------------------


@dataclass(frozen=True)
class AnioContratoRealidadPrivado:
    anio: int
    salario_mensual: Decimal  # "salario promedio mensual por año"
    meses: Decimal  # "# de meses" (admite fraccion de mes)


@dataclass(frozen=True)
class FilaContratoRealidadPrivado:
    anio: int
    factor_ipc: Decimal
    total_salarios: Decimal
    cesantias: Decimal
    cesantias_indexadas: Decimal
    intereses_cesantias: Decimal
    primas: Decimal
    primas_indexadas: Decimal
    vacaciones: Decimal
    vacaciones_indexadas: Decimal
    aporte_salud: Decimal
    aporte_pension: Decimal


@dataclass(frozen=True)
class LiquidacionContratoRealidadPrivado:
    filas: list[FilaContratoRealidadPrivado] = field(default_factory=list)
    total_salarios_sin_percibir: Decimal = _CERO
    total_cesantias_indexadas: Decimal = _CERO
    total_intereses_cesantias: Decimal = _CERO
    total_primas_indexadas: Decimal = _CERO
    total_vacaciones_indexadas: Decimal = _CERO
    total_prestaciones_indexadas: Decimal = _CERO
    total_aportes_salud: Decimal = _CERO
    total_aportes_pension: Decimal = _CERO
    total_prestaciones_sociales: Decimal = _CERO
    total_prestaciones_mas_salarios: Decimal = _CERO
    pension_por_calculo_actuarial: bool = False


def liquidar_contrato_realidad_privado(
    filas: Sequence[AnioContratoRealidadPrivado],
    anio_final: int,
    calculo_actuarial_pension: ReservaActuarial | Decimal | None = None,
    *,
    ipc_cierre: Callable[[int], Decimal] | None = None,
    pct_salud_total: Callable[[int], Decimal] | None = None,
    pct_pension_total: Callable[[int], Decimal] | None = None,
) -> LiquidacionContratoRealidadPrivado:
    """Plantilla L7 (privado), por fila (S = salario mensual, G = meses,
    f = factor IPC):

    - salarios = S x G (el consolidado los suma SIN indexar, como L7)
    - cesantias = S/12 x G; indexadas x f
    - intereses = cesantias indexadas x G/100 (12 % anual prorrateado)
    - primas = S/12 x G; indexadas x f
    - vacaciones = primas/2; indexadas x f
    - aporte salud/pension = salarios x f x porcentaje TOTAL (100 % de la
      cotizacion omisa, sin descontar el 4 % del trabajador)

    Si se da `calculo_actuarial_pension` (ReservaActuarial -> se usa `vr`, o
    un monto), el aporte a pension de cada fila es 0 y el total de pension es
    ese valor. Sin bonificacion por servicio (no aplica al privado).
    `ipc_cierre`/`pct_*` son inyectables; por defecto se leen de
    `parametros_legales`."""
    _validar_comunes(filas, anio_final)
    ipc_cierre = ipc_cierre or _ipc_cierre_parametro
    pct_salud = pct_salud_total or _pct_parametro("SS_SALUD_PCT")
    pct_pension = pct_pension_total or _pct_parametro("SS_PENSION_PCT")
    actuarial = _monto_calculo_actuarial(calculo_actuarial_pension)

    resultado: list[FilaContratoRealidadPrivado] = []
    for entrada in filas:
        salario = _no_negativo(entrada.salario_mensual, "El salario")
        meses = _no_negativo(entrada.meses, "El numero de meses")
        if meses > 12:
            raise ValueError("El numero de meses por año no puede superar 12.")
        f = _factor_ipc(entrada.anio, anio_final, ipc_cierre)

        salarios = salario * meses
        cesantias = salario / 12 * meses
        cesantias_idx = cesantias * f
        primas = cesantias
        vacaciones = primas / 2
        base_aportes = salarios * f
        resultado.append(
            FilaContratoRealidadPrivado(
                anio=entrada.anio,
                factor_ipc=f,
                total_salarios=Rounding.money(salarios),
                cesantias=Rounding.money(cesantias),
                cesantias_indexadas=Rounding.money(cesantias_idx),
                intereses_cesantias=Rounding.money(cesantias_idx * meses / _CIEN),
                primas=Rounding.money(primas),
                primas_indexadas=Rounding.money(primas * f),
                vacaciones=Rounding.money(vacaciones),
                vacaciones_indexadas=Rounding.money(vacaciones * f),
                aporte_salud=Rounding.money(base_aportes * pct_salud(entrada.anio)),
                aporte_pension=Rounding.money(
                    _CERO if actuarial is not None else base_aportes * pct_pension(entrada.anio)
                ),
            )
        )

    total_ces = _suma(r.cesantias_indexadas for r in resultado)
    total_int = _suma(r.intereses_cesantias for r in resultado)
    total_pri = _suma(r.primas_indexadas for r in resultado)
    total_vac = _suma(r.vacaciones_indexadas for r in resultado)
    total_prest = total_ces + total_int + total_pri + total_vac
    total_salud = _suma(r.aporte_salud for r in resultado)
    total_pension = (
        actuarial if actuarial is not None else _suma(r.aporte_pension for r in resultado)
    )
    total_salarios = _suma(r.total_salarios for r in resultado)
    total_sociales = total_prest + total_salud + total_pension
    return LiquidacionContratoRealidadPrivado(
        filas=resultado,
        total_salarios_sin_percibir=total_salarios,
        total_cesantias_indexadas=total_ces,
        total_intereses_cesantias=total_int,
        total_primas_indexadas=total_pri,
        total_vacaciones_indexadas=total_vac,
        total_prestaciones_indexadas=total_prest,
        total_aportes_salud=total_salud,
        total_aportes_pension=total_pension,
        total_prestaciones_sociales=total_sociales,
        total_prestaciones_mas_salarios=total_sociales + total_salarios,
        pension_por_calculo_actuarial=actuarial is not None,
    )


# ---- Publico (L8) --------------------------------------------------------


@dataclass(frozen=True)
class AnioContratoRealidadPublico:
    anio: int
    dias: Decimal  # "# dias por año" (base 360)
    meses: Decimal  # "# meses completos por año"
    salario_mensual: Decimal  # asignacion basica mensual
    auxilio_transporte: Decimal = _CERO
    auxilio_alimentacion: Decimal = _CERO
    # Solo para la bonificacion por servicio del Decreto 0320/2026 (base y
    # condicion del tope: asignacion basica + gastos de representacion).
    gastos_representacion: Decimal = _CERO


@dataclass(frozen=True)
class FilaContratoRealidadPublico:
    anio: int
    factor_ipc: Decimal
    auxilio_transporte_indexado: Decimal
    auxilio_alimentacion_indexado: Decimal
    total_salarios: Decimal
    cesantias: Decimal
    cesantias_indexadas: Decimal
    intereses_cesantias: Decimal
    prima_servicio: Decimal
    prima_servicio_indexada: Decimal
    prima_navidad: Decimal
    prima_navidad_indexada: Decimal
    vacaciones: Decimal
    vacaciones_indexadas: Decimal
    prima_vacaciones: Decimal
    prima_vacaciones_indexada: Decimal
    porcentaje_bonificacion_servicio: Decimal
    bonificacion_servicio: Decimal
    bonificacion_servicio_indexada: Decimal
    bonificacion_recreacion: Decimal
    bonificacion_recreacion_indexada: Decimal
    aporte_salud: Decimal
    aporte_pension: Decimal


@dataclass(frozen=True)
class LiquidacionContratoRealidadPublico:
    filas: list[FilaContratoRealidadPublico] = field(default_factory=list)
    total_auxilio_transporte_indexado: Decimal = _CERO
    total_auxilio_alimentacion_indexado: Decimal = _CERO
    total_cesantias_indexadas: Decimal = _CERO
    total_intereses_cesantias: Decimal = _CERO
    total_prima_servicio_indexada: Decimal = _CERO
    total_prima_navidad_indexada: Decimal = _CERO
    total_vacaciones_indexadas: Decimal = _CERO
    total_prima_vacaciones_indexada: Decimal = _CERO
    total_bonificacion_servicio_indexada: Decimal = _CERO
    total_bonificacion_recreacion_indexada: Decimal = _CERO
    total_prestaciones_indexadas: Decimal = _CERO
    total_aportes_salud: Decimal = _CERO
    total_aportes_pension: Decimal = _CERO
    gran_total: Decimal = _CERO
    pension_por_calculo_actuarial: bool = False


def liquidar_contrato_realidad_publico(
    filas: Sequence[AnioContratoRealidadPublico],
    anio_final: int,
    dias_vacaciones: Decimal,
    porcentaje_bonificacion_servicio: Decimal | None = None,
    calculo_actuarial_pension: ReservaActuarial | Decimal | None = None,
    tope_decreto_0320: Decimal | None = None,
    *,
    ipc_cierre: Callable[[int], Decimal] | None = None,
    pct_salud_total: Callable[[int], Decimal] | None = None,
    pct_pension_total: Callable[[int], Decimal] | None = None,
) -> LiquidacionContratoRealidadPublico:
    """Plantilla L8 (sector publico), por fila (H = salario mensual, F =
    dias, G = meses completos, I/K = auxilios de transporte/alimentacion,
    GR = gastos de representacion, f = factor IPC, D = `dias_vacaciones`):

    - Y bonificacion por servicio = (H+GR) x pct/100 / 12 x G, con pct de
      `porcentaje_bonificacion_por_servicio` (Decreto 0320 desde 2026; antes,
      `porcentaje_bonificacion_servicio`). Con GR = 0 es la formula de L8.
    - Q prima de servicio = (H+Y)/12 x G/2
    - W prima de vacaciones = ((Q+Y)/12 + (H+I+K))/30 x 15 x F/360
    - S prima de navidad = ((Q+Y+W)/12 + H)/12 x G
    - N cesantia = ((Q+S+W+Y)/12 + H)/360 x F; P intereses = N x f x 12 %/360 x F
    - U vacacion = ((Q+Y)/12 + (H+I+K))/30 x D x F/360
    - AA bonificacion especial de recreacion = H/30 x 2
    - auxilios indexados = I x f, K x f
    - M salarios = H/30 x F; aportes = M x f x porcentaje TOTAL
    Cada concepto se indexa x f. Gran total = prestaciones indexadas +
    aportes (L8 no suma salarios). Calculo actuarial: igual que el privado.
    """
    _validar_comunes(filas, anio_final)
    ipc_cierre = ipc_cierre or _ipc_cierre_parametro
    pct_salud = pct_salud_total or _pct_parametro("SS_SALUD_PCT")
    pct_pension = pct_pension_total or _pct_parametro("SS_PENSION_PCT")
    actuarial = _monto_calculo_actuarial(calculo_actuarial_pension)
    dias_vac = _no_negativo(dias_vacaciones, "Los dias de vacaciones")

    resultado: list[FilaContratoRealidadPublico] = []
    for e in filas:
        h = _no_negativo(e.salario_mensual, "El salario")
        dias = _no_negativo(e.dias, "El numero de dias")
        meses = _no_negativo(e.meses, "El numero de meses")
        if dias > 360 or meses > 12:
            raise ValueError("Un año no puede tener mas de 360 dias ni mas de 12 meses.")
        aux_t = _no_negativo(e.auxilio_transporte, "El auxilio de transporte")
        aux_a = _no_negativo(e.auxilio_alimentacion, "El auxilio de alimentacion")
        gr = _no_negativo(e.gastos_representacion, "Los gastos de representacion")
        f = _factor_ipc(e.anio, anio_final, ipc_cierre)

        pct_bon = porcentaje_bonificacion_por_servicio(
            SectorContratoRealidad.PUBLICO,
            e.anio,
            h,
            gr,
            porcentaje_usuario=porcentaje_bonificacion_servicio,
            tope_decreto_0320=tope_decreto_0320,
        )
        y = (h + gr) * pct_bon / _CIEN / 12 * meses
        q = (h + y) / 12 * meses / 2
        base_vac = (q + y) / 12 + (h + aux_t + aux_a)
        w = base_vac / 30 * 15 * dias / 360
        s = ((q + y + w) / 12 + h) / 12 * meses
        n = ((q + s + w + y) / 12 + h) / 360 * dias
        u = base_vac / 30 * dias_vac * dias / 360
        aa = h / 30 * 2
        m = h / 30 * dias
        base_aportes = m * f

        resultado.append(
            FilaContratoRealidadPublico(
                anio=e.anio,
                factor_ipc=f,
                auxilio_transporte_indexado=Rounding.money(aux_t * f),
                auxilio_alimentacion_indexado=Rounding.money(aux_a * f),
                total_salarios=Rounding.money(m),
                cesantias=Rounding.money(n),
                cesantias_indexadas=Rounding.money(n * f),
                intereses_cesantias=Rounding.money(n * f * Decimal("0.12") / 360 * dias),
                prima_servicio=Rounding.money(q),
                prima_servicio_indexada=Rounding.money(q * f),
                prima_navidad=Rounding.money(s),
                prima_navidad_indexada=Rounding.money(s * f),
                vacaciones=Rounding.money(u),
                vacaciones_indexadas=Rounding.money(u * f),
                prima_vacaciones=Rounding.money(w),
                prima_vacaciones_indexada=Rounding.money(w * f),
                porcentaje_bonificacion_servicio=pct_bon,
                bonificacion_servicio=Rounding.money(y),
                bonificacion_servicio_indexada=Rounding.money(y * f),
                bonificacion_recreacion=Rounding.money(aa),
                bonificacion_recreacion_indexada=Rounding.money(aa * f),
                aporte_salud=Rounding.money(base_aportes * pct_salud(e.anio)),
                aporte_pension=Rounding.money(
                    _CERO if actuarial is not None else base_aportes * pct_pension(e.anio)
                ),
            )
        )

    totales = {
        "total_auxilio_transporte_indexado": _suma(
            r.auxilio_transporte_indexado for r in resultado
        ),
        "total_auxilio_alimentacion_indexado": _suma(
            r.auxilio_alimentacion_indexado for r in resultado
        ),
        "total_cesantias_indexadas": _suma(r.cesantias_indexadas for r in resultado),
        "total_intereses_cesantias": _suma(r.intereses_cesantias for r in resultado),
        "total_prima_servicio_indexada": _suma(r.prima_servicio_indexada for r in resultado),
        "total_prima_navidad_indexada": _suma(r.prima_navidad_indexada for r in resultado),
        "total_vacaciones_indexadas": _suma(r.vacaciones_indexadas for r in resultado),
        "total_prima_vacaciones_indexada": _suma(r.prima_vacaciones_indexada for r in resultado),
        "total_bonificacion_servicio_indexada": _suma(
            r.bonificacion_servicio_indexada for r in resultado
        ),
        "total_bonificacion_recreacion_indexada": _suma(
            r.bonificacion_recreacion_indexada for r in resultado
        ),
    }
    total_prest = sum(totales.values(), Rounding.money(_CERO))
    total_salud = _suma(r.aporte_salud for r in resultado)
    total_pension = (
        actuarial if actuarial is not None else _suma(r.aporte_pension for r in resultado)
    )
    return LiquidacionContratoRealidadPublico(
        filas=resultado,
        **totales,
        total_prestaciones_indexadas=total_prest,
        total_aportes_salud=total_salud,
        total_aportes_pension=total_pension,
        gran_total=total_prest + total_salud + total_pension,
        pension_por_calculo_actuarial=actuarial is not None,
    )
