"""
Motor de prescripcion y caducidad: calcula fechas limite a partir de una
fecha de origen y un tipo de accion/proceso, reutilizando
CalendarUtils.vencimiento_calendario (Sprint 6) para el computo calendario
(meses/anios, con topeo de fin de mes y corrimiento a dia habil).

Modulo independiente de EstadoTermino (Sprint 6): prescripcion/caducidad no
necesitan pausar/reanudar un reloj, solo una fecha limite calculada desde una
fecha de origen (ver docs/superpowers/specs/2026-07-19-sprint7-prescripcion-caducidad-design.md).
"""

from datetime import date
from enum import Enum

from app.engine.time.calendar import CalendarUtils


class TipoAccion(Enum):
    EJECUTIVA = "ejecutiva"
    ORDINARIA = "ordinaria"
    HONORARIOS_PROFESIONALES = "honorarios_profesionales"
    CAMBIARIA_DIRECTA = "cambiaria_directa"
    CAMBIARIA_REGRESO_TENEDOR = "cambiaria_regreso_tenedor"
    CAMBIARIA_REGRESO_ENTRE_OBLIGADOS = "cambiaria_regreso_entre_obligados"


PLAZOS_PRESCRIPCION_MESES = {
    TipoAccion.EJECUTIVA: 60,  # 5 anios (PDF pags. 16/19, 42, 43, 45)
    TipoAccion.ORDINARIA: 120,  # 10 anios (Art. 2536 C.C.)
    TipoAccion.HONORARIOS_PROFESIONALES: 36,  # 3 anios (PDF pag. 35)
    TipoAccion.CAMBIARIA_DIRECTA: 36,  # 3 anios (Art. 789 C.Co.)
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: 12,  # 1 anio (Art. 790 C.Co.)
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: 6,  # 6 meses (Art. 791 C.Co.)
}


def calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date:
    meses = PLAZOS_PRESCRIPCION_MESES[tipo_accion]
    return CalendarUtils.vencimiento_calendario(fecha_exigibilidad, meses)
