from decimal import Decimal

from app.engine.math.rounding import Rounding


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

    Deliberadamente NO trae hardcodeados los porcentajes legales (HED 25%,
    HEN 75%, HEFD 100%, HEFN 150%) ni ninguna tabla de vigencia: la Ley 2466
    de 2025 los esta modificando progresivamente entre 2025 y 2027, y la
    tabla de transicion exacta sigue pendiente de confirmacion del despacho
    (ver docs/Pendientes.md, Sprint 95, y docs/Preguntas-Para-Abogado-Abiertas.md).
    Esta funcion solo formaliza, con tests, la formula aritmetica -- no
    esta cableada a ningun formulario, `parametro_service` ni `LaboralStrategy`.
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
    (nocturno, festivo diurno, festivo nocturno). Mismas salvedades que
    `calcular_hora_extra` sobre porcentajes/vigencia pendientes del Sprint 95.
    """
    numero_horas = Decimal(str(numero_horas))
    valor_hora_ordinaria = Decimal(str(valor_hora_ordinaria))
    porcentaje = Decimal(str(porcentaje))
    _validar_comunes(numero_horas, valor_hora_ordinaria, porcentaje)

    return Rounding.money(numero_horas * valor_hora_ordinaria * porcentaje / Decimal("100"))
