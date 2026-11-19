"""Motor de calculo actuarial del Decreto 1296 de 2022 (Sprints 86/87).

Comun al bono pensional Tipo A (Sprint 86) y al calculo actuarial de
cotizaciones omisas (Sprint 87). Formulas y datos de la respuesta del
despacho del 16/11/2026 (`docs/Preguntas-Para-Abogado-Respondidas.md`,
"Sprint 86/87 (seguimiento)"):

- Interpolacion por dias entre cumpleaños: `v0 = (d1*v2 + d2*v1)/(d1+d2)`
  (v1 = valor a la edad cumplida, v2 = a la edad siguiente, d1 = dias desde
  el ultimo cumpleaños, d2 = dias hasta el siguiente). El despacho la dio
  para el SMN; para FAC1/FAC2 pidio "tablas parametrizadas con interpolacion
  lineal" sin regla propia, asi que se usa la misma regla por dias.
- FAC3 estandar: `((1.03^t) - 1) / ((1.03^(t+n)) - 1)`.
- FAC3 con tiempo previo: `[((1.03^t1)-1)/t1] / [((1.03^(t1+n))-1)/(t1+n)]`,
  con `t1 = t + tiempos previos`. `t` se redondea a 6 decimales.
- `VRA = [(FAC1*PR) + (FAC2*AR)] * FAC3`, `CA = 0.005*VRA`,
  `VR = VRA / 0.995`.
- `SR = SB * (SMN_FR / SMN_FC)`.
- Auxilio funerario AR: PR < 5 SMLV -> 5 SMLV; 5 <= PR <= 10 SMLV -> PR;
  PR > 10 SMLV -> 10 SMLV.
- DTF pensional anual `1.03 * (1 + INF_i/100)`, INF_i = variacion anual del
  IPC del año calendario inmediatamente anterior, prorrateada por dias.

Limites deliberados (no se adivinaron):
- PR (pension de referencia): la respuesta no dice como se obtiene, asi que
  se recibe como parametro. Tampoco se convierte aqui de fechas a años la
  `t`/`n` de FAC3 (la respuesta no da la base de dias): se reciben en años.
- Prorrateo de la DTF pensional: la respuesta solo dice "se prorratea segun
  los dias transcurridos". Se aplica como exponente (capitalizacion,
  coherente con la "capitalizacion anual" del Art. 7 Decreto 1887/1994):
  `DTF_i ^ (dias_en_el_año_i / dias_del_año_calendario_i)`, de modo que un
  año calendario completo da exactamente `DTF_i`.
- Solo se liquida desde el 01/01/1994 (plantillas P12/P14: "Liquida desde
  Enero de 1994, con la vigencia de la Ley 100").
- Edades fuera de 55-90 para FAC1/FAC2 o menores de 12 para el SMN: error
  explicito, sin extrapolar.
- Nacidos un 29 de febrero: en años no bisiestos el cumpleaños se toma el
  28 de febrero (`CalendarUtils.safe_create_date`).

Sin conectar a la UI ni a ningun AreaStrategy todavia.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from enum import Enum

from app.engine.indexation.historical_index import _IPC_VARIACION_ANUAL
from app.engine.labor.tablas_actuariales import (
    EDAD_MAXIMA_FAC,
    EDAD_MINIMA_FAC,
    EDAD_MINIMA_SMN,
    EDAD_TOPE_SMN,
    FAC1_FAC2_POR_EDAD,
    SALARIO_MEDIO_NACIONAL_POR_EDAD,
)
from app.engine.math.rounding import Rounding
from app.engine.time.calendar import CalendarUtils

TASA_REAL = Decimal("1.03")
COMISION_ADMINISTRACION = Decimal("0.005")
FECHA_INICIO_DTF_PENSIONAL = date(1994, 1, 1)
_SEIS_DECIMALES = Decimal("0.000001")


class Sexo(Enum):
    HOMBRE = "hombre"
    MUJER = "mujer"


@dataclass(frozen=True)
class ReservaActuarial:
    vra: Decimal  # Valor de la Reserva Actuarial
    ca: Decimal  # Comision de Administracion (0,5 % del VRA)
    vr: Decimal  # Valor final de la Reserva = VRA / 0,995


# --------------------------------------------------------------------------
# Interpolacion por dias entre cumpleaños
# --------------------------------------------------------------------------


def interpolar_por_dias(v1: Decimal, v2: Decimal, d1: int, d2: int) -> Decimal:
    """`v0 = (d1*v2 + d2*v1) / (d1+d2)` (regla del despacho)."""
    if d1 < 0 or d2 <= 0:
        raise ValueError("d1 debe ser >= 0 y d2 > 0.")
    return (Decimal(d1) * v2 + Decimal(d2) * v1) / Decimal(d1 + d2)


def _cumpleanos(nacimiento: date, anio: int) -> date:
    return CalendarUtils.safe_create_date(anio, nacimiento.month, nacimiento.day)


def _edad_y_dias(nacimiento: date, fecha: date) -> tuple[int, int, int]:
    """(edad cumplida, d1 = dias desde el ultimo cumpleaños, d2 = dias
    hasta el siguiente)."""
    if fecha < nacimiento:
        raise ValueError("La fecha de calculo no puede ser anterior al nacimiento.")
    ultimo = _cumpleanos(nacimiento, fecha.year)
    if ultimo > fecha:
        ultimo = _cumpleanos(nacimiento, fecha.year - 1)
    siguiente = _cumpleanos(nacimiento, ultimo.year + 1)
    return ultimo.year - nacimiento.year, (fecha - ultimo).days, (siguiente - fecha).days


def factores_fac1_fac2(
    fecha_nacimiento: date, fecha_calculo: date, sexo: Sexo
) -> tuple[Decimal, Decimal]:
    """FAC1 y FAC2 (Tabla 2) interpolados por dias a `fecha_calculo`.

    Solo edades 55-90: fuera de ese rango (o 90 años y algun dia, que
    necesitaria la edad 91) se lanza ValueError -- no se extrapola."""
    edad, d1, d2 = _edad_y_dias(fecha_nacimiento, fecha_calculo)
    edad_siguiente = edad + 1 if d1 > 0 else edad
    if edad < EDAD_MINIMA_FAC or edad_siguiente > EDAD_MAXIMA_FAC:
        raise ValueError(
            f"La Tabla 2 (FAC1/FAC2) solo cubre edades {EDAD_MINIMA_FAC}-{EDAD_MAXIMA_FAC}; "
            f"la edad a {fecha_calculo.isoformat()} es {edad} años y {d1} dias."
        )
    actual = FAC1_FAC2_POR_EDAD[edad]
    if d1 == 0:
        if sexo is Sexo.HOMBRE:
            return actual.fac1_hombres, actual.fac2_hombres
        return actual.fac1_mujeres, actual.fac2_mujeres
    siguiente = FAC1_FAC2_POR_EDAD[edad_siguiente]
    if sexo is Sexo.HOMBRE:
        return (
            interpolar_por_dias(actual.fac1_hombres, siguiente.fac1_hombres, d1, d2),
            interpolar_por_dias(actual.fac2_hombres, siguiente.fac2_hombres, d1, d2),
        )
    return (
        interpolar_por_dias(actual.fac1_mujeres, siguiente.fac1_mujeres, d1, d2),
        interpolar_por_dias(actual.fac2_mujeres, siguiente.fac2_mujeres, d1, d2),
    )


def _smn_edad_entera(edad: int) -> Decimal:
    return SALARIO_MEDIO_NACIONAL_POR_EDAD[min(edad, EDAD_TOPE_SMN)]


def salario_medio_nacional(fecha_nacimiento: date, fecha_calculo: date) -> Decimal:
    """SMN (Tabla 1, indice base 1 a los 12 años) interpolado por dias a
    `fecha_calculo`. Desde los 71 años aplica la fila "71+" (constante).
    Menores de 12 años: ValueError."""
    edad, d1, d2 = _edad_y_dias(fecha_nacimiento, fecha_calculo)
    if edad < EDAD_MINIMA_SMN:
        raise ValueError(
            f"La Tabla 1 (SMN) empieza a los {EDAD_MINIMA_SMN} años; la edad a "
            f"{fecha_calculo.isoformat()} es {edad}."
        )
    v1 = _smn_edad_entera(edad)
    if d1 == 0:
        return v1
    return interpolar_por_dias(v1, _smn_edad_entera(edad + 1), d1, d2)


# --------------------------------------------------------------------------
# FAC3
# --------------------------------------------------------------------------


def calcular_fac3_estandar(t: Decimal, n: Decimal) -> Decimal:
    """Variante 1 (sin tiempos previos al periodo omitido):
    `((1.03^t) - 1) / ((1.03^(t+n)) - 1)`, con `t` (años a convalidar a la
    fecha de corte) redondeado a 6 decimales y `n` (años desde la fecha de
    corte hasta la edad de referencia)."""
    t = Rounding.six(t)
    n = Decimal(str(n))
    if t < 0 or n < 0:
        raise ValueError("t y n no pueden ser negativos.")
    if t + n == 0:
        raise ValueError("t + n debe ser mayor que cero.")
    return (TASA_REAL**t - 1) / (TASA_REAL ** (t + n) - 1)


def calcular_fac3_con_tiempo_previo(t1: Decimal, n: Decimal) -> Decimal:
    """Variante 2 (con tiempos cotizados u omitidos previos):
    `[((1.03^t1) - 1) / t1] / [((1.03^(t1+n)) - 1) / (t1+n)]`, con
    `t1 = t + tiempos previos` (en años)."""
    t1 = Decimal(str(t1))
    n = Decimal(str(n))
    if t1 <= 0:
        raise ValueError("t1 debe ser mayor que cero.")
    if n < 0:
        raise ValueError("n no puede ser negativo.")
    total = t1 + n
    return ((TASA_REAL**t1 - 1) / t1) / ((TASA_REAL**total - 1) / total)


def calcular_fac3(t: Decimal, n: Decimal, tiempos_previos: Decimal = Decimal("0")) -> Decimal:
    """Elige la variante de FAC3 segun existan tiempos previos (despacho,
    16/11/2026): sin previos -> estandar; con previos -> variante 2 con
    `t1 = t (redondeado a 6 decimales) + tiempos_previos`."""
    tiempos_previos = Decimal(str(tiempos_previos))
    if tiempos_previos < 0:
        raise ValueError("Los tiempos previos no pueden ser negativos.")
    if tiempos_previos == 0:
        return calcular_fac3_estandar(t, n)
    return calcular_fac3_con_tiempo_previo(Rounding.six(t) + tiempos_previos, n)


# --------------------------------------------------------------------------
# Salario y auxilio funerario de referencia, reserva actuarial
# --------------------------------------------------------------------------


def calcular_salario_referencia(sb: Decimal, smn_fr: Decimal, smn_fc: Decimal) -> Decimal:
    """`SR = SB * (SMN_FR / SMN_FC)`: SB = salario base actualizado a la fecha
    de corte; SMN a la edad de referencia (FR) y a la de la fecha de corte (FC)."""
    sb, smn_fr, smn_fc = (Decimal(str(x)) for x in (sb, smn_fr, smn_fc))
    if sb < 0:
        raise ValueError("El salario base no puede ser negativo.")
    if smn_fr <= 0 or smn_fc <= 0:
        raise ValueError("Los salarios medios nacionales deben ser positivos.")
    return Rounding.money(sb * smn_fr / smn_fc)


def calcular_auxilio_funerario_referencia(pr: Decimal, smlv: Decimal) -> Decimal:
    """AR segun PR: < 5 SMLV -> 5 SMLV; entre 5 y 10 SMLV (inclusive) -> PR;
    > 10 SMLV -> 10 SMLV. `smlv` es el salario minimo mensual aplicable."""
    pr, smlv = Decimal(str(pr)), Decimal(str(smlv))
    if pr < 0:
        raise ValueError("La pension de referencia no puede ser negativa.")
    if smlv <= 0:
        raise ValueError("El SMLV debe ser positivo.")
    minimo, maximo = 5 * smlv, 10 * smlv
    return Rounding.money(min(max(pr, minimo), maximo))


def calcular_reserva_actuarial(
    fac1: Decimal, fac2: Decimal, pr: Decimal, ar: Decimal, fac3: Decimal
) -> ReservaActuarial:
    """`VRA = [(FAC1*PR) + (FAC2*AR)] * FAC3`; `CA = 0.005*VRA`;
    `VR = VRA / 0.995`. Se calcula todo sin redondear y solo se redondea a
    centavos cada valor en pesos del resultado."""
    fac1, fac2, pr, ar, fac3 = (Decimal(str(x)) for x in (fac1, fac2, pr, ar, fac3))
    if pr < 0 or ar < 0:
        raise ValueError("PR y AR no pueden ser negativos.")
    if fac1 < 0 or fac2 < 0 or fac3 < 0:
        raise ValueError("Los factores actuariales no pueden ser negativos.")
    vra = (fac1 * pr + fac2 * ar) * fac3
    return ReservaActuarial(
        vra=Rounding.money(vra),
        ca=Rounding.money(COMISION_ADMINISTRACION * vra),
        vr=Rounding.money(vra / (1 - COMISION_ADMINISTRACION)),
    )


# --------------------------------------------------------------------------
# Actualizacion con DTF pensional
# --------------------------------------------------------------------------


def factor_dtf_pensional(
    fecha_inicial: date,
    fecha_final: date,
    inflacion_anual: Mapping[int, Decimal] | None = None,
) -> Decimal:
    """Factor acumulado de DTF pensional entre dos fechas.

    Para cada año calendario `i` tocado por el periodo:
    `(1.03 * (1 + INF_{i-1}/100)) ^ (dias_i / dias_del_año_i)`, donde
    `INF_{i-1}` es la variacion anual del IPC del año anterior y `dias_i` los
    dias del periodo dentro de ese año (`fecha_final - fecha_inicial`, sin
    contar el dia inicial). `inflacion_anual` es {año: variacion %}; por
    defecto, la serie de referencia del sistema (`_IPC_VARIACION_ANUAL`,
    1967-2025, en historical_index). Si falta la variacion de algun año
    necesario se lanza ValueError."""
    if fecha_inicial < FECHA_INICIO_DTF_PENSIONAL:
        raise ValueError("La DTF pensional solo se liquida desde el 01/01/1994.")
    if fecha_final < fecha_inicial:
        raise ValueError("La fecha final no puede ser anterior a la inicial.")
    serie = _IPC_VARIACION_ANUAL if inflacion_anual is None else inflacion_anual

    factor = Decimal("1")
    cursor = fecha_inicial
    while cursor < fecha_final:
        anio = cursor.year
        fin_tramo = min(date(anio + 1, 1, 1), fecha_final)
        if anio - 1 not in serie:
            raise ValueError(
                f"No hay variacion anual del IPC para {anio - 1}, necesaria para la "
                f"DTF pensional de {anio}."
            )
        dtf = TASA_REAL * (1 + Decimal(str(serie[anio - 1])) / 100)
        dias_tramo = (fin_tramo - cursor).days
        dias_anio = (date(anio + 1, 1, 1) - date(anio, 1, 1)).days
        factor *= dtf ** (Decimal(dias_tramo) / Decimal(dias_anio))
        cursor = fin_tramo
    return factor


def actualizar_reserva_dtf_pensional(
    valor: Decimal,
    fecha_corte: date,
    fecha_pago: date,
    inflacion_anual: Mapping[int, Decimal] | None = None,
) -> Decimal:
    """Reserva a la fecha de pago = reserva a la fecha de corte x factor de
    DTF pensional entre ambas fechas (ver `factor_dtf_pensional`)."""
    valor = Decimal(str(valor))
    if valor < 0:
        raise ValueError("El valor de la reserva no puede ser negativo.")
    factor = factor_dtf_pensional(fecha_corte, fecha_pago, inflacion_anual)
    return (valor * factor).quantize(Rounding.MONEY, rounding=ROUND_HALF_UP)
