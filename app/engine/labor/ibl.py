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


def calcular_tasa_reemplazo(
    ibl: Decimal,
    smlmv_vigente: Decimal,
    semanas_cotizadas: int,
) -> Decimal:
    """Formula R completa (Ley 100 de 1993, art. 34; el PDF de BASTIUM solo
    trae la linea base r = 65.5 - 0.5*s, ver Preguntas-Para-Abogado.md, Sprint
    17): piso 65%, techo 80%, bono +1.5% por cada 50 semanas sobre 1300."""
    if smlmv_vigente <= Decimal("0.00"):
        raise ValueError("El SMLMV vigente debe ser positivo.")

    s = ibl / smlmv_vigente
    r = Decimal("65.5") - Decimal("0.5") * s

    if semanas_cotizadas > 1300:
        bloques_50_semanas = (semanas_cotizadas - 1300) // 50
        r += Decimal(bloques_50_semanas) * Decimal("1.5")

    r = max(Decimal("65"), min(Decimal("80"), r))
    return Rounding.money(r)
