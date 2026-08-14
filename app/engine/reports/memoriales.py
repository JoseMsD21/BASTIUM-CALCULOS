"""Generacion de los 2 memoriales del protocolo de recalculo historico
(Sprint 47) -- reutiliza integramente el motor de reportes existente
(ReportSummaryBuilder/ReportTableBuilder, build_encabezado,
JudicialPDFGenerator/WordReportGenerator, ver app/reports/pdf.py y
app/reports/word.py) siguiendo el mismo wiring que
app/views/liquidaciones.py::_construir_datos_reporte_en_hilo_de_fondo --
este modulo no reimplementa generacion de PDF/Word, solo arma los datos
(titulo/encabezado/resumen/cronologia/diferencia/cuerpo legal) especificos
del memorial.

Protocolo confirmado por el despacho (docs/Preguntas-Para-Abogado-Respondidas.md,
Sprint 47), segun estado procesal del Expediente:
- EN_TRAMITE: "Memorial de Actualizacion/Correccion" (principios de verdad
  real y primacia de la realidad, Art. 53 C.P.), para presentar antes del
  fallo de instancia.
- PRESENTADO_JUZGADO_CPACA: memorial de correccion de error aritmetico
  (Art. 151 CPACA).
- COSA_JUZGADA: NO se genera ningun memorial -- CosaJuzgadaNoRecalculableError.
"""

from __future__ import annotations

from app.engine.audit.service import reconstruir_liquidacion
from app.engine.reports.summary import ReportSummaryBuilder
from app.engine.reports.table_builder import ReportTableBuilder
from app.reports.header import build_encabezado
from app.reports.pdf import JudicialPDFGenerator
from app.reports.word import WordReportGenerator
from app.services.recalculo_historico import (
    ACCION_NO_RECALCULAR_COSA_JUZGADA,
    ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION,
    ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO,
    DiferenciaRecalculo,
    accion_por_estado_procesal,
)
from database.models import AuditLog, EstadoProcesal, Expediente

TIPO_ACTUALIZACION = "ACTUALIZACION"
TIPO_ERROR_ARITMETICO_CPACA = "ERROR_ARITMETICO_CPACA"

_TITULO_POR_TIPO = {
    TIPO_ACTUALIZACION: "MEMORIAL DE ACTUALIZACIÓN/CORRECCIÓN DE LIQUIDACIÓN",
    TIPO_ERROR_ARITMETICO_CPACA: "MEMORIAL DE CORRECCIÓN DE ERROR ARITMÉTICO (ART. 151 CPACA)",
}

_CUERPO_LEGAL_POR_TIPO = {
    TIPO_ACTUALIZACION: (
        "El apoderado presenta memorial de actualización/corrección de la "
        "liquidación practicada en este proceso, en aplicación de los "
        "principios de verdad real y primacía de la realidad (Art. 53 C.P.), "
        "para que el despacho tenga en cuenta el valor recalculado antes del "
        "fallo de instancia. La liquidación original (AuditLog #{anterior_id}) "
        "se calculó con lógica de cómputo posteriormente corregida en el "
        "Sprint 30 (fecha de interrupción de la prescripción fecha-a-fecha "
        "real, y conteo inclusivo de días de prestaciones sociales sobre "
        "base comercial de 360 días); el valor recalculado que se adjunta "
        "aplica esa corrección."
    ),
    TIPO_ERROR_ARITMETICO_CPACA: (
        "El apoderado solicita la corrección del error aritmético advertido "
        "en la liquidación presentada a este despacho (AuditLog "
        "#{anterior_id}), de conformidad con el artículo 151 del Código de "
        "Procedimiento Administrativo y de lo Contencioso Administrativo "
        "(CPACA), aportando el comparativo numérico entre el valor original "
        "y el valor corregido tras la corrección de cómputo del Sprint 30 "
        "(fecha de interrupción de la prescripción fecha-a-fecha real, y "
        "conteo inclusivo de días de prestaciones sociales sobre base "
        "comercial de 360 días)."
    ),
}

_TIPO_POR_ACCION = {
    ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION: TIPO_ACTUALIZACION,
    ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO: TIPO_ERROR_ARITMETICO_CPACA,
}


class CosaJuzgadaNoRecalculableError(Exception):
    """Se lanza al intentar generar un memorial de recalculo para un
    expediente en EstadoProcesal.COSA_JUZGADA. Instruccion explicita del
    despacho: NO se recalcula, se mantiene el valor por seguridad juridica,
    salvo recurso de revision por error de hecho manifiesto (ese recurso,
    de haber lugar, es un tramite manual del abogado -- fuera del alcance
    automatizado de este modulo)."""


