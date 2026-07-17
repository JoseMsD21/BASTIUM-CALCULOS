from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from database.models import Base, Expediente, Obligacion, Abono, AuditLog, AreaDerecho, TipoObligacion


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as s:
        yield s


def test_crea_expediente_con_area_civil_familia(session):
    expediente = Expediente(
        radicado="2026-00123",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        juzgado="Juzgado 3 de Familia de Bogota",
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.commit()

    fetched = session.query(Expediente).one()
    assert fetched.radicado == "2026-00123"
    assert fetched.area_derecho == AreaDerecho.CIVIL_FAMILIA


def test_obligacion_puntual_asociada_a_expediente(session):
    expediente = Expediente(
        radicado="2026-00124",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()

    assert expediente.obligaciones[0].concepto == "Gastos medicos"
    assert expediente.obligaciones[0].pagada is False


def test_obligacion_recurrente_tiene_campos_de_periodicidad(session):
    expediente = Expediente(
        radicado="2026-00125",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        dia_pago=5,
        fecha_inicio=date(2026, 1, 1),
        fecha_fin=None,
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.dia_pago == 5
    assert fetched.fecha_fin is None


def test_abono_asociado_a_obligacion(session):
    expediente = Expediente(
        radicado="2026-00126",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.flush()

    abono = Abono(
        obligacion_id=obligacion.id,
        fecha=date(2026, 1, 15),
        monto=Decimal("100000.00"),
        referencia="Consignacion Bancolombia",
    )
    session.add(abono)
    session.commit()

    assert obligacion.abonos[0].monto == Decimal("100000.00")


def test_borrar_expediente_borra_en_cascada_obligaciones_y_abonos(session):
    expediente = Expediente(
        radicado="2026-00127",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Gastos medicos",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2025, 11, 20),
        valor=Decimal("427900.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.flush()
    session.add(Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 15), monto=Decimal("100000.00")))
    session.commit()

    session.delete(expediente)
    session.commit()

    assert session.query(Obligacion).count() == 0
    assert session.query(Abono).count() == 0


def test_audit_log_asociado_a_expediente(session):
    expediente = Expediente(
        radicado="2026-00128",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    log = AuditLog(
        expediente_id=expediente.id,
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 7, 17, 10, 30, 0),
        fecha_corte=date(2026, 7, 14),
        area_derecho="CIVIL_FAMILIA",
        resultado_json="{}",
    )
    session.add(log)
    session.commit()

    assert expediente.audit_logs[0].usuario == "jsilva"
    assert expediente.audit_logs[0].area_derecho == "CIVIL_FAMILIA"


def test_borrar_expediente_borra_en_cascada_audit_logs(session):
    expediente = Expediente(
        radicado="2026-00129",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()
    session.add(
        AuditLog(
            expediente_id=expediente.id,
            usuario="jsilva",
            fecha_ejecucion=datetime(2026, 7, 17, 10, 30, 0),
            fecha_corte=date(2026, 7, 14),
            area_derecho="CIVIL_FAMILIA",
            resultado_json="{}",
        )
    )
    session.commit()

    session.delete(expediente)
    session.commit()

    assert session.query(AuditLog).count() == 0
