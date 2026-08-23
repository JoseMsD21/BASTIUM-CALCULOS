"""Formulas actuariales de lucro cesante (Sprint 97/98, respuesta del
despacho 22/08/2026): anualidad vencida (Consolidado, periodo pasado) y
anualidad anticipada (Futuro, periodo por venir), mas la interpolacion lineal
de expectativa de vida entre dos edades enteras de la tabla de mortalidad de
rentistas (Resolucion 1555 de 2010, Superfinanciera).

Funciones AISLADAS -- sin cablear a ningun AreaStrategy ni al modelo de
`Obligacion` todavia. El Sprint 97 (docs/Pendientes.md) pedia una decision de
arquitectura (septima area de derecho vs. submodo de Civil/Familia, y cuales
de las 6 variantes de reparto de beneficiario construir) que esta respuesta
del despacho NO contesto -- solo trajo las formulas matematicas. Tampoco trae
la tabla de mortalidad completa (el diccionario que aporto viene truncado con
"..." a la mitad para hombres_invalidos, y el sprint 98 advierte que ni la
version leida de las plantillas confirma si llega hasta la edad maxima
necesaria). Construir el motor completo (wiring, reparto por beneficiario,
tabla de mortalidad) sin resolver esos dos puntos arriesgaria un area nueva
mal disenada o una liquidacion real con datos de mortalidad incompletos -- se
documenta la formula, verificada con tests, y se deja sin conectar. Ver
docs/Preguntas-Para-Abogado-Abiertas.md, "Sprint 97 (seguimiento)".
"""

from decimal import Decimal

from app.engine.math.rounding import Rounding


def calcular_lucro_cesante_consolidado(
    renta_actualizada_mensual: Decimal, tasa_mensual: Decimal, n_meses: Decimal
) -> Decimal:
    """Lucro cesante consolidado (periodo pasado/vencido): formula de
    anualidad vencida `LCC = Ra * (((1+i)^n - 1) / i)` (respuesta del
    despacho, Sprint 97, 22/08/2026). `tasa_mensual` es la tasa mensual pura
    (fraccion, no porcentaje -- ej. 0.0048676 para el 6% EA del Art. 2232
    C.C., ver EffectiveRateConverter.annual_to_monthly). `n_meses` es el
    tiempo transcurrido en meses exactos (puede ser fraccionario)."""
    renta_actualizada_mensual = Decimal(str(renta_actualizada_mensual))
    tasa_mensual = Decimal(str(tasa_mensual))
    n_meses = Decimal(str(n_meses))

    if renta_actualizada_mensual < 0:
        raise ValueError("La renta actualizada mensual no puede ser negativa.")
    if tasa_mensual <= 0:
        raise ValueError("La tasa mensual debe ser mayor que cero.")
    if n_meses <= 0:
        raise ValueError("El numero de meses debe ser mayor que cero.")

    factor = ((Decimal("1") + tasa_mensual) ** n_meses - Decimal("1")) / tasa_mensual
    return Rounding.money(renta_actualizada_mensual * factor)


def calcular_lucro_cesante_futuro(
    renta_actualizada_mensual: Decimal, tasa_mensual: Decimal, n_meses: Decimal
) -> Decimal:
    """Lucro cesante futuro (periodo anticipado): formula de valor presente
    de anualidad anticipada `LCF = Ra * (((1+i)^n - 1) / (i*(1+i)^n))`
    (respuesta del despacho, Sprint 97, 22/08/2026). Mismos parametros que
    `calcular_lucro_cesante_consolidado`; `n_meses` normalmente proviene de
    `Expectativa_Vida_En_Anios_Segun_Tabla * 12` (ver
    `interpolar_expectativa_vida_rentista`)."""
    renta_actualizada_mensual = Decimal(str(renta_actualizada_mensual))
    tasa_mensual = Decimal(str(tasa_mensual))
    n_meses = Decimal(str(n_meses))

    if renta_actualizada_mensual < 0:
        raise ValueError("La renta actualizada mensual no puede ser negativa.")
    if tasa_mensual <= 0:
        raise ValueError("La tasa mensual debe ser mayor que cero.")
    if n_meses <= 0:
        raise ValueError("El numero de meses debe ser mayor que cero.")

    base = (Decimal("1") + tasa_mensual) ** n_meses
    factor = (base - Decimal("1")) / (tasa_mensual * base)
    return Rounding.money(renta_actualizada_mensual * factor)


def interpolar_expectativa_vida_rentista(
    tabla_expectativa_vida: dict, edad_anios: int, edad_meses: int = 0
) -> Decimal:
    """Interpola linealmente la expectativa de vida de la tabla de mortalidad
    de rentistas entre las dos edades enteras que la rodean, segun los meses
    cumplidos entre ellas -- respuesta del despacho (Sprint 97, 22/08/2026):
    "si la victima tiene 33 años y 7 meses, el sistema interpolara
    matematicamente entre la expectativa a los 33 y a los 34".

    `tabla_expectativa_vida` es un dict {edad_en_anios: expectativa_en_anios}
    -- deliberadamente un parametro, no una tabla hardcodeada: la tabla que
    aporto el despacho llego truncada/incompleta (ver docstring del modulo),
    asi que esta funcion exige que la tabla que reciba tenga las edades
    exactas que necesita, sin inventar valores para las que falten."""
    edad_anios = int(edad_anios)
    edad_meses = int(edad_meses)
    if not (0 <= edad_meses < 12):
        raise ValueError("edad_meses debe estar entre 0 y 11.")

    if edad_meses == 0:
        if edad_anios not in tabla_expectativa_vida:
            raise ValueError(
                f"La tabla de mortalidad no tiene expectativa de vida para la edad "
                f"{edad_anios} años."
            )
        return Decimal(str(tabla_expectativa_vida[edad_anios]))

    edad_siguiente = edad_anios + 1
    if edad_anios not in tabla_expectativa_vida or edad_siguiente not in tabla_expectativa_vida:
        raise ValueError(
            f"La tabla de mortalidad necesita las edades {edad_anios} y {edad_siguiente} "
            "completas para interpolar."
        )

    expectativa_actual = Decimal(str(tabla_expectativa_vida[edad_anios]))
    expectativa_siguiente = Decimal(str(tabla_expectativa_vida[edad_siguiente]))
    fraccion_anio = Decimal(edad_meses) / Decimal("12")
    return expectativa_actual + (expectativa_siguiente - expectativa_actual) * fraccion_anio
