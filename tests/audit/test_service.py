from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.engine.audit.service import (
    historial_de_expediente,
    reconstruir_liquidacion,
    registrar_liquidacion,
)
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from database.models import AreaDerecho, AuditLog, Base, Expediente


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def _expediente(session) -> int:
    expediente = Expediente(
        radicado="2026-00200",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()
    return expediente.id


def _resultado() -> LiquidationResult:
    debt = PendingDebt(Decimal("300000.00"), Decimal("3000.00"), Decimal("0.00"))
    balance = RunningBalance(date=date(2026, 1, 1), debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=date(2026, 1, 1),
        concept="Cuota enero",
        capital_base=Decimal("300000.00"),
        interest_rate=Decimal("1.00"),
        interest_amount=Decimal("3000.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
        rate_source="Tasa pactada (Art. 1617 C.C.)",
    )
    return LiquidationResult(items=[item])


def test_registrar_liquidacion_crea_fila_con_usuario_explicito(session):
    expediente_id = _expediente(session)

    log = registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 7, 14),
        resultado=_resultado(),
        usuario="jsilva",
    )

    assert log.id is not None
    assert log.usuario == "jsilva"
    assert log.fecha_corte == date(2026, 7, 14)
    assert log.area_derecho == "CIVIL_FAMILIA"
    assert isinstance(log.fecha_ejecucion, datetime)
    assert session.query(AuditLog).count() == 1


def test_registrar_liquidacion_usa_getpass_si_no_se_pasa_usuario(session, monkeypatch):
    monkeypatch.setattr("app.engine.audit.service.getpass.getuser", lambda: "usuario-del-so")
    expediente_id = _expediente(session)

    log = registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 7, 14),
        resultado=_resultado(),
    )

    assert log.usuario == "usuario-del-so"


def test_reconstruir_liquidacion_devuelve_resultado_identico(session):
    expediente_id = _expediente(session)
    resultado_original = _resultado()

    log = registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 7, 14),
        resultado=resultado_original,
        usuario="jsilva",
    )

    reconstruido = reconstruir_liquidacion(session, log.id)

    assert reconstruido == resultado_original


def test_reconstruir_liquidacion_con_id_inexistente_lanza_value_error(session):
    with pytest.raises(ValueError, match="No existe un registro de auditoría"):
        reconstruir_liquidacion(session, 9999)


def test_historial_de_expediente_ordena_mas_reciente_primero_y_es_append_only(session):
    expediente_id = _expediente(session)

    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 6, 1),
        resultado=_resultado(),
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 6, 1, 9, 0, 0),
    )
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho="CIVIL_FAMILIA",
        fecha_corte=date(2026, 7, 14),
        resultado=_resultado(),
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 7, 14, 9, 0, 0),
    )

    historial = historial_de_expediente(session, expediente_id)

    assert len(historial) == 2
    assert historial[0].fecha_corte == date(2026, 7, 14)
    assert historial[1].fecha_corte == date(2026, 6, 1)


def test_historial_de_expediente_sin_liquidaciones_devuelve_lista_vacia(session):
    expediente_id = _expediente(session)

    historial = historial_de_expediente(session, expediente_id)

    assert historial == []
