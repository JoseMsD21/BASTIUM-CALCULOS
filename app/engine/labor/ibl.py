from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from app.engine.indexation.historical_index import get_ipc_interpolado_for_date
from app.engine.indexation.ipc import IPCIndexation
from app.engine.math.rounding import Rounding


def calcular_ibl(
    historial_salarios: list[tuple[date, Decimal]],
    fecha_calculo: date,
) -> Decimal:
    """Promedio de los salarios cotizados, cada uno indexado por IPC desde su
    fecha hasta fecha_calculo (PDF pag. 52). El historial ya debe venir acotado
    a los ultimos 10 anios cotizados -- esta funcion no filtra por fecha, solo
    indexa y promedia lo que reciba."""
    if not historial_salarios:
        raise ValueError("El historial de salarios no puede estar vacio.")

    indice_final = get_ipc_interpolado_for_date(fecha_calculo)
    total = Decimal("0.00")
    for fecha, salario in historial_salarios:
        indice_inicial = get_ipc_interpolado_for_date(fecha)
        total += salario + IPCIndexation.calculate(salario, indice_inicial, indice_final)

    return Rounding.money(total / len(historial_salarios))


# Semanas minimas de cotizacion exigidas por año de causacion (Ley 797 de 2003, art. 9,
# que modifico el art. 33 Ley 100/1993): 1000 semanas base, +50 en 2005, +25 cada año desde
# 2006 hasta llegar a 1300 en 2015 -- NO una cifra fija de 1300 para cualquier año, como
# tenia el codigo antes de esta correccion (Sprint 17, respuesta del despacho,
# docs/Preguntas-Para-Abogado-Respondidas.md: caso de prueba 2006 exige 1075 semanas, no 1300).
_SEMANAS_MINIMAS_POR_ANIO: dict[int, int] = {
    2005: 1050,
    2006: 1075,
    2007: 1100,
    2008: 1125,
    2009: 1150,
    2010: 1175,
    2011: 1200,
    2012: 1225,
    2013: 1250,
    2014: 1275,
    2015: 1300,
}


def semanas_minimas_requeridas(anio_causacion: int) -> int:
    """Semanas minimas exigidas para pensionarse en `anio_causacion`. Antes de
    2005: 1000 (base original Ley 100/1993). Desde 2015 en adelante: se queda
    fija en 1300 (el escalonamiento de la Ley 797/2003 termino ese año)."""
    if anio_causacion < 2005:
        return 1000
    if anio_causacion >= 2015:
        return 1300
    return _SEMANAS_MINIMAS_POR_ANIO[anio_causacion]


def calcular_tasa_reemplazo(
    ibl: Decimal,
    smlmv_vigente: Decimal,
    semanas_cotizadas: int,
    anio_causacion: int,
) -> Decimal:
    """Formula R completa (Ley 100 de 1993 art. 34, modificada por el art. 10
    Ley 797/2003; el PDF de BASTIUM solo trae la linea base r = 65.5 - 0.5*s).
    Corregida en el Sprint 17 (2026-08-01) tras respuesta del despacho:
    - Rango de la tasa INICIAL (antes del bono): piso 55%, techo 65.5% -- NO un
      piso de 65% como tenia el codigo antes de esta correccion.
    - Semanas minimas para el bono: varian por `anio_causacion`
      (semanas_minimas_requeridas), no una cifra fija de 1300.
    - Techo final (tasa inicial + bonos): 80%.
    """
    if smlmv_vigente <= Decimal("0.00"):
        raise ValueError("El SMLMV vigente debe ser positivo.")

    s = ibl / smlmv_vigente
    r_inicial = Decimal("65.5") - Decimal("0.5") * s
    r_inicial = max(Decimal("55"), min(Decimal("65.5"), r_inicial))

    minimo_semanas = semanas_minimas_requeridas(anio_causacion)
    bono = Decimal("0")
    if semanas_cotizadas > minimo_semanas:
        bloques_50_semanas = (semanas_cotizadas - minimo_semanas) // 50
        bono = Decimal(bloques_50_semanas) * Decimal("1.5")

    r_final = min(Decimal("80"), r_inicial + bono)
    return Rounding.money(r_final)


