from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.services.recalculo_historico import (
    ACCION_NO_RECALCULAR_COSA_JUZGADA,
    ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION,
    FLAG_OBSOLETO,
)
from database.models import (
    AreaDerecho,
    AuditLog,
    EstadoProcesal,
    Expediente,
    Obligacion,
    TipoObligacion,
)
from scripts.recalcular_historicas_sprint30 import ejecutar, procesar_liquidacion


@pytest.fixture
def session():
    s = session_module.get_session()
    yield s
    s.close()


def _expediente(session, estado: EstadoProcesal, radicado: str) -> Expediente:
    expediente = Expediente(
        radicado=radicado,
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2020, 12, 31),
        estado_procesal=estado,
    )
    session.add(expediente)
    session.flush()
    return expediente


def _obligacion_laboral(expediente_id) -> Obligacion:
    return Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
        pagada=False,
        fecha_pago_total=None,
    )


def _log_pre_sprint30(session, expediente) -> AuditLog:
    debt = PendingDebt(Decimal("7830000.00"), Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2020, 12, 31), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2020, 12, 31),
        concept="Prestaciones sociales (logica pre-Sprint-30)",
        capital_base=Decimal("7830000.00"),
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return registrar_liquidacion(
        session,
        expediente_id=expediente.id,
        area_derecho="LABORAL",
        fecha_corte=date(2020, 12, 31),
        resultado=LiquidationResult(items=[item]),
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 7, 1, 9, 0, 0),
    )


def test_procesar_liquidacion_en_tramite_recalcula_y_genera_memorial(session, tmp_path):
    expediente = _expediente(session, EstadoProcesal.EN_TRAMITE, "2026-01001")
    session.add(_obligacion_laboral(expediente.id))
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)

    resultado = procesar_liquidacion(
        session, log_viejo, carpeta_salida=tmp_path, formato="pdf"
    )

    assert resultado.accion == ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION
    assert resultado.audit_log_nuevo_id is not None
    assert resultado.diferencia is not None
    assert resultado.ruta_memorial is not None
    assert (tmp_path / f"2026_01001_AuditLog{log_viejo.id}_recalculo.pdf").exists()


def test_procesar_liquidacion_cosa_juzgada_no_recalcula_ni_genera_memorial(session, tmp_path):
    expediente = _expediente(session, EstadoProcesal.COSA_JUZGADA, "2026-01002")
    session.add(_obligacion_laboral(expediente.id))
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)

    resultado = procesar_liquidacion(
        session, log_viejo, carpeta_salida=tmp_path, formato="pdf"
    )

    assert resultado.accion == ACCION_NO_RECALCULAR_COSA_JUZGADA
    assert resultado.audit_log_nuevo_id is None
    assert resultado.ruta_memorial is None
    # No debe haberse creado ninguna fila AuditLog adicional (no se recalculo).
    assert session.query(AuditLog).filter(AuditLog.expediente_id == expediente.id).count() == 1
    assert list(tmp_path.iterdir()) == []


def test_ejecutar_marca_obsoletas_y_procesa_todas_las_pre_sprint30(session, tmp_path):
    expediente_activo = _expediente(session, EstadoProcesal.EN_TRAMITE, "2026-01003")
    session.add(_obligacion_laboral(expediente_activo.id))
    expediente_cosa_juzgada = _expediente(session, EstadoProcesal.COSA_JUZGADA, "2026-01004")
    session.add(_obligacion_laboral(expediente_cosa_juzgada.id))
    session.flush()

    log_activo = _log_pre_sprint30(session, expediente_activo)
    log_cosa_juzgada = _log_pre_sprint30(session, expediente_cosa_juzgada)

    resultados = ejecutar(session, carpeta_salida=tmp_path, formato="pdf")

    assert len(resultados) == 2
    resultados_por_id = {r.audit_log_anterior_id: r for r in resultados}
    assert resultados_por_id[log_activo.id].accion == ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION
    assert resultados_por_id[log_cosa_juzgada.id].accion == ACCION_NO_RECALCULAR_COSA_JUZGADA

    session.refresh(log_activo)
    session.refresh(log_cosa_juzgada)
    assert log_activo.obsoleto_requiere_recalculo is True
    assert log_activo.motivo_recalculo == FLAG_OBSOLETO
    assert log_cosa_juzgada.obsoleto_requiere_recalculo is True
    assert log_cosa_juzgada.motivo_recalculo == FLAG_OBSOLETO


def test_ejecutar_sin_carpeta_salida_recalcula_pero_no_genera_archivos(session):
    expediente = _expediente(session, EstadoProcesal.EN_TRAMITE, "2026-01005")
    session.add(_obligacion_laboral(expediente.id))
    session.flush()
    _log_pre_sprint30(session, expediente)

    resultados = ejecutar(session, carpeta_salida=None)

    assert len(resultados) == 1
    assert resultados[0].audit_log_nuevo_id is not None
    assert resultados[0].ruta_memorial is None