def tipo_memorial_por_estado_procesal(estado: EstadoProcesal) -> str:
    """Resuelve cual de los 2 tipos de memorial corresponde segun el
    protocolo del despacho, reutilizando
    app.services.recalculo_historico.accion_por_estado_procesal. Lanza
    CosaJuzgadaNoRecalculableError si el estado es COSA_JUZGADA (no hay
    memorial para ese caso, por diseno)."""
    accion = accion_por_estado_procesal(estado)
    if accion == ACCION_NO_RECALCULAR_COSA_JUZGADA:
        raise CosaJuzgadaNoRecalculableError(
            "El expediente está en cosa juzgada (fallo en firme) -- el despacho "
            "instruyó explícitamente NO recalcular ni generar memorial en este "
            "caso, salvo recurso de revisión por error de hecho manifiesto."
        )
    return _TIPO_POR_ACCION[accion]


def _formatear_dias(valor: int | None) -> str:
    return "N/A" if valor is None else str(valor)


def _construir_datos_memorial(
    session,
    expediente: Expediente,
    audit_log_anterior: AuditLog,
    audit_log_nuevo: AuditLog,
    diferencia: DiferenciaRecalculo,
    tipo: str,
) -> dict:
    resultado_nuevo = reconstruir_liquidacion(session, audit_log_nuevo.id)

    encabezado = build_encabezado(
        expediente.radicado, expediente.demandante, expediente.demandado, expediente.juzgado
    )
    summary = ReportSummaryBuilder().build_summary(resultado_nuevo)
    table_data = ReportTableBuilder().build_matrix(resultado_nuevo)
    renta_liquida = ReportSummaryBuilder().build_renta_liquida(resultado_nuevo)

    diferencia_recalculo = {
        "audit_log_anterior": f"AuditLog #{audit_log_anterior.id}",
        "monto_anterior": f"${diferencia.monto_anterior:,.2f}",
        "monto_recalculado": f"${diferencia.monto_recalculado:,.2f}",
        "diferencia_monto": (
            f"{'+' if diferencia.diferencia_monto > 0 else ''}"
            f"${diferencia.diferencia_monto:,.2f}"
        ),
        "dias_cubiertos_anterior": _formatear_dias(diferencia.dias_cubiertos_anterior),
        "dias_cubiertos_recalculado": _formatear_dias(diferencia.dias_cubiertos_recalculado),
        "resumen": diferencia.resumen_texto,
    }

    cuerpo_legal = _CUERPO_LEGAL_POR_TIPO[tipo].format(anterior_id=audit_log_anterior.id)

    return {
        "title": _TITULO_POR_TIPO[tipo],
        "encabezado": encabezado,
        "summary": summary,
        "table_data": table_data,
        "renta_liquida": renta_liquida,
        "diferencia_recalculo": diferencia_recalculo,
        "cuerpo_legal": cuerpo_legal,
    }


def generar_memorial(
    session,
    expediente: Expediente,
    audit_log_anterior: AuditLog,
    audit_log_nuevo: AuditLog,
    diferencia: DiferenciaRecalculo,
    *,
    ruta_salida: str,
    formato: str = "pdf",
    tipo: str | None = None,
) -> str:
    """Genera el memorial que corresponda segun el estado procesal del
    expediente (o segun `tipo` explicito, si se provee -- para no acoplar
    esta funcion a que el llamador siempre tenga que tocar
    expediente.estado_procesal) y lo escribe en `ruta_salida`.
    `formato` es "pdf" o "word". Lanza CosaJuzgadaNoRecalculableError si el
    expediente esta en cosa juzgada y no se paso `tipo` explicito."""
    if tipo is None:
        tipo = tipo_memorial_por_estado_procesal(expediente.estado_procesal)
    if tipo not in _TITULO_POR_TIPO:
        raise ValueError(f"Tipo de memorial desconocido: {tipo!r}")

    datos = _construir_datos_memorial(
        session, expediente, audit_log_anterior, audit_log_nuevo, diferencia, tipo
    )

    if formato == "pdf":
        generador = JudicialPDFGenerator(ruta_salida)
    elif formato == "word":
        generador = WordReportGenerator(ruta_salida)
    else:
        raise ValueError(f"Formato de memorial desconocido: {formato!r} (use 'pdf' o 'word')")

    generador.generate(
        datos["title"],
        datos["summary"],
        datos["table_data"],
        datos["encabezado"],
        renta_liquida=datos["renta_liquida"],
        diferencia_recalculo=datos["diferencia_recalculo"],
        cuerpo_legal=datos["cuerpo_legal"],
    )
    return ruta_salida
