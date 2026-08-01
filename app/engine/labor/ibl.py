from datetime import date
from decimal import Decimal, ROUND_HALF_UP

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
# Preguntas-Para-Abogado.md: caso de prueba 2006 exige 1075 semanas, no 1300).
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


def calcular_densidad_semanas(periodos_cotizados: list[tuple[date, date]]) -> int:
    """Semanas de cotizacion en dias calendario reales (365/366), no dias
    habiles ni ano comercial de 360 (Sentencia SL138-2024). Los periodos
    solapados se unen antes de contar, para no cotizar "doble" el mismo dia
    calendario."""
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

    dias_totales = sum((fin - inicio).days for inicio, fin in fusionados)
    semanas = (Decimal(dias_totales) / Decimal("7")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    return int(semanas)