# Regimenes pensionales historicos anteriores a la Ley 797/2003 (Sprint 70/91,
# respuesta del despacho 2026-08-22): calcular_tasa_reemplazo (arriba) SOLO
# cubre la formula vigente desde 2004 en adelante. Desde la respuesta del
# despacho del 16/11/2026 (fechas exactas de vigencia de cada regimen), el
# router por fecha de causacion vive en app/engine/labor/vigencia_pensional.py
# (regimen_por_fecha / calcular_tasa_reemplazo_por_fecha), que despacha a
# estas funciones.
def calcular_tasa_reemplazo_regimen_1985_1989() -> Decimal:
    """Regimen de Ley 33 de 1985 y Ley 71 de 1988: tasa de reemplazo fija del
    75%, sin variables dinamicas (respuesta del despacho, Sprint 70,
    22/08/2026)."""
    return Decimal("75.00")


def calcular_tasa_reemplazo_iss_pre_ley_100(semanas_cotizadas: int) -> Decimal:
    """Regimen ISS anterior a la Ley 100 de 1993 (Acuerdo 049 de 1990):
    exige minimo 500 semanas cotizadas. Base 45% desde 500 semanas, o 75%
    desde 1.000 semanas; +3% por cada bloque de 50 semanas adicionales a la
    base que corresponda, tope 90% (respuesta del despacho, Sprint 70,
    22/08/2026)."""
    if semanas_cotizadas < 500:
        raise ValueError(
            "El regimen ISS anterior a la Ley 100 (Acuerdo 049/1990) exige minimo "
            "500 semanas cotizadas."
        )
    if semanas_cotizadas < 1000:
        base = Decimal("45.00")
        bloques = (semanas_cotizadas - 500) // 50
    else:
        base = Decimal("75.00")
        bloques = (semanas_cotizadas - 1000) // 50
    tasa = base + Decimal(bloques) * Decimal("3.00")
    return Rounding.money(min(tasa, Decimal("90.00")))


def calcular_tasa_reemplazo_ley_100_original(semanas_cotizadas: int) -> Decimal:
    """Ley 100 de 1993 en su version original (antes de la reforma de la Ley
    797/2003): exige minimo 1.000 semanas cotizadas. Base 65% desde 1.000
    semanas; +2% por cada bloque de 50 semanas entre 1.000 y 1.200, +3% por
    cada bloque de 50 semanas entre 1.200 y 1.400; tope 85% (respuesta del
    despacho, Sprint 70, 22/08/2026)."""
    if semanas_cotizadas < 1000:
        raise ValueError(
            "La Ley 100 de 1993 (version original) exige minimo 1.000 semanas cotizadas."
        )
    tasa = Decimal("65.00")
    if semanas_cotizadas > 1000:
        semanas_tramo_1 = min(semanas_cotizadas, 1200)
        bloques_1 = (semanas_tramo_1 - 1000) // 50
        tasa += Decimal(bloques_1) * Decimal("2.00")
    if semanas_cotizadas > 1200:
        semanas_tramo_2 = min(semanas_cotizadas, 1400)
        bloques_2 = (semanas_tramo_2 - 1200) // 50
        tasa += Decimal(bloques_2) * Decimal("3.00")
    return Rounding.money(min(tasa, Decimal("85.00")))


