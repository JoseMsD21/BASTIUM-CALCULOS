from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

import database.session as session_module
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.temporal.prescripcion import TipoAccion, calcular_prescripcion
from app.services.recalculo_historico import (
    ACCION_NO_RECALCULAR_COSA_JUZGADA,
    ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION,
    ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO,
    FLAG_OBSOLETO,
    SPRINT_30_CIERRE,
    CosaJuzgadaNoRecalculableError,
    accion_por_estado_procesal,
    calcular_diferencia,
    dias_para_prescribir,
    identificar_liquidaciones_pre_sprint30,
    marcar_obsoletas,
    priorizar_recalculo,
    recalcular_liquidacion,
)
from database.models import (
    AreaDerecho,
    AuditLog,
    EstadoProcesal,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)


@pytest.fixture
def session():
    # Mismo patron que tests/temporal/test_prescripcion.py y
    # tests/services/test_area_strategy.py-style de integracion: usar
    # session_module.get_session() (no un engine aparte) para que quede
    # atado al mismo motor SQLite en memoria que la fixture autouse
    # _db_en_memoria_por_defecto de tests/conftest.py -- necesario porque
    # LaboralStrategy/calcular_prescripcion abren sus propias sesiones
    # internamente via ese mismo modulo (get_parametro).
    s = session_module.get_session()
    yield s
    s.close()


def _expediente(session, radicado="2026-00500", estado=EstadoProcesal.EN_TRAMITE) -> Expediente:
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


def _resultado(monto_total: Decimal, fecha: date = date(2026, 1, 1)) -> LiquidationResult:
    debt = PendingDebt(monto_total, Decimal("0.00"), Decimal("0.00"))
    balance = RunningBalance(date=fecha, debt=debt, event_type="INSTALLMENT")
    item = LiquidationItem(
        date=fecha,
        concept="Cuota",
        capital_base=monto_total,
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=balance,
    )
    return LiquidationResult(items=[item])


def _log_pre_sprint30(session, expediente, monto=Decimal("7830000.00")) -> AuditLog:
    return registrar_liquidacion(
        session,
        expediente_id=expediente.id,
        area_derecho="LABORAL",
        fecha_corte=date(2020, 12, 31),
        resultado=_resultado(monto, fecha=date(2020, 12, 31)),
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 7, 1, 9, 0, 0),
    )


def _log_post_sprint30(session, expediente, monto=Decimal("8000000.00")) -> AuditLog:
    return registrar_liquidacion(
        session,
        expediente_id=expediente.id,
        area_derecho="LABORAL",
        fecha_corte=date(2020, 12, 31),
        resultado=_resultado(monto, fecha=date(2020, 12, 31)),
        usuario="jsilva",
        fecha_ejecucion=datetime(2026, 8, 10, 9, 0, 0),
    )


def _obligacion_laboral(
    expediente_id,
    salario=Decimal("3000000.00"),
    fecha_inicio=date(2020, 1, 1),
    fecha_fin=date(2020, 12, 31),
) -> Obligacion:
    # Mismo fixture (fecha_inicio/fecha_fin/salario) que
    # tests/services/test_area_strategy.py::_obligacion_laboral -- contrato
    # de un año comercial completo (dias_comerciales_360 = 360), sin
    # seguridad social/mora/costas para no depender de mas parametros de los
    # necesarios. fecha_corte == fecha_fin evita la rama de mora.
    return Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato",
        categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=fecha_inicio,
        valor=salario,
        tasa_efectiva_anual=Decimal("0.00"),
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        pagada=False,
        fecha_pago_total=None,
    )


# ---------------------------------------------------------------------------
# Identificacion y marcado
# ---------------------------------------------------------------------------


def test_identificar_liquidaciones_pre_sprint30_incluye_solo_las_anteriores_al_cierre(session):
    expediente = _expediente(session)
    log_viejo = _log_pre_sprint30(session, expediente)
    _log_post_sprint30(session, expediente)

    identificadas = identificar_liquidaciones_pre_sprint30(session)

    assert [log.id for log in identificadas] == [log_viejo.id]


