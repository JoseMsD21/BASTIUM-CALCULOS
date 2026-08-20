"""Recalculo historico de liquidaciones afectadas por las correcciones del
Sprint 30 (Sprint 47). Ver docs/Pendientes.md, seccion "Sprint 47", y
docs/Preguntas-Para-Abogado-Respondidas.md, misma seccion, para el fraseo
legal exacto y el protocolo completo confirmado por el despacho.

Contexto (no repetir en cada docstring de abajo): el Sprint 30 corrigio dos
computos de fecha/conteo -- `fecha_interrupcion_efectiva`
(app/engine/temporal/prescripcion.py, prescripcion fecha-a-fecha real en vez
de <= 365 dias fijos) y el conteo de dias de prestaciones sociales en
`LaboralStrategy.liquidar` (app/services/area_strategy.py, ahora inclusivo
sobre base comercial de 360 dias) -- pero por diseno explicito no toco
ninguna liquidacion ya guardada en AuditLog. El despacho confirmo
(2026-08-13) que es obligatorio recalcular (verdad real / primacia de la
realidad, Art. 53 CP), con un protocolo distinto segun el estado procesal de
cada expediente.

Este modulo NUNCA sobrescribe una fila de AuditLog existente -- toda
liquidacion recalculada se guarda como una fila NUEVA vinculada a la anterior
via `AuditLog.liquidacion_anterior_id` (mecanismo tecnico decidido con el
usuario antes de este sprint, ver Pendientes.md). Reutiliza
`app.engine.audit.service.registrar_liquidacion` para crear esa fila nueva
(no duplica la logica de serializacion/persistencia de AuditLog) y
`app.engine.liquidation.registry.AreaRegistry` para despachar la
`AreaStrategy` correcta por area de derecho -- el mismo mecanismo que ya usa
`app/views/expediente_detalle.py` para liquidar en primer lugar."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.core.exceptions import ParametroNoDisponibleError
from app.engine.audit.service import reconstruir_liquidacion, registrar_liquidacion
from app.engine.liquidation.registry import AreaRegistry
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from database.models import AuditLog, EstadoProcesal, Expediente

# Cierre del Sprint 30 en main: commit 5c4cc9a ("merge: Sprint 30 - corrige
# error de un dia en prescripcion y prestaciones"), 2026-08-04 17:15:23-05:00
# (hora de Bogota, igual que el resto de fechas de cierre de sprint en
# docs/Pendientes.md). Cualquier AuditLog.fecha_ejecucion anterior a esta
# marca pudo calcularse con la logica defectuosa -- ver
# identificar_liquidaciones_pre_sprint30.
SPRINT_30_CIERRE_COMMIT = "5c4cc9a"
SPRINT_30_CIERRE = datetime(2026, 8, 4, 17, 15, 23)

# Flag literal exigido por el despacho (docs/Preguntas-Para-Abogado-Respondidas.md,
# Sprint 47): "marcar con flag 'OBSOLETO - REQUIERE RECÁLCULO' todas las
# liquidaciones generadas antes del cierre del Sprint 30".
FLAG_OBSOLETO = "OBSOLETO - REQUIERE RECÁLCULO"

# Umbral de priorizacion exigido por el despacho: "el recalculo automatizado
# debe priorizar los expedientes donde la alerta de prescripcion este a menos
# de 30 dias de ocurrir".
UMBRAL_DIAS_PRESCRIPCION_URGENTE = 30

# Acciones del protocolo de recalculo segun estado procesal (despacho,
# Sprint 47). COSA_JUZGADA es la unica que NO recalcula.
ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION = "RECALCULAR_MEMORIAL_ACTUALIZACION"
ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO = "RECALCULAR_MEMORIAL_ERROR_ARITMETICO"
ACCION_NO_RECALCULAR_COSA_JUZGADA = "NO_RECALCULAR_COSA_JUZGADA"

_ACCION_POR_ESTADO = {
    EstadoProcesal.EN_TRAMITE: ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION,
    EstadoProcesal.PRESENTADO_JUZGADO_CPACA: ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO,
    EstadoProcesal.COSA_JUZGADA: ACCION_NO_RECALCULAR_COSA_JUZGADA,
}


class CosaJuzgadaNoRecalculableError(Exception):
    """Se lanza al intentar recalcular (o generar un memorial para) un
    expediente en EstadoProcesal.COSA_JUZGADA. Instruccion explicita del
    despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 47): NO se
    recalcula, se mantiene el valor por seguridad juridica, salvo recurso de
    revision por error de hecho manifiesto (ese recurso, de haber lugar, es
    un tramite manual del abogado -- fuera del alcance automatizado de este
    modulo). Vive aqui (la capa que escribe AuditLog), no en
    app/engine/reports/memoriales.py, para que la restriccion se aplique en
    la capa que efectivamente escribe datos, sin importar el llamador --
    memoriales.py importa esta misma excepcion en vez de duplicarla, ver
    hallazgo de code review del Sprint 47 (recalcular_liquidacion no
    validaba estado_procesal, solo lo hacia el script de orquestacion y la
    generacion de memoriales, ambos posteriores al punto donde ya se habia
    escrito la fila AuditLog nueva)."""


def accion_por_estado_procesal(estado: EstadoProcesal) -> str:
    """Protocolo de recalculo segun estado procesal, tal como lo confirmo el
    despacho: EN_TRAMITE -> recalculo obligatorio + Memorial de
    Actualizacion/Correccion; PRESENTADO_JUZGADO_CPACA -> recalculo +
    memorial de correccion de error aritmetico (Art. 151 CPACA);
    COSA_JUZGADA -> NO recalcular, se mantiene el valor por seguridad
    juridica."""
    return _ACCION_POR_ESTADO[estado]


# ---------------------------------------------------------------------------
# Identificacion y marcado (BD)
# ---------------------------------------------------------------------------


def identificar_liquidaciones_pre_sprint30(
    session: Session, *, cierre: datetime = SPRINT_30_CIERRE
) -> list[AuditLog]:
    """Todas las filas de AuditLog generadas antes del cierre del Sprint 30 y
    que todavia no estan marcadas obsoletas ni son ellas mismas el producto de
    un recalculo (liquidacion_anterior_id IS NULL) -- idempotente: una
    segunda corrida no vuelve a traer las que ya se marcaron. Ordenadas por
    fecha_ejecucion ascendente (mas antiguas primero)."""
    return (
        session.query(AuditLog)
        .filter(
            and_(
                AuditLog.fecha_ejecucion < cierre,
                AuditLog.obsoleto_requiere_recalculo.is_(False),
                AuditLog.liquidacion_anterior_id.is_(None),
            )
        )
        .order_by(AuditLog.fecha_ejecucion.asc())
        .all()
    )


def marcar_obsoletas(
    session: Session, logs: list[AuditLog] | None = None
) -> list[AuditLog]:
    """Marca `logs` (o el resultado de identificar_liquidaciones_pre_sprint30
    si no se pasa nada) con el flag literal que exige el despacho. No toca
    resultado_json -- el marcado es aditivo, la fila obsoleta se preserva tal
    cual se entrego (rastro de auditoria)."""
    if logs is None:
        logs = identificar_liquidaciones_pre_sprint30(session)
    for log in logs:
        log.obsoleto_requiere_recalculo = True
        log.motivo_recalculo = FLAG_OBSOLETO
    session.commit()
    return logs


# ---------------------------------------------------------------------------
# Log de diferencias
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DiferenciaRecalculo:
    audit_log_anterior_id: int
    audit_log_nuevo_id: int | None
    monto_anterior: Decimal
    monto_recalculado: Decimal
    diferencia_monto: Decimal
    dias_cubiertos_anterior: int | None
    dias_cubiertos_recalculado: int | None
    diferencia_dias: int | None
    resumen_texto: str


def _dias_cubiertos(resultado: LiquidationResult) -> int | None:
    """Dias entre la primera y la ultima fecha de la cronologia (inclusive),
    o None si el resultado no tiene items. Es un proxy honesto de "extension
    temporal cubierta por la liquidacion" a partir de datos que SI estan
    expuestos en LiquidationResult -- las liquidaciones Laborales concentran
    todos sus eventos en la fecha de terminacion (Art. 65 CST, ver
    LaborScheduler), asi que para esa area el valor tipicamente es 1 en
    ambos lados y la diferencia es 0; para areas con cronologia extendida
    (Civil/Familia, Comercial) puede variar si el recalculo cambia el rango
    de fechas cubierto (p.ej. por el efecto interruptor de la prescripcion)."""
    if not resultado.items:
        return None
    fechas = [item.date for item in resultado.items]
    return (max(fechas) - min(fechas)).days + 1


def _formatear_pesos(valor: Decimal) -> str:
    signo = "+" if valor > Decimal("0.00") else ("-" if valor < Decimal("0.00") else "")
    return f"{signo}${abs(valor):,.2f} pesos"


def calcular_diferencia(
    resultado_anterior: LiquidationResult,
    resultado_nuevo: LiquidationResult,
    *,
    audit_log_anterior_id: int,
    audit_log_nuevo_id: int | None = None,
) -> DiferenciaRecalculo:
    """Comparativo numerico entre la liquidacion vieja (guardada con la
    logica pre-Sprint-30) y la recalculada con la logica actual --
    "Diferencia recuperada: +X dias / +$Z pesos" (formato exigido por el
    despacho). El monto es GRAN TOTAL ADEUDADO (capital + interes +
    indexacion), igual que la fila "GRAN TOTAL ADEUDADO" que ya muestran
    ReportSummaryBuilder/pdf.py/word.py."""
    monto_anterior = resultado_anterior.final_balance().total()
    monto_recalculado = resultado_nuevo.final_balance().total()
    diferencia_monto = monto_recalculado - monto_anterior

    dias_anterior = _dias_cubiertos(resultado_anterior)
    dias_recalculado = _dias_cubiertos(resultado_nuevo)
    diferencia_dias = (
        dias_recalculado - dias_anterior
        if dias_anterior is not None and dias_recalculado is not None
        else None
    )

    partes = []
    if diferencia_dias:
        signo_dias = "+" if diferencia_dias > 0 else ""
        partes.append(f"{signo_dias}{diferencia_dias} días")
    partes.append(_formatear_pesos(diferencia_monto))
    resumen_texto = "Diferencia recuperada: " + " / ".join(partes)

    return DiferenciaRecalculo(
        audit_log_anterior_id=audit_log_anterior_id,
        audit_log_nuevo_id=audit_log_nuevo_id,
        monto_anterior=monto_anterior,
        monto_recalculado=monto_recalculado,
        diferencia_monto=diferencia_monto,
        dias_cubiertos_anterior=dias_anterior,
        dias_cubiertos_recalculado=dias_recalculado,
        diferencia_dias=diferencia_dias,
        resumen_texto=resumen_texto,
    )


# ---------------------------------------------------------------------------
# Recalculo (liquidacion nueva vinculada a la anterior, no sobrescribe)
# ---------------------------------------------------------------------------


def recalcular_liquidacion(
    session: Session,
    audit_log: AuditLog,
    *,
    fecha_corte: date | None = None,
    usuario: str | None = None,
) -> tuple[AuditLog, DiferenciaRecalculo]:
    """Re-ejecuta la liquidacion de `audit_log` con la logica ACTUAL
    (post-Sprint-30) sobre las obligaciones/abonos vigentes en BD para ese
    expediente, usando el mismo despacho AreaRegistry.get_strategy(...) que
    ya usa app/views/expediente_detalle.py. Guarda el resultado como una
    AuditLog NUEVA vinculada a `audit_log` via liquidacion_anterior_id
    (append-only -- nunca sobrescribe `audit_log.resultado_json`) y marca
    `audit_log` como obsoleta si todavia no lo estaba.

    Restriccion dura (Art. 53 CP / seguridad juridica, ver
    CosaJuzgadaNoRecalculableError): si el expediente esta en
    EstadoProcesal.COSA_JUZGADA, esta funcion se NIEGA a recalcular --
    lanza ANTES de leer/escribir nada -- sin importar quien la llame. Esta
    es la UNICA garantia real: un llamador que se salte
    scripts/recalcular_historicas_sprint30.py (una vista de GUI futura, un
    script de mantenimiento puntual, una consola interactiva) no tiene
    ninguna otra barrera -- la validacion en
    app/engine/reports/memoriales.py solo protege la generacion del
    documento, que ocurre DESPUES de que esta funcion ya habria escrito la
    fila AuditLog nueva.

    Nota conocida: esto asume que las filas Obligacion/Abono del expediente
    no cambiaron desde que `audit_log` se genero -- el AuditLog original solo
    guarda el RESULTADO, no los parametros de entrada, asi que no hay forma
    de reconstruir con certeza los inputs exactos de entonces si alguien
    edito la obligacion despues. Es la misma limitacion que ya tiene
    reconstruir_liquidacion para cualquier otro proposito de auditoria."""
    expediente = session.get(Expediente, audit_log.expediente_id)
    if expediente is None:
        raise ValueError(f"No existe el expediente {audit_log.expediente_id}.")
    accion = accion_por_estado_procesal(expediente.estado_procesal)
    if accion == ACCION_NO_RECALCULAR_COSA_JUZGADA:
        raise CosaJuzgadaNoRecalculableError(
            f"El expediente {expediente.radicado!r} está en cosa juzgada (fallo en "
            "firme) -- el despacho instruyó explícitamente NO recalcular en este "
            "caso, salvo recurso de revisión por error de hecho manifiesto. "
            f"AuditLog #{audit_log.id} se mantiene sin cambios."
        )

    resultado_anterior = reconstruir_liquidacion(session, audit_log.id)
    obligaciones = list(expediente.obligaciones)
    abonos = [abono for obligacion in obligaciones for abono in obligacion.abonos]
    for obligacion in obligaciones:
        list(obligacion.eventos_laborales)
        list(obligacion.descuentos_laborales)
        # idem (Sprint 74): CivilFamiliaStrategy lee obligacion.beneficiario para
        # topar la vigencia de las cuotas RECURRENTE -- ver expediente_detalle.py.
        _ = obligacion.beneficiario

    fecha_corte_final = fecha_corte or audit_log.fecha_corte
    estrategia = AreaRegistry.get_strategy(audit_log.area_derecho)
    resultado_nuevo = estrategia.liquidar(
        obligaciones=obligaciones, abonos=abonos, fecha_corte=fecha_corte_final
    )

    nuevo_log = registrar_liquidacion(
        session,
        expediente_id=audit_log.expediente_id,
        area_derecho=audit_log.area_derecho,
        fecha_corte=fecha_corte_final,
        resultado=resultado_nuevo,
        usuario=usuario,
    )

    diferencia = calcular_diferencia(
        resultado_anterior,
        resultado_nuevo,
        audit_log_anterior_id=audit_log.id,
        audit_log_nuevo_id=nuevo_log.id,
    )

    nuevo_log.liquidacion_anterior_id = audit_log.id
    nuevo_log.motivo_recalculo = (
        f"Recálculo Sprint 30 (commit {SPRINT_30_CIERRE_COMMIT}) de AuditLog "
        f"#{audit_log.id}. {diferencia.resumen_texto}."
    )

    if not audit_log.obsoleto_requiere_recalculo:
        audit_log.obsoleto_requiere_recalculo = True
        audit_log.motivo_recalculo = FLAG_OBSOLETO

    session.commit()

    return nuevo_log, diferencia


# ---------------------------------------------------------------------------
# Priorizacion por cercania de prescripcion
# ---------------------------------------------------------------------------


def dias_para_prescribir(
    session: Session,
    expediente: Expediente,
    fecha_referencia: date,
    tipo_accion: TipoAccion = TipoAccion.EJECUTIVA,
) -> int | None:
    """Dias que faltan para que la obligacion mas proxima a prescribir del
    expediente efectivamente prescriba, reutilizando
    app.engine.temporal.prescripcion.calcular_prescripcion (motor ya
    existente del Sprint 7/42, no se reconstruye aqui). None si el
    expediente no tiene obligaciones con fecha_origen o si el parametro de
    plazo no esta configurado (mismo criterio de fallo abierto que ya usa
    app/services/motor_universal.py._marcar_obligaciones_prescritas)."""
    dias_restantes: list[int] = []
    for obligacion in expediente.obligaciones:
        if obligacion.fecha_origen is None:
            continue
        try:
            fecha_limite = calcular_prescripcion(obligacion.fecha_origen, tipo_accion)
        except ParametroNoDisponibleError:
            continue
        dias_restantes.append((fecha_limite - fecha_referencia).days)

    if not dias_restantes:
        return None
    return min(dias_restantes)


def priorizar_recalculo(
    session: Session,
    logs: list[AuditLog],
    *,
    fecha_referencia: date | None = None,
    umbral_dias: int = UMBRAL_DIAS_PRESCRIPCION_URGENTE,
) -> list[AuditLog]:
    """Reordena `logs` (ya identificados como pre-Sprint-30) priorizando los
    expedientes cuya alerta de prescripcion esta a menos de `umbral_dias`
    dias de ocurrir -- instruccion explicita del despacho. Orden final: (1)
    todos los "urgentes" (dias_para_prescribir <= umbral_dias), de mas
    cercano a prescribir a menos; (2) el resto, en el mismo criterio de
    cercania (los que no tienen fecha de prescripcion resoluble -- sin
    obligaciones o sin el parametro de plazo configurado -- quedan siempre al
    final)."""
    if fecha_referencia is None:
        fecha_referencia = date.today()

    expedientes_cache: dict[int, Expediente] = {}

    def _dias_de(log: AuditLog) -> float:
        expediente = expedientes_cache.get(log.expediente_id)
        if expediente is None:
            expediente = session.get(Expediente, log.expediente_id)
            expedientes_cache[log.expediente_id] = expediente
        if expediente is None:
            return float("inf")
        dias = dias_para_prescribir(session, expediente, fecha_referencia)
        return float("inf") if dias is None else dias

    def _clave(log: AuditLog) -> tuple[int, float]:
        dias = _dias_de(log)
        urgente = dias <= umbral_dias
        return (0, dias) if urgente else (1, dias)

    return sorted(logs, key=_clave)
