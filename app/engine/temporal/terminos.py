"""
Modelador puro de términos procesales: representa el "reloj" de un plazo
judicial y sus 4 dinámicas de alteración de cómputo (PDF pág. 25):
interrupción (reset), suspensión (pausa), reanudación (resume) y expiración.

Cada función recibe un EstadoTermino y devuelve uno nuevo — ninguna muta el
estado que recibe.
"""

from dataclasses import dataclass, replace
from datetime import date

from app.engine.time.calendar import CalendarUtils


@dataclass(frozen=True)
class EstadoTermino:
    dias_totales: int
    dias_consumidos: int
    checkpoint: date
    suspendido: bool = False


def iniciar_termino(fecha_inicio: date, dias_totales: int) -> EstadoTermino:
    if dias_totales < 1:
        raise ValueError("dias_totales debe ser al menos 1")

    return EstadoTermino(
        dias_totales=dias_totales,
        dias_consumidos=0,
        checkpoint=fecha_inicio,
        suspendido=False,
    )


def dias_restantes(estado: EstadoTermino, fecha_actual: date) -> int:
    if estado.suspendido:
        consumidos = estado.dias_consumidos
    else:
        consumidos = estado.dias_consumidos + CalendarUtils.dias_habiles_entre(
            estado.checkpoint, fecha_actual
        )
    return estado.dias_totales - consumidos


def esta_vencido(estado: EstadoTermino, fecha_actual: date) -> bool:
    return dias_restantes(estado, fecha_actual) <= 0
