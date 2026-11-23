from datetime import date
from decimal import Decimal
from enum import StrEnum

from app.engine.math.rounding import Rounding

FECHA_CORTE_JORNADA_NOCTURNA_LEY_2466 = date(2025, 12, 25)
PORCENTAJE_RECARGO_NOCTURNO = Decimal("35")

LIMITE_HORAS_EXTRA_DIARIAS_LEY_2466 = Decimal("2")
LIMITE_HORAS_EXTRA_SEMANALES_LEY_2466 = Decimal("12")

# Fechas de inicio de los tramos de transicion de la Ley 2466 de 2025 para el
# recargo dominical/festivo (respuesta del despacho, Sprint 95, 22/08/2026).
FECHA_INICIO_TRAMO_1_LEY_2466 = date(2025, 7, 1)
FECHA_INICIO_TRAMO_2_LEY_2466 = date(2026, 7, 1)
FECHA_INICIO_TRAMO_3_LEY_2466 = date(2027, 7, 1)

_TRAMOS_RECARGO_DOMINICAL_FESTIVO = (
    (FECHA_INICIO_TRAMO_1_LEY_2466, Decimal("75")),
    (FECHA_INICIO_TRAMO_2_LEY_2466, Decimal("80")),
    (FECHA_INICIO_TRAMO_3_LEY_2466, Decimal("90")),
)
_PORCENTAJE_RECARGO_DOMINICAL_FESTIVO_FINAL = Decimal("100")


class ConceptoHoraExtra(StrEnum):
    """Los 4 conceptos "Horas Extras..." de la plantilla del despacho
    `L3.HORASEXTRASYRECARGOS.md`."""

    HED = "HED"  # Hora extra diurna (ordinaria)
    HEN = "HEN"  # Hora extra nocturna (ordinaria)
    HEFD = "HEFD"  # Hora extra festiva/dominical diurna
    HEFN = "HEFN"  # Hora extra festiva/dominical nocturna


# Factores (valor hora x factor) confirmados por el despacho (Sprint 95,
# seguimiento): HED 1.25 y HEN 1.75 sin vigencia por fecha.
_FACTORES_HORA_EXTRA_ORDINARIA = {
    ConceptoHoraExtra.HED: Decimal("1.25"),
    ConceptoHoraExtra.HEN: Decimal("1.75"),
}

# HEFD/HEFN incorporan la tabla progresiva del recargo dominical/festivo:
# (fecha de inicio del tramo, factor HEFD, factor HEFN), en orden ascendente.
_TRAMOS_FACTOR_HORA_EXTRA_FESTIVA = (
    (FECHA_INICIO_TRAMO_1_LEY_2466, Decimal("2.05"), Decimal("2.55")),  # festivo 80%
    (FECHA_INICIO_TRAMO_2_LEY_2466, Decimal("2.15"), Decimal("2.65")),  # festivo 90%
    (FECHA_INICIO_TRAMO_3_LEY_2466, Decimal("2.25"), Decimal("2.75")),  # festivo 100%
)


class HoraExtraFestivaSinFactorConfirmadoError(ValueError):
    """HEFD/HEFN causadas antes del 01/07/2025: la respuesta del despacho
    (Sprint 95, seguimiento) solo fija sus factores desde el Tramo 1 de la Ley
    2466/2025. Para esas horas se conserva el comportamiento previo: el
    llamador debe pasar el porcentaje explicitamente a `calcular_hora_extra`."""


class LimiteHorasExtraLey2466Error(ValueError):
    """Las horas extra superan el tope legal de la Ley 2466 de 2025 (2
    horas/dia o 12 horas/semana) -- respuesta del despacho, Sprint 95,
    22/08/2026."""


def hora_inicio_jornada_nocturna(fecha_hecho: date) -> int:
    """Hora (0-23) en que inicia la jornada nocturna. La Ley 2466 de 2025
    adelanta el inicio de las 21:00 a las 19:00 con vigencia inmediata desde
    una sola fecha de corte (a diferencia del recargo dominical/festivo, que
    transiciona progresivamente) -- respuesta del despacho, Sprint 95,
    22/08/2026. El porcentaje del recargo nocturno (35%) no cambia, solo el
    horario -- ver `PORCENTAJE_RECARGO_NOCTURNO`."""
    if fecha_hecho >= FECHA_CORTE_JORNADA_NOCTURNA_LEY_2466:
        return 19
    return 21


def porcentaje_recargo_dominical_festivo(fecha_hecho: date) -> Decimal:
    """Porcentaje del recargo dominical/festivo vigente en `fecha_hecho`,
    segun la tabla de transicion progresiva de la Ley 2466 de 2025 (respuesta
    del despacho, Sprint 95, 22/08/2026): 75% hasta 30/06/2025, 80% desde
    01/07/2025, 90% desde 01/07/2026, 100% desde 01/07/2027 en adelante."""
    for fecha_corte, porcentaje in _TRAMOS_RECARGO_DOMINICAL_FESTIVO:
        if fecha_hecho < fecha_corte:
            return porcentaje
    return _PORCENTAJE_RECARGO_DOMINICAL_FESTIVO_FINAL


