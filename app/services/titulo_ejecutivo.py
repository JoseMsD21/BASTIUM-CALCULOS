"""Sprint 106: datos del titulo ejecutivo de un expediente, capturados una
sola vez por caso (ver `Expediente.tipo_titulo` y siguientes en
database/models.py).

`fecha_limite_prescripcion` es un campo CALCULADO (respuesta del despacho,
docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 106) y por eso no se
guarda en la base de datos: se deriva siempre de `fecha_exigibilidad` y
`termino_prescripcion_anos`.

Desde que fecha se cuenta: ni la respuesta del despacho ni
docs/Pendientes.md (Sprint 106) lo precisan; se cuenta desde
`fecha_exigibilidad`, el mismo punto de partida que ya usa el motor de
prescripcion existente (`calcular_prescripcion(fecha_exigibilidad, ...)` en
app/engine/temporal/prescripcion.py). El computo es el mismo calendario de ese
motor (`CalendarUtils.vencimiento_calendario`): suma N años como N*12 meses,
topa el dia al ultimo dia real del mes de llegada (un 29 de febrero cae en 28
de febrero en año no bisiesto) y corre la fecha al siguiente dia habil si cae
en fin de semana o festivo.

Esta fecha es solo informativa: NO se conecta a las alertas de prescripcion
del Dashboard (que siguen leyendo `Obligacion.tipo_accion_proceso`) ni
interrumpe/suspende el termino por actuaciones procesales -- eso no fue
pedido en este sprint."""

from datetime import date

from app.engine.time.calendar import CalendarUtils
from database.models import TipoTituloEjecutivo

ETIQUETAS_TIPO_TITULO = {
    TipoTituloEjecutivo.SENTENCIA: "Sentencia",
    TipoTituloEjecutivo.ACTA: "Acta (ej. de conciliación)",
    TipoTituloEjecutivo.LAUDO: "Laudo arbitral",
    TipoTituloEjecutivo.RESOLUCION: "Resolución",
    TipoTituloEjecutivo.OTRO: "Otro",
}


def calcular_fecha_limite_prescripcion_titulo(
    fecha_exigibilidad: date | None, termino_prescripcion_anos: int | None
) -> date | None:
    """Fecha limite de prescripcion del titulo ejecutivo, o None si falta la
    fecha de exigibilidad o el termino (0 o None = no capturado)."""
    if fecha_exigibilidad is None or not termino_prescripcion_anos:
        return None
    return CalendarUtils.vencimiento_calendario(
        fecha_exigibilidad, termino_prescripcion_anos * 12
    )