def calcular_tasa_reemplazo_invalidez_grado_2(semanas_cotizadas: int) -> Decimal:
    """Pension de invalidez, grado 2 (perdida de capacidad laboral >= 66%):
    exige minimo 800 semanas cotizadas. Base 54% desde 800 semanas, +2% por
    cada bloque de 50 semanas adicionales, tope 75% (respuesta del despacho,
    Sprint 70, 22/08/2026 -- coincide con la plantilla P9 del despacho ya
    citada en el Sprint 91, filas 81-91). El despacho reconfirmo el 16/11/2026
    que el tope de 75% es el del Grado 2 (no el del Grado 1)."""
    if semanas_cotizadas < 800:
        raise ValueError(
            "La pension de invalidez grado 2 exige minimo 800 semanas cotizadas."
        )
    bloques = (semanas_cotizadas - 800) // 50
    tasa = Decimal("54.00") + Decimal(bloques) * Decimal("2.00")
    return Rounding.money(min(tasa, Decimal("75.00")))


def calcular_tasa_reemplazo_invalidez_grado_1(semanas_cotizadas: int) -> Decimal:
    """Pension de invalidez, grado 1: base 45% del IBL por 500 semanas
    cotizadas, +1,5% por cada bloque completo de 50 semanas adicionales, tope
    60% (alcanzado a las 1.000 semanas). Respuesta del despacho, Sprint 70/91
    (seguimiento), 16/11/2026: "El tope correcto es el 60% del IBL [...] El
    75% corresponde a la Invalidez Grado 2" -- resuelve la discrepancia con la
    plantilla P9 (que mostraba 75% para este grado).

    Por debajo de 500 semanas la formula confirmada no define tasa: se lanza
    ValueError (mismo criterio que el minimo de 800 del Grado 2) en vez de
    extrapolar."""
    if semanas_cotizadas < 500:
        raise ValueError(
            "La formula de pension de invalidez grado 1 parte de 500 semanas cotizadas."
        )
    bloques = (semanas_cotizadas - 500) // 50
    tasa = Decimal("45.00") + Decimal(bloques) * Decimal("1.50")
    return Rounding.money(min(tasa, Decimal("60.00")))


def calcular_tasa_reemplazo_invalidez(grado: int, semanas_cotizadas: int) -> Decimal:
    """Despacha la tasa de reemplazo de invalidez segun el grado (1 o 2).
    Cualquier otro grado lanza ValueError: el despacho solo confirmo esos dos."""
    if grado == 1:
        return calcular_tasa_reemplazo_invalidez_grado_1(semanas_cotizadas)
    if grado == 2:
        return calcular_tasa_reemplazo_invalidez_grado_2(semanas_cotizadas)
    raise ValueError(f"Grado de invalidez no soportado: {grado} (solo 1 o 2).")


def calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int:
    """Semanas de cotizacion en dias calendario reales (365/366), no dias
    habiles ni ano comercial de 360 (Sentencia SL138-2024). Los periodos
    solapados se unen antes de contar, para no cotizar "doble" el mismo dia
    calendario. Conteo INCLUSIVO (+1 dia por periodo fusionado, respuesta del
    despacho, Sprint 78, 22/08/2026): "se deben restar las fechas, sumar 1
    (inclusivo) y dividir exactamente por 7" -- misma regla general de
    conteo inclusivo del Sprint 3, ahora confirmada tambien para densidad
    pensional (antes de esta respuesta, el sprint la dejaba deliberadamente
    sin el +1 por falta de confirmacion)."""
    if not periodos_cotizados:
        return 0
    for inicio, fin in periodos_cotizados:
        if fin < inicio:
            raise ValueError(f"Periodo invalido: fin ({fin}) es anterior a inicio ({inicio}).")

    periodos_ordenados = sorted(periodos_cotizados)
    fusionados: list[tuple[date, date]] = [periodos_ordenados[0]]
    for inicio, fin in periodos_ordenados[1:]:
        ultimo_inicio, ultimo_fin = fusionados[-1]
        if inicio <= ultimo_fin:
            fusionados[-1] = (ultimo_inicio, max(ultimo_fin, fin))
        else:
            fusionados.append((inicio, fin))

    dias_totales = sum((fin - inicio).days + 1 for inicio, fin in fusionados)
    semanas = (Decimal(dias_totales) / Decimal("7")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(semanas)
