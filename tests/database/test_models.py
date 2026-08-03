from datetime import date, datetime
from decimal import Decimal

import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from database.models import (
    Abono,
    AreaDerecho,
    AuditLog,
    Base,
    EventoLaboral,
    Expediente,
    MotivoSuspension,
    Obligacion,
    TipoEventoLaboral,
    TipoObligacion,
)


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


def test_evento_laboral_suspension_asociado_a_obligacion(session):
    expediente = Expediente(
        radicado="2026-00200",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.flush()

    evento = EventoLaboral(
        obligacion_id=obligacion.id,
        tipo=TipoEventoLaboral.SUSPENSION,
        fecha_inicio=date(2020, 3, 1),
        fecha_fin=date(2020, 3, 15),
        motivo_suspension=MotivoSuspension.HUELGA,
    )
    session.add(evento)
    session.commit()

    assert obligacion.eventos_laborales[0].tipo == TipoEventoLaboral.SUSPENSION
    assert obligacion.eventos_laborales[0].motivo_suspension == MotivoSuspension.HUELGA


def test_evento_laboral_incapacidad_no_requiere_motivo_suspension(session):
    expediente = Expediente(
        radicado="2026-00201",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.flush()

    evento = EventoLaboral(
        obligacion_id=obligacion.id,
        tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1),
        fecha_fin=date(2020, 5, 3),
    )
    session.add(evento)
    session.commit()

    assert obligacion.eventos_laborales[0].motivo_suspension is None


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


def test_obligacion_aplica_indexacion_ipc_default_false(session):
    expediente = Expediente(
        radicado="2026-00130",
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

    assert obligacion.aplica_indexacion_ipc is False


def test_obligacion_aplica_indexacion_ipc_true_cuando_se_activa(session):
    expediente = Expediente(
        radicado="2026-00131",
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
        aplica_indexacion_ipc=True,
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.aplica_indexacion_ipc is True


def test_obligacion_moneda_default_cop_al_no_especificarla(session):
    expediente = Expediente(
        radicado="2026-00132",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()

    assert obligacion.moneda == "COP"
    assert obligacion.trm_aplicable is None
    assert obligacion.trm_fecha_referencia is None


def test_obligacion_en_usd_guarda_trm_aplicable_y_fecha_referencia(session):
    expediente = Expediente(
        radicado="2026-00133",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare en USD",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("10000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        moneda="USD",
        trm_aplicable=Decimal("4150.2500"),
        trm_fecha_referencia=date(2025, 1, 1),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.moneda == "USD"
    assert fetched.trm_aplicable == Decimal("4150.2500")
    assert fetched.trm_fecha_referencia == date(2025, 1, 1)


def test_obligacion_incluir_seguridad_social_default_false(session):
    expediente = Expediente(
        radicado="2026-00202",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.incluir_seguridad_social is False
    assert fetched.nivel_riesgo_arl is None


def test_obligacion_incluir_seguridad_social_con_nivel_riesgo(session):
    expediente = Expediente(
        radicado="2026-00203",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1),
        valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=date(2020, 1, 1),
        fecha_fin=date(2020, 12, 31),
        incluir_seguridad_social=True,
        nivel_riesgo_arl="I",
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).one()
    assert fetched.incluir_seguridad_social is True
    assert fetched.nivel_riesgo_arl == "I"


def test_obligacion_anatocismo_defaults(session):
    expediente = Expediente(
        radicado="2026-00140",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()

    assert obligacion.anatocismo_demanda_judicial is False
    assert obligacion.anatocismo_fecha_acuerdo is None


def test_obligacion_anatocismo_activo_con_fecha_acuerdo(session):
    expediente = Expediente(
        radicado="2026-00141",
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2026, 7, 14),
    )
    session.add(expediente)
    session.flush()

    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Capital de pagare",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2025, 1, 1),
        valor=Decimal("1000000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        anatocismo_fecha_acuerdo=date(2026, 2, 15),
    )
    session.add(obligacion)
    session.commit()

    fetched = session.query(Obligacion).filter_by(id=obligacion.id).one()
    assert fetched.anatocismo_fecha_acuerdo == date(2026, 2, 15)
    assert fetched.anatocismo_demanda_judicial is False


def test_columnas_de_filtrado_frecuente_tienen_indice(session):
    inspector = inspect(session.get_bind())
    indices_obligaciones = {
        columna for idx in inspector.get_indexes("obligaciones") for columna in idx["column_names"]
    }
    indices_audit_logs = {
        columna for idx in inspector.get_indexes("audit_logs") for columna in idx["column_names"]
    }
    indices_abonos = {
        columna for idx in inspector.get_indexes("abonos") for columna in idx["column_names"]
    }
    indices_parametros = {
        columna for idx in inspector.get_indexes("parametros_legales") for columna in idx["column_names"]
    }

    assert "expediente_id" in indices_obligaciones
    assert "expediente_id" in indices_audit_logs
    assert "obligacion_id" in indices_abonos
    assert "clave" in indices_parametros
