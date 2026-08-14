"""Recalculo historico de liquidaciones afectadas por las correcciones del
Sprint 30 (Sprint 47) -- script de orquestacion, ejecutable a mano
(`python -m scripts.recalcular_historicas_sprint30`) o importable pieza por
pieza (p.ej. desde una futura vista de GUI). Toda la logica de negocio real
vive en app/services/recalculo_historico.py y app/engine/reports/memoriales.py
-- este script solo encadena esas piezas contra la base de datos real
(bastium.db) en el orden que exige el protocolo del despacho
(docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 47):

1. Identificar y marcar (flag "OBSOLETO - REQUIERE RECÁLCULO") todas las
   liquidaciones (AuditLog) generadas antes del cierre del Sprint 30.
2. Priorizar por cercania de prescripcion (<30 dias primero).
3. Por cada una, segun el estado procesal del expediente:
   - COSA_JUZGADA: NO recalcular, se deja el flag de obsoleta como unico
     rastro (para que quede visible que existe una version mas nueva de la
     logica pero que este expediente esta protegido por seguridad juridica).
   - EN_TRAMITE / PRESENTADO_JUZGADO_CPACA: recalcular (liquidacion nueva
     vinculada a la anterior, nunca sobrescribe) y generar el memorial que
     corresponda.

`carpeta_salida` es donde se escriben los memoriales generados (uno por
liquidacion recalculada, nombrado con el radicado y el tipo). Este script NO
decide POR SU CUENTA el estado_procesal de ningun expediente -- lee el que ya
este guardado en BD (ver EstadoProcesal en database/models.py: default
EN_TRAMITE, requiere revision manual antes de correr esto en produccion,
sobre todo para marcar los expedientes en cosa juzgada)."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from sqlalchemy.orm import Session

import database.session as session_module
from app.engine.reports.memoriales import CosaJuzgadaNoRecalculableError, generar_memorial
from app.services.recalculo_historico import (
    ACCION_NO_RECALCULAR_COSA_JUZGADA,
    DiferenciaRecalculo,
    accion_por_estado_procesal,
    identificar_liquidaciones_pre_sprint30,
    marcar_obsoletas,
    priorizar_recalculo,
    recalcular_liquidacion,
)
from database.models import AuditLog, Expediente


@dataclass(frozen=True)
class ResultadoProcesamiento:
    audit_log_anterior_id: int
    expediente_radicado: str
    accion: str
    audit_log_nuevo_id: int | None = None
    diferencia: DiferenciaRecalculo | None = None
    ruta_memorial: str | None = None


def _sanitizar_nombre_archivo(texto: str) -> str:
    return "".join(caracter if caracter.isalnum() else "_" for caracter in texto)


def procesar_liquidacion(
    session: Session,
    audit_log: AuditLog,
    *,
    carpeta_salida: Path | None,
    formato: str = "pdf",
) -> ResultadoProcesamiento:
    """Aplica el protocolo del despacho a UNA liquidacion ya identificada
    como pre-Sprint-30: recalcula (si el estado procesal lo permite) y
    genera el memorial correspondiente. Si el expediente esta en
    COSA_JUZGADA, no recalcula -- el flag de obsoleta (ya puesto por
    marcar_obsoletas) queda como unico rastro."""
    expediente = session.get(Expediente, audit_log.expediente_id)
    if expediente is None:
        raise ValueError(f"No existe el expediente {audit_log.expediente_id}.")

    accion = accion_por_estado_procesal(expediente.estado_procesal)
    if accion == ACCION_NO_RECALCULAR_COSA_JUZGADA:
        return ResultadoProcesamiento(
            audit_log_anterior_id=audit_log.id,
            expediente_radicado=expediente.radicado,
            accion=accion,
        )

    audit_log_nuevo, diferencia = recalcular_liquidacion(session, audit_log)

    ruta_memorial = None
    if carpeta_salida is not None:
        carpeta_salida.mkdir(parents=True, exist_ok=True)
        extension = "pdf" if formato == "pdf" else "docx"
        nombre = (
            f"{_sanitizar_nombre_archivo(expediente.radicado)}_"
            f"AuditLog{audit_log.id}_recalculo.{extension}"
        )
        ruta_memorial = str(carpeta_salida / nombre)
        try:
            generar_memorial(
                session,
                expediente,
                audit_log,
                audit_log_nuevo,
                diferencia,
                ruta_salida=ruta_memorial,
                formato=formato,
            )
        except CosaJuzgadaNoRecalculableError:
            # No deberia poder pasar (ya se filtro arriba), pero se deja
            # como salvaguarda defensiva en vez de asumir que el chequeo de
            # arriba es infalible ante un cambio futuro de estado_procesal
            # concurrente a esta misma corrida.
            ruta_memorial = None

    return ResultadoProcesamiento(
        audit_log_anterior_id=audit_log.id,
        expediente_radicado=expediente.radicado,
        accion=accion,
        audit_log_nuevo_id=audit_log_nuevo.id,
        diferencia=diferencia,
        ruta_memorial=ruta_memorial,
    )


def ejecutar(
    session: Session,
    *,
    carpeta_salida: Path | None = None,
    formato: str = "pdf",
    fecha_referencia: date | None = None,
) -> list[ResultadoProcesamiento]:
    """Corre el protocolo completo: identifica, marca, prioriza por
    prescripcion, y procesa (recalcula + genera memorial) cada liquidacion
    pre-Sprint-30, en el orden de prioridad resultante."""
    pendientes = identificar_liquidaciones_pre_sprint30(session)
    marcar_obsoletas(session, pendientes)
    priorizados = priorizar_recalculo(session, pendientes, fecha_referencia=fecha_referencia)

    return [
        procesar_liquidacion(session, log, carpeta_salida=carpeta_salida, formato=formato)
        for log in priorizados
    ]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--carpeta-salida",
        type=Path,
        default=Path("memoriales_sprint47"),
        help="Carpeta donde se escriben los memoriales generados.",
    )
    parser.add_argument(
        "--formato", choices=["pdf", "word"], default="pdf", help="Formato de los memoriales."
    )
    args = parser.parse_args()

    session = session_module.get_session()
    try:
        resultados = ejecutar(session, carpeta_salida=args.carpeta_salida, formato=args.formato)
    finally:
        session.close()

    for resultado in resultados:
        if resultado.accion == ACCION_NO_RECALCULAR_COSA_JUZGADA:
            print(
                f"[COSA JUZGADA] Expediente {resultado.expediente_radicado} "
                f"(AuditLog #{resultado.audit_log_anterior_id}): marcado obsoleto, "
                "NO recalculado (seguridad juridica)."
            )
        else:
            print(
                f"[{resultado.accion}] Expediente {resultado.expediente_radicado}: "
                f"{resultado.diferencia.resumen_texto} -> {resultado.ruta_memorial}"
            )


if __name__ == "__main__":
    main()
