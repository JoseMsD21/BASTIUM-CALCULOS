from datetime import date
from decimal import Decimal

from app.engine.math.rounding import Rounding

FECHA_CORTE_JORNADA_NOCTURNA_LEY_2466 = date(2025, 12, 25)
PORCENTAJE_RECARGO_NOCTURNO = Decimal("35")

LIMITE_HORAS_EXTRA_DIARIAS_LEY_2466 = Decimal("2")
LIMITE_HORAS_EXTRA_SEMANALES_LEY_2466 = Decimal("12")

_TRAMOS_RECARGO_DOMINICAL_FESTIVO = (
    (date(2025, 7, 1), Decimal("75")),
    (date(2026, 7, 1), Decimal("80")),
    (date(2027, 7, 1), Decimal("90")),
)
_PORCENTAJE_RECARGO_DOMINICAL_FESTIVO_FINAL = Decimal("100")


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

    Deliberadamente NO trae hardcodeados los porcentajes legales de los 4
    conceptos "Horas Extras..." (HED, HEN, HEFD, HEFN): la respuesta del
    despacho (Sprint 95, 22/08/2026) confirmo la vigencia del recargo
    nocturno y del recargo dominical/festivo (ver `hora_inicio_jornada_nocturna`/
    `porcentaje_recargo_dominical_festivo`), pero no restablecio los
    porcentajes especificos de estos 4 conceptos combinados (extra + festivo)
    -- sigue pendiente en docs/Preguntas-Para-Abogado-Abiertas.md, "Sprint 95
    (seguimiento)". Esta funcion solo formaliza, con tests, la formula
    aritmetica -- no esta cableada a ningun formulario, `parametro_service`
    ni `LaboralStrategy`.
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