def validar_limite_horas_extra_ley_2466(
    horas_extra_diarias: Decimal, horas_extra_semanales: Decimal
) -> None:
    """Los topes nuevos de la Ley 2466 de 2025 (respuesta del despacho,
    Sprint 95, 22/08/2026): maximo 2 horas extra diarias y 12 semanales.
    Lanza `LimiteHorasExtraLey2466Error` en vez de liquidar un exceso no
    permitido legalmente."""
    if (
        horas_extra_diarias > LIMITE_HORAS_EXTRA_DIARIAS_LEY_2466
        or horas_extra_semanales > LIMITE_HORAS_EXTRA_SEMANALES_LEY_2466
    ):
        raise LimiteHorasExtraLey2466Error(
            f"Supera el limite legal de la Ley 2466 de 2025: {horas_extra_diarias} horas "
            f"extra diarias (maximo {LIMITE_HORAS_EXTRA_DIARIAS_LEY_2466}) o "
            f"{horas_extra_semanales} horas extra semanales (maximo "
            f"{LIMITE_HORAS_EXTRA_SEMANALES_LEY_2466})."
        )


def _validar_comunes(numero_horas, valor_hora_ordinaria, porcentaje):
    if numero_horas <= 0:
        raise ValueError("El numero de horas debe ser mayor a cero.")
    if valor_hora_ordinaria < 0:
        raise ValueError("El valor de la hora ordinaria no puede ser negativo.")
    if porcentaje < 0:
        raise ValueError("El porcentaje no puede ser negativo.")


def calcular_hora_extra(numero_horas, valor_hora_ordinaria, porcentaje) -> Decimal:
    """Liquida una hora extra (tiempo trabajado por fuera de la jornada
    ordinaria, no remunerado por ningun otro concepto): se paga la hora
    completa mas el recargo, `horas x valor_hora x (1 + porcentaje/100)`.

    Aplica a los 4 conceptos "Horas Extras..." de la plantilla del despacho
    `L3.HORASEXTRASYRECARGOS.md` (diurnas/nocturnas, ordinarias/festivas).

    Recibe el porcentaje explicito. Para resolver el factor legal vigente
    segun la fecha de causacion (HED/HEN y HEFD/HEFN por tramo de la Ley
    2466/2025) usar `liquidar_hora_extra` / `factor_hora_extra`. Esta funcion
    sigue siendo la via para HEFD/HEFN causadas antes del 01/07/2025, cuyo
    factor no fijo el despacho.
    """
    numero_horas = Decimal(str(numero_horas))
    valor_hora_ordinaria = Decimal(str(valor_hora_ordinaria))
    porcentaje = Decimal(str(porcentaje))
    _validar_comunes(numero_horas, valor_hora_ordinaria, porcentaje)

    factor = Decimal("1") + porcentaje / Decimal("100")
    return Rounding.money(numero_horas * valor_hora_ordinaria * factor)


def calcular_recargo(numero_horas, valor_hora_ordinaria, porcentaje) -> Decimal:
    """Liquida un recargo (horas dentro de la jornada ordinaria que ya se
    remuneraron como salario base, pero en un horario/dia que exige un pago
    adicional): solo el porcentaje adicional, `horas x valor_hora x
    (porcentaje/100)`, sin sumar de nuevo el valor de la hora base.

    Aplica a los 3 conceptos "Recargo..." de la misma plantilla `L3`
    (nocturno, festivo diurno, festivo nocturno). A diferencia de
    `calcular_hora_extra`, estos 3 porcentajes SI estan confirmados por el
    despacho (Sprint 95, 22/08/2026): recargo nocturno constante
    (`PORCENTAJE_RECARGO_NOCTURNO`) y recargo festivo diurno/nocturno con
    vigencia por fecha (`porcentaje_recargo_dominical_festivo`) -- el
    llamador debe resolver el porcentaje vigente antes de invocar esta
    funcion, que sigue sin cablear a `parametro_service` ni `LaboralStrategy`.
    """
    numero_horas = Decimal(str(numero_horas))
    valor_hora_ordinaria = Decimal(str(valor_hora_ordinaria))
    porcentaje = Decimal(str(porcentaje))
    _validar_comunes(numero_horas, valor_hora_ordinaria, porcentaje)

    return Rounding.money(numero_horas * valor_hora_ordinaria * porcentaje / Decimal("100"))


