"""Sprint 74: calcula si una obligacion alimentaria de Civil/Familia sigue vigente
segun el tipo de beneficiario -- arbol de decision pedido por el usuario (reporte
2026-08-13, ver docs/Pendientes.md, Sprint 74).

Reglas implementadas (confirmadas como hecho conocido -- NO son la pregunta abierta
del sprint):
- NINO sin discapacidad: vigente hasta los 18 anos si no estudia; hasta los 25 si
  estudia una carrera profesional/tecnica/tecnologica.
- NINO_DISCAPACIDAD con `Beneficiario.discapacidad_permanente=True`: vigente de
  forma vitalicia (sin `fecha_fin_vigencia`).

Reglas NO implementadas -- deliberadamente sin criterio automatico (pregunta
abierta sin responder del despacho, ver docs/Preguntas-Para-Abogado-Abiertas.md,
seccion Sprint 74):
- CONYUGE: "hasta que supere su condicion de vulnerabilidad" no tiene ningun
  criterio operacional/numerico confirmado -- NO se inventa una edad o plazo
  limite.
- PADRES: "hasta la muerte de cualquiera de las partes" no es calculable sin
  datos de fallecimiento, que el modelo de datos actual no captura.
- OTRO (donante, abuelos, etc.): el sprint solo dice que "aplicarian reglas
  puntuales", sin especificarlas -- se trata igual que CONYUGE/PADRES.
- NINO_DISCAPACIDAD con `discapacidad_permanente` en False/None: el sprint solo
  confirma la regla para discapacidad PERMANENTE -- no se reutiliza la regla de
  NINO sin discapacidad (18/25) sin confirmacion explicita.

En todos estos casos `ResultadoVigencia.determinable_automaticamente` es False y
`fecha_fin_vigencia` es None -- el sistema NUNCA corta la obligacion por edad para
estos beneficiarios (Definicion de Hecho del Sprint 74, punto 2) y lo deja
explicito en `motivo` para que la UI/el reporte lo muestren en vez de fallar en
silencio o inventar un valor."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.core.exceptions import FechaCorteAlimentosRequeridaError
from database.models import Beneficiario, TipoBeneficiario

EDAD_LIMITE_NINO_NO_ESTUDIA = 18
EDAD_LIMITE_NINO_ESTUDIA = 25

_MOTIVOS_NO_DETERMINABLE = {
    TipoBeneficiario.NINO_DISCAPACIDAD: (
        "Nino con discapacidad NO marcada como permanente: el sprint solo "
        "confirma la regla de vigencia vitalicia para discapacidad permanente "
        "-- requiere evaluacion caso a caso."
    ),
    TipoBeneficiario.CONYUGE: (
        "Conyuge: vigente hasta que supere su condicion de vulnerabilidad -- sin "
        "criterio operacional confirmado por el despacho (pregunta abierta, ver "
        "Preguntas-Para-Abogado-Abiertas.md, Sprint 74). Requiere evaluacion caso "
        "a caso, no se calcula una fecha de fin automatica."
    ),
    TipoBeneficiario.PADRES: (
        "Padres: vigente hasta la muerte de cualquiera de las partes -- no "
        "calculable automaticamente sin datos de fallecimiento. Requiere "
        "evaluacion caso a caso."
    ),
    TipoBeneficiario.OTRO: (
        "Otro beneficiario (donante, abuelos, etc.): el sprint no especifica "
        "reglas de vigencia puntuales -- requiere evaluacion caso a caso."
    ),
}


@dataclass(frozen=True)
class ResultadoVigencia:
    """Resultado de `calcular_vigencia_alimentos()`.

    `vigente` es None cuando `determinable_automaticamente` es False -- NUNCA
    asumir True/False por defecto en ese caso, mostrar `motivo` en vez de eso."""

    vigente: bool | None
    fecha_fin_vigencia: date | None
    determinable_automaticamente: bool
    motivo: str


def calcular_edad(fecha_nacimiento: date, fecha_referencia: date) -> int:
    """Edad en anos cumplidos de una persona con `fecha_nacimiento`, a
    `fecha_referencia`."""
    if fecha_nacimiento > fecha_referencia:
        raise ValueError(
            "La fecha de nacimiento no puede ser posterior a la fecha de referencia."
        )
    edad = fecha_referencia.year - fecha_nacimiento.year
    if (fecha_referencia.month, fecha_referencia.day) < (
        fecha_nacimiento.month,
        fecha_nacimiento.day,
    ):
        edad -= 1
    return edad


def _fecha_cumpleanos(fecha_nacimiento: date, edad: int) -> date:
    """Fecha exacta en que la persona nacida en `fecha_nacimiento` cumple `edad`
    anios. Caso raro (29 de febrero, ano bisiesto) en un ano de destino NO
    bisiesto: se retrocede al 28 de febrero -- convencion elegida (no hay una
    respuesta "correcta" unica), documentada aqui para que sea facil de revisar
    si el despacho pide otra."""
    anio = fecha_nacimiento.year + edad
    try:
        return date(anio, fecha_nacimiento.month, fecha_nacimiento.day)
    except ValueError:
        return date(anio, 2, 28)


def calcular_vigencia_alimentos(
    beneficiario: Beneficiario, fecha_referencia: date
) -> ResultadoVigencia:
    """Calcula la vigencia de una obligacion alimentaria segun el tipo de
    `beneficiario` -- ver docstring del modulo para las reglas exactas."""
    if beneficiario.tipo == TipoBeneficiario.NINO:
        edad_limite = (
            EDAD_LIMITE_NINO_ESTUDIA if beneficiario.estudia else EDAD_LIMITE_NINO_NO_ESTUDIA
        )
        fecha_fin = _fecha_cumpleanos(beneficiario.fecha_nacimiento, edad_limite)
        # Inclusivo (fecha_referencia <= fecha_fin, no <): mismo criterio que
        # `Obligacion.fecha_fin` en el resto del motor (ver
        # CivilFamiliaStrategy._eventos_de_obligacion, `fin = obligacion.fecha_fin
        # or fecha_corte` pasado tal cual a FamilyScheduler.generate(), que causa
        # el evento CUYA fecha coincide exactamente con `end`) -- el dia exacto
        # del cumpleanos limite todavia cuenta como vigente; deja de estarlo
        # desde el dia siguiente.
        vigente = fecha_referencia <= fecha_fin
        estudia_texto = "estudia" if beneficiario.estudia else "no estudia"
        return ResultadoVigencia(
            vigente=vigente,
            fecha_fin_vigencia=fecha_fin,
            determinable_automaticamente=True,
            motivo=(
                f"Nino sin discapacidad, {estudia_texto}: vigente hasta los "
                f"{edad_limite} anos ({fecha_fin.isoformat()}, inclusive)."
            ),
        )

    if (
        beneficiario.tipo == TipoBeneficiario.NINO_DISCAPACIDAD
        and beneficiario.discapacidad_permanente
    ):
        return ResultadoVigencia(
            vigente=True,
            fecha_fin_vigencia=None,
            determinable_automaticamente=True,
            motivo="Nino con discapacidad permanente: obligacion vitalicia.",
        )

    return ResultadoVigencia(
        vigente=None,
        fecha_fin_vigencia=None,
        determinable_automaticamente=False,
        motivo=_MOTIVOS_NO_DETERMINABLE[beneficiario.tipo],
    )


def fecha_fin_efectiva_recurrente(
    fecha_fin_manual: date | None,
    beneficiario: Beneficiario | None,
    fecha_referencia: date,
) -> date | None:
    """Fecha de fin efectiva para topar la generacion de eventos/cuotas de una
    Obligacion RECURRENTE: el minimo entre `fecha_fin_manual` (si el usuario la
    fijo a mano) y la fecha de fin de vigencia automatica calculada para su
    beneficiario -- solo cuando esta ultima es determinable (NINO sin
    discapacidad). NINO_DISCAPACIDAD vitalicio y CONYUGE/PADRES/OTRO nunca
    aportan una fecha (`fecha_fin_vigencia` siempre None para esos casos, ver
    `calcular_vigencia_alimentos`), asi que jamas cortan la obligacion por edad
    -- cumple el punto 2 de la Definicion de Hecho del Sprint 74.

    Devuelve None si ninguna de las dos fuentes aplica -- el llamador debe usar
    su propio fallback (ej. `fecha_corte`)."""
    fecha_fin_vigencia = None
    if beneficiario is not None:
        fecha_fin_vigencia = calcular_vigencia_alimentos(
            beneficiario, fecha_referencia
        ).fecha_fin_vigencia
    candidatos = [fecha for fecha in (fecha_fin_manual, fecha_fin_vigencia) if fecha is not None]
    return min(candidatos) if candidatos else None


def validar_fecha_corte_beneficiario_obligatoria(
    beneficiario: Beneficiario | None,
    fecha_fin_manual: date | None,
    fecha_referencia: date,
) -> None:
    """Respuesta del despacho, Sprint 74 (22/08/2026): para un beneficiario
    cuya vigencia NO es determinable automaticamente (CONYUGE, PADRES, OTRO,
    o NINO_DISCAPACIDAD sin discapacidad_permanente), el usuario debe
    proporcionar una fecha de corte manual obligatoriamente -- "porque
    requiere una fecha de exoneracion dictada por la autoridad", nunca se
    asume por defecto. Lanza FechaCorteAlimentosRequeridaError si aplica y
    `fecha_fin_manual` es None. No aplica si no hay beneficiario, o si su
    vigencia SI es determinable automaticamente (NINO, o NINO_DISCAPACIDAD
    permanente) -- esos casos nunca requieren fecha de corte manual."""
    if beneficiario is None:
        return
    resultado = calcular_vigencia_alimentos(beneficiario, fecha_referencia)
    if not resultado.determinable_automaticamente and fecha_fin_manual is None:
        raise FechaCorteAlimentosRequeridaError(
            f"La vigencia de este beneficiario ({beneficiario.tipo.value}) no es "
            "determinable automaticamente -- debe proporcionar la fecha de corte "
            "manualmente (respuesta del despacho, Sprint 74: requiere una fecha de "
            "exoneracion dictada por la autoridad)."
        )