def test_identificar_excluye_las_ya_marcadas_obsoletas(session):
    expediente = _expediente(session)
    log_viejo = _log_pre_sprint30(session, expediente)
    marcar_obsoletas(session, [log_viejo])

    identificadas = identificar_liquidaciones_pre_sprint30(session)

    assert identificadas == []


def test_marcar_obsoletas_pone_el_flag_literal_exigido_por_el_despacho(session):
    expediente = _expediente(session)
    log_viejo = _log_pre_sprint30(session, expediente)

    marcadas = marcar_obsoletas(session, [log_viejo])

    assert len(marcadas) == 1
    assert marcadas[0].obsoleto_requiere_recalculo is True
    assert marcadas[0].motivo_recalculo == FLAG_OBSOLETO == "OBSOLETO - REQUIERE RECÁLCULO"


def test_marcar_obsoletas_sin_argumento_identifica_y_marca(session):
    expediente = _expediente(session)
    log_viejo = _log_pre_sprint30(session, expediente)
    _log_post_sprint30(session, expediente)

    marcadas = marcar_obsoletas(session)

    assert [log.id for log in marcadas] == [log_viejo.id]
    session.refresh(log_viejo)
    assert log_viejo.obsoleto_requiere_recalculo is True


def test_sprint_30_cierre_coincide_con_el_commit_de_cierre_documentado():
    # docs/Pendientes.md, Sprint 30: "Cierre de implementacion (2026-08-04)";
    # el commit real (5c4cc9a, merge a main) quedo a las 17:15:23 -05:00 --
    # ver git log del worktree. Cualquier liquidacion de ese mismo dia antes
    # de esa hora todavia pudo calcularse con la logica vieja.
    assert SPRINT_30_CIERRE == datetime(2026, 8, 4, 17, 15, 23)


# ---------------------------------------------------------------------------
# Log de diferencias
# ---------------------------------------------------------------------------


def _item(fecha: date, monto: Decimal) -> LiquidationItem:
    return LiquidationItem(
        date=fecha,
        concept="Rubro",
        capital_base=monto,
        interest_rate=Decimal("0.00"),
        interest_amount=Decimal("0.00"),
        indexation_amount=Decimal("0.00"),
        payment_amount=Decimal("0.00"),
        balance=RunningBalance(
            date=fecha,
            debt=PendingDebt(monto, Decimal("0.00"), Decimal("0.00")),
            event_type="INSTALLMENT",
        ),
    )


def test_calcular_diferencia_reporta_monto_y_dias(session):
    # anterior: 1 solo item -> dias_cubiertos = 1.
    anterior = _resultado(Decimal("7830000.00"), fecha=date(2020, 12, 30))
    # nuevo: 2 items en fechas distintas (2020-12-28 a 2020-12-31) -> rango de
    # 4 dias inclusive -- distinto del anterior a proposito, para verificar
    # que calcular_diferencia SI detecta la diferencia de dias cubiertos.
    nuevo = LiquidationResult(
        items=[
            _item(date(2020, 12, 28), Decimal("8000000.00")),
            _item(date(2020, 12, 31), Decimal("8000000.00")),
        ]
    )

    diferencia = calcular_diferencia(
        anterior, nuevo, audit_log_anterior_id=1, audit_log_nuevo_id=2
    )

    assert diferencia.monto_anterior == Decimal("7830000.00")
    assert diferencia.monto_recalculado == Decimal("8000000.00")
    assert diferencia.diferencia_monto == Decimal("170000.00")
    assert diferencia.dias_cubiertos_anterior == 1
    assert diferencia.dias_cubiertos_recalculado == 4  # 2020-12-28 a 2020-12-31 inclusive
    assert diferencia.diferencia_dias == 3
    assert diferencia.resumen_texto == "Diferencia recuperada: +3 días / +$170,000.00 pesos"