def factor_hora_extra(concepto, fecha_causacion: date) -> Decimal:
    """Factor (valor hora x factor) del concepto de hora extra vigente en
    `fecha_causacion`, segun la respuesta del despacho (Sprint 95,
    seguimiento): las horas extra festivas SI incorporan la tabla progresiva
    del recargo dominical/festivo de la Ley 2466/2025.

    - HED: 1.25 (25%) y HEN: 1.75 (75%), en cualquier fecha.
    - HEFD / HEFN:
      Tramo 1 (01/07/2025 - 30/06/2026, festivo 80%): 2.05 / 2.55.
      Tramo 2 (01/07/2026 - 30/06/2027, festivo 90%): 2.15 / 2.65.
      Tramo 3 (desde 01/07/2027, festivo 100%): 2.25 / 2.75.

    HEFD/HEFN causadas antes del 01/07/2025 lanzan
    `HoraExtraFestivaSinFactorConfirmadoError` (la respuesta no fija ese
    tramo; ver docstring de la excepcion). Acepta el concepto como
    `ConceptoHoraExtra` o como su codigo en texto ("HEFD").
    """
    try:
        concepto = ConceptoHoraExtra(concepto)
    except ValueError as exc:
        raise ValueError(f"Concepto de hora extra desconocido: {concepto!r}.") from exc

    if concepto in _FACTORES_HORA_EXTRA_ORDINARIA:
        return _FACTORES_HORA_EXTRA_ORDINARIA[concepto]

    factor = None
    for fecha_inicio, factor_hefd, factor_hefn in _TRAMOS_FACTOR_HORA_EXTRA_FESTIVA:
        if fecha_causacion >= fecha_inicio:
            factor = factor_hefd if concepto is ConceptoHoraExtra.HEFD else factor_hefn
    if factor is None:
        raise HoraExtraFestivaSinFactorConfirmadoError(
            f"No hay factor confirmado para {concepto.value} causada el "
            f"{fecha_causacion:%d/%m/%Y} (antes del "
            f"{FECHA_INICIO_TRAMO_1_LEY_2466:%d/%m/%Y}). Indique el porcentaje "
            "explicitamente con calcular_hora_extra."
        )
    return factor


def liquidar_hora_extra(
    concepto, numero_horas, valor_hora_ordinaria, fecha_causacion: date
) -> Decimal:
    """Liquida horas extra con el factor legal vigente en `fecha_causacion`:
    `horas x valor_hora x factor_hora_extra(concepto, fecha_causacion)`,
    redondeado a centavos. Ver `factor_hora_extra` para la tabla de factores
    y el tratamiento de HEFD/HEFN anteriores al 01/07/2025."""
    numero_horas = Decimal(str(numero_horas))
    valor_hora_ordinaria = Decimal(str(valor_hora_ordinaria))
    factor = factor_hora_extra(concepto, fecha_causacion)
    _validar_comunes(numero_horas, valor_hora_ordinaria, factor)

    return Rounding.money(numero_horas * valor_hora_ordinaria * factor)


def requiere_porcentaje_manual(concepto, fecha_causacion: date) -> bool:
    """True si el motor no tiene factor confirmado por el despacho para
    `concepto` en `fecha_causacion` (hoy: HEFD/HEFN causadas antes del
    01/07/2025) y por tanto el usuario debe digitar el porcentaje. La UI
    (`app/views/horas_extra_laborales.py`) lo usa para pedir ese dato solo
    cuando hace falta."""
    try:
        factor_hora_extra(concepto, fecha_causacion)
    except HoraExtraFestivaSinFactorConfirmadoError:
        return True
    return False


def liquidar_hora_extra_con_porcentaje_manual(
    concepto,
    numero_horas,
    valor_hora_ordinaria,
    fecha_causacion: date,
    porcentaje_manual=None,
) -> tuple[Decimal, Decimal]:
    """Liquida una fila de horas extra registrada en una liquidacion Laboral
    (Sprint 95, conexion a la UI) y retorna `(monto, factor_aplicado)`.

    - Si el motor tiene factor confirmado para la fecha, se usa ese
      (`liquidar_hora_extra`) y `porcentaje_manual` se ignora: el factor legal
      lo fijo el despacho, no el usuario.
    - Si no (HEFD/HEFN antes del 01/07/2025), se usa el porcentaje digitado
      con `calcular_hora_extra` (factor = 1 + porcentaje/100). Sin porcentaje
      digitado lanza `HoraExtraFestivaSinFactorConfirmadoError`.
    """
    if not requiere_porcentaje_manual(concepto, fecha_causacion):
        factor = factor_hora_extra(concepto, fecha_causacion)
        monto = liquidar_hora_extra(concepto, numero_horas, valor_hora_ordinaria, fecha_causacion)
        return monto, factor

    if porcentaje_manual is None:
        raise HoraExtraFestivaSinFactorConfirmadoError(
            f"No hay factor confirmado por el despacho para {ConceptoHoraExtra(concepto).value} "
            f"causada el {fecha_causacion:%d/%m/%Y} (antes del "
            f"{FECHA_INICIO_TRAMO_1_LEY_2466:%d/%m/%Y}, inicio del Tramo 1 de la Ley 2466 "
            "de 2025). Digite el porcentaje de la hora extra festiva."
        )
    porcentaje = Decimal(str(porcentaje_manual))
    monto = calcular_hora_extra(numero_horas, valor_hora_ordinaria, porcentaje)
    return monto, Decimal("1") + porcentaje / Decimal("100")
