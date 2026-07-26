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