def test_calcular_diferencia_sin_diferencia_de_dias_omite_esa_parte_del_resumen():
    anterior = _resultado(Decimal("7830000.00"), fecha=date(2020, 12, 31))
    nuevo = _resultado(Decimal("7860000.00"), fecha=date(2020, 12, 31))

    diferencia = calcular_diferencia(anterior, nuevo, audit_log_anterior_id=1)

    assert diferencia.diferencia_dias == 0
    assert diferencia.resumen_texto == "Diferencia recuperada: +$30,000.00 pesos"


def test_calcular_diferencia_con_disminucion_reporta_signo_negativo():
    anterior = _resultado(Decimal("8000000.00"), fecha=date(2020, 12, 31))
    nuevo = _resultado(Decimal("7860000.00"), fecha=date(2020, 12, 31))

    diferencia = calcular_diferencia(anterior, nuevo, audit_log_anterior_id=1)

    assert diferencia.diferencia_monto == Decimal("-140000.00")
    assert diferencia.resumen_texto == "Diferencia recuperada: -$140,000.00 pesos"


# ---------------------------------------------------------------------------
# Recalculo (liquidacion nueva vinculada a la anterior)
# ---------------------------------------------------------------------------


def test_recalcular_liquidacion_crea_fila_nueva_vinculada_sin_sobrescribir_la_anterior(session):
    expediente = _expediente(session)
    obligacion = _obligacion_laboral(expediente.id)
    session.add(obligacion)
    session.flush()

    log_viejo = _log_pre_sprint30(session, expediente, monto=Decimal("7830000.00"))
    resultado_json_original = log_viejo.resultado_json

    nuevo_log, diferencia = recalcular_liquidacion(session, log_viejo)

    # La fila vieja NUNCA se sobrescribe -- mismo resultado_json de antes,
    # solo se le agrega el flag/motivo de obsoleta.
    assert log_viejo.resultado_json == resultado_json_original
    assert log_viejo.obsoleto_requiere_recalculo is True
    assert log_viejo.motivo_recalculo == FLAG_OBSOLETO

    # La fila nueva es un registro AuditLog distinto, vinculado a la vieja.
    assert nuevo_log.id != log_viejo.id
    assert nuevo_log.liquidacion_anterior_id == log_viejo.id
    assert nuevo_log.expediente_id == expediente.id
    assert nuevo_log.area_derecho == "LABORAL"

    # Recalculado con la logica ACTUAL (post-Sprint-30): mismo valor que
    # tests/services/test_area_strategy.py::TestLaboralStrategy para este
    # mismo contrato (cesantias 3000000 + intereses 360000 + prima x2
    # 3000000 + vacaciones 1500000 = 7860000.00).
    assert diferencia.monto_recalculado == Decimal("7860000.00")
    assert diferencia.monto_anterior == Decimal("7830000.00")
    assert diferencia.diferencia_monto == Decimal("30000.00")
    assert "30,000.00" in diferencia.resumen_texto

    assert session.query(AuditLog).count() == 2


def test_recalcular_liquidacion_propio_registro_de_auditoria_con_usuario(session):
    expediente = _expediente(session)
    obligacion = _obligacion_laboral(expediente.id)
    session.add(obligacion)
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)

    nuevo_log, _diferencia = recalcular_liquidacion(session, log_viejo, usuario="paralegal-1")

    assert nuevo_log.usuario == "paralegal-1"
    assert "Recálculo Sprint 30" in nuevo_log.motivo_recalculo
    assert str(log_viejo.id) in nuevo_log.motivo_recalculo


