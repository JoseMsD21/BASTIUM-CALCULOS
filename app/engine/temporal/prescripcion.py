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
from typing import List, Optional, Tuple

from app.engine.time.calendar import CalendarUtils
from app.engine.temporal.schedulers.base import Event
from app.services.parametro_service import get_parametro


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


_CLAVE_POR_TIPO_ACCION = {
    TipoAccion.EJECUTIVA: "PRESCRIPCION_EJECUTIVA_MESES",
    TipoAccion.ORDINARIA: "PRESCRIPCION_ORDINARIA_MESES",
    TipoAccion.HONORARIOS_PROFESIONALES: "PRESCRIPCION_HONORARIOS_MESES",
    TipoAccion.CAMBIARIA_DIRECTA: "PRESCRIPCION_CAMBIARIA_DIRECTA_MESES",
    TipoAccion.CAMBIARIA_REGRESO_TENEDOR: "PRESCRIPCION_CAMBIARIA_REGRESO_TENEDOR_MESES",
    TipoAccion.CAMBIARIA_REGRESO_ENTRE_OBLIGADOS: "PRESCRIPCION_CAMBIARIA_REGRESO_ENTRE_OBLIGADOS_MESES",
}


def calcular_prescripcion(fecha_exigibilidad: date, tipo_accion: TipoAccion) -> date:
    meses = int(get_parametro(_CLAVE_POR_TIPO_ACCION[tipo_accion], fecha_exigibilidad))
    return CalendarUtils.vencimiento_calendario(fecha_exigibilidad, meses)


PLAZOS_CADUCIDAD_MESES_CONOCIDOS = {
    # Impugnacion de ineficacia societaria, PDF pag. 40.
    "IMPUGNACION_INEFICACIA_SOCIETARIA": 60,
    # Los siguientes 6 (Seguro se divide en dos, ordinaria/extraordinaria, mismo
    # criterio que los tres plazos cambiarios) fueron precargados en el Sprint 7
    # (2026-08-01) a partir de la respuesta del despacho
    # (Preguntas-Para-Abogado.md), no del PDF de requisitos.
    "CHEQUES": 6,
    "ENRIQUECIMIENTO_SIN_CAUSA": 12,
    "TRANSPORTE": 24,
    "SEGURO_ORDINARIA": 24,
    "SEGURO_EXTRAORDINARIA": 60,
    "IMPUGNACION_ACTAS_SOCIALES": 2,
}
# Deliberadamente no exhaustivo: solo casos con plazo confirmado (PDF fuente o
# respuesta del despacho); cualquier otro tipo_proceso requiere
# plazo_meses_manual explicito.

_TIPOS_CADUCIDAD_CONOCIDOS = set(PLAZOS_CADUCIDAD_MESES_CONOCIDOS)


def calcular_caducidad(
    fecha_hecho: date,
    tipo_proceso: str,
    plazo_meses_manual: Optional[int] = None,
) -> date:
    # El catalogo conocido tiene prioridad sobre plazo_meses_manual por
    # diseno: si tipo_proceso ya esta confirmado, el valor manual se ignora.
    if tipo_proceso in _TIPOS_CADUCIDAD_CONOCIDOS:
        meses = int(get_parametro(f"CADUCIDAD_{tipo_proceso}_MESES", fecha_hecho))
    elif plazo_meses_manual is not None:
        meses = plazo_meses_manual
    else:
        raise ValueError(
            f"No hay plazo de caducidad conocido para '{tipo_proceso}'; "
            "debe indicarse 'plazo_meses_manual' explicitamente."
        )
    return CalendarUtils.vencimiento_calendario(fecha_hecho, meses)


def filtrar_cuotas_prescritas(
    eventos: List[Event],
    fecha_corte: date,
    tipo_accion: TipoAccion = TipoAccion.EJECUTIVA,
) -> Tuple[List[Event], List[Event]]:
    vivas: List[Event] = []
    prescritas: List[Event] = []
    for evento in eventos:
        fecha_limite = calcular_prescripcion(evento.date, tipo_accion)
        if fecha_limite <= fecha_corte:
            prescritas.append(evento)
        else:
            vivas.append(evento)
    return vivas, prescritas


def fecha_interrupcion_efectiva(fecha_radicacion: date, fecha_notificacion: date) -> date:
    if fecha_notificacion < fecha_radicacion:
        raise ValueError(
            f"fecha_notificacion ({fecha_notificacion}) no puede ser anterior a "
            f"fecha_radicacion ({fecha_radicacion})."
        )
    if (fecha_notificacion - fecha_radicacion).days <= 365:
        return fecha_radicacion
    return fecha_notificacion
