import getpass
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.engine.audit.serialization import deserializar_resultado, serializar_resultado
from app.engine.liquidation.result import LiquidationResult
from database.models import AuditLog


def registrar_liquidacion(
    session: Session,
    *,
    expediente_id: int,
    area_derecho: str,
    fecha_corte: date,
    resultado: LiquidationResult,
    usuario: str | None = None,
    fecha_ejecucion: datetime | None = None,
) -> AuditLog:
    """Registra una ejecución de liquidación como fila append-only en AuditLog."""
    log = AuditLog(
        expediente_id=expediente_id,
        usuario=usuario or getpass.getuser(),
        fecha_ejecucion=fecha_ejecucion or datetime.now(),
        fecha_corte=fecha_corte,
        area_derecho=area_derecho,
        resultado_json=serializar_resultado(resultado),
    )
    session.add(log)
    session.commit()
    return log


def reconstruir_liquidacion(session: Session, audit_log_id: int) -> LiquidationResult:
    """Reconstruye exactamente el LiquidationResult de una ejecución pasada, sin recalcular."""
    log = session.get(AuditLog, audit_log_id)
    if log is None:
        raise ValueError(f"No existe un registro de auditoría con id {audit_log_id}.")
    return deserializar_resultado(log.resultado_json)


def historial_de_expediente(session: Session, expediente_id: int) -> list[AuditLog]:
    """Liquidaciones ejecutadas para un expediente, más recientes primero."""
    return (
        session.query(AuditLog)
        .filter(AuditLog.expediente_id == expediente_id)
        .order_by(AuditLog.fecha_ejecucion.desc())
        .all()
    )