def test_recalcular_liquidacion_cosa_juzgada_lanza_y_no_crea_fila_nueva(session):
    # Code review Critical #1 (Sprint 47): la restriccion "nunca recalcular
    # cosa juzgada" tiene que vivir en la funcion que ESCRIBE datos, no solo
    # en el script de orquestacion (scripts/recalcular_historicas_sprint30.py)
    # ni en la generacion de memoriales (app/engine/reports/memoriales.py) --
    # ambos corren DESPUES de que recalcular_liquidacion ya habria escrito la
    # fila AuditLog nueva. Este test llama recalcular_liquidacion
    # DIRECTAMENTE, sin pasar por ningun script/orquestador, para probar que
    # la garantia es real sin importar el llamador.
    expediente = _expediente(session, radicado="2026-00502", estado=EstadoProcesal.COSA_JUZGADA)
    obligacion = _obligacion_laboral(expediente.id)
    session.add(obligacion)
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)

    conteo_audit_logs_antes = session.query(AuditLog).count()

    with pytest.raises(CosaJuzgadaNoRecalculableError, match="cosa juzgada"):
        recalcular_liquidacion(session, log_viejo)

    # Ninguna fila AuditLog nueva se creo -- la funcion lanzo ANTES de llamar
    # a registrar_liquidacion, no despues de crearla y luego "deshacerla".
    assert session.query(AuditLog).count() == conteo_audit_logs_antes

    # La fila vieja tampoco quedo tocada de ninguna forma (ni marcada
    # obsoleta ni vinculada) -- esta funcion no escribe NADA en el caso de
    # cosa juzgada, el marcado (si aplica) es responsabilidad explicita de
    # otro llamador (ver marcar_obsoletas / procesar_liquidacion).
    session.refresh(log_viejo)
    assert log_viejo.obsoleto_requiere_recalculo is False
    assert log_viejo.liquidacion_anterior_id is None
    assert log_viejo.motivo_recalculo is None


def test_recalcular_liquidacion_en_tramite_y_cpaca_si_recalculan(session):
    # Contraste directo con el test de arriba: EN_TRAMITE y
    # PRESENTADO_JUZGADO_CPACA (los otros 2 valores de EstadoProcesal) SI
    # deben poder recalcularse sin excepcion -- solo COSA_JUZGADA bloquea.
    for estado, radicado in (
        (EstadoProcesal.EN_TRAMITE, "2026-00503"),
        (EstadoProcesal.PRESENTADO_JUZGADO_CPACA, "2026-00504"),
    ):
        expediente = _expediente(session, radicado=radicado, estado=estado)
        session.add(_obligacion_laboral(expediente.id))
        session.flush()
        log_viejo = _log_pre_sprint30(session, expediente)

        nuevo_log, diferencia = recalcular_liquidacion(session, log_viejo)

        assert nuevo_log.liquidacion_anterior_id == log_viejo.id
        assert diferencia.monto_recalculado == Decimal("7860000.00")


# ---------------------------------------------------------------------------
# Protocolo por estado procesal
# ---------------------------------------------------------------------------


def test_accion_por_estado_procesal_mapea_los_3_valores_del_protocolo():
    assert (
        accion_por_estado_procesal(EstadoProcesal.EN_TRAMITE)
        == ACCION_RECALCULAR_MEMORIAL_ACTUALIZACION
    )
    assert (
        accion_por_estado_procesal(EstadoProcesal.PRESENTADO_JUZGADO_CPACA)
        == ACCION_RECALCULAR_MEMORIAL_ERROR_ARITMETICO
    )
    assert (
        accion_por_estado_procesal(EstadoProcesal.COSA_JUZGADA)
        == ACCION_NO_RECALCULAR_COSA_JUZGADA
    )


# ---------------------------------------------------------------------------
# Priorizacion por cercania de prescripcion
# ---------------------------------------------------------------------------


@pytest.fixture
def _parametro_prescripcion_ejecutiva(session):
    session.add(
        ParametroLegal(
            clave="PRESCRIPCION_EJECUTIVA_MESES",
            valor=Decimal("60"),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime(2020, 1, 1),
        )
    )
    session.commit()


def test_dias_para_prescribir_usa_el_motor_existente(session, _parametro_prescripcion_ejecutiva):
    expediente = _expediente(session)
    obligacion = _obligacion_laboral(
        expediente.id, fecha_inicio=date(2020, 1, 1), fecha_fin=date(2020, 6, 1)
    )
    session.add(obligacion)
    session.flush()

    fecha_referencia = date(2025, 1, 1)
    dias = dias_para_prescribir(session, expediente, fecha_referencia=fecha_referencia)

    fecha_limite_esperada = calcular_prescripcion(date(2020, 1, 1), TipoAccion.EJECUTIVA)
    assert dias == (fecha_limite_esperada - fecha_referencia).days


def test_dias_para_prescribir_sin_obligaciones_devuelve_none(session):
    expediente = _expediente(session)

    assert dias_para_prescribir(session, expediente, date(2026, 1, 1)) is None


def test_priorizar_recalculo_prioriza_los_que_prescriben_en_menos_de_30_dias(
    session, _parametro_prescripcion_ejecutiva
):
    # fecha_referencia se elige a partir de calcular_prescripcion real (no
    # una fecha limite adivinada a mano) para que el test no dependa de
    # asumir de memoria el calendario de festivos/corrimiento de
    # CalendarUtils.vencimiento_calendario.
    fecha_origen_urgente = date(2019, 1, 15)
    fecha_limite_urgente = calcular_prescripcion(fecha_origen_urgente, TipoAccion.EJECUTIVA)
    fecha_referencia = fecha_limite_urgente - timedelta(days=15)  # < 30 dias, "urgente"

    fecha_origen_lejano = date(2024, 1, 1)
    fecha_limite_lejano = calcular_prescripcion(fecha_origen_lejano, TipoAccion.EJECUTIVA)
    assert (fecha_limite_lejano - fecha_referencia).days > 30  # confirma que SI queda lejos

    expediente_lejano = _expediente(session, radicado="2026-00600")
    session.add(
        _obligacion_laboral(
            expediente_lejano.id, fecha_inicio=fecha_origen_lejano, fecha_fin=date(2024, 6, 1)
        )
    )
    expediente_urgente = _expediente(session, radicado="2026-00601")
    session.add(
        _obligacion_laboral(
            expediente_urgente.id, fecha_inicio=fecha_origen_urgente, fecha_fin=date(2019, 6, 1)
        )
    )
    session.flush()

    log_lejano = _log_pre_sprint30(session, expediente_lejano)
    log_urgente = _log_pre_sprint30(session, expediente_urgente)

    priorizados = priorizar_recalculo(
        session, [log_lejano, log_urgente], fecha_referencia=fecha_referencia
    )

    assert [log.id for log in priorizados] == [log_urgente.id, log_lejano.id]


def test_priorizar_recalculo_manda_al_final_los_que_no_tienen_fecha_resoluble(session):
    expediente_sin_obligaciones = _expediente(session, radicado="2026-00700")
    expediente_con_obligacion = _expediente(session, radicado="2026-00701")
    session.add(
        _obligacion_laboral(
            expediente_con_obligacion.id, fecha_inicio=date(2019, 1, 1), fecha_fin=date(2019, 6, 1)
        )
    )
    session.flush()

    log_sin_obligaciones = _log_pre_sprint30(session, expediente_sin_obligaciones)
    log_con_obligacion = _log_pre_sprint30(session, expediente_con_obligacion)

    # Sin PRESCRIPCION_EJECUTIVA_MESES configurado, dias_para_prescribir
    # siempre devuelve None (ParametroNoDisponibleError) -- ambos deberian
    # quedar empatados al final, pero el que sí tiene una obligacion (aunque
    # no resoluble por falta de parametro) no debe reventar el ordenamiento.
    priorizados = priorizar_recalculo(
        session, [log_con_obligacion, log_sin_obligaciones], fecha_referencia=date(2026, 1, 1)
    )

    assert {log.id for log in priorizados} == {log_con_obligacion.id, log_sin_obligaciones.id}
