from datetime import date, datetime
from decimal import Decimal

import pytest
from docx import Document

import database.session as session_module
from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.models import LiquidationItem, PendingDebt, RunningBalance
from app.engine.liquidation.result import LiquidationResult
from app.engine.reports.memoriales import (
    TIPO_ACTUALIZACION,
    TIPO_ERROR_ARITMETICO_CPACA,
    CosaJuzgadaNoRecalculableError,
    generar_memorial,
    tipo_memorial_por_estado_procesal,
)
from app.services.recalculo_historico import recalcular_liquidacion
from database.models import (
    AreaDerecho,
    EstadoProcesal,
    Expediente,
    Obligacion,
    TipoObligacion,
)


@pytest.fixture
def session():
    s = session_module.get_session()
    yield s
    s.close()


def _expediente(session, estado: EstadoProcesal, radicado="2026-00900") -> Expediente:
    expediente = Expediente(
        radicado=radicado,
        demandante="Ana Perez",
        demandado="Luis Gomez",
        area_derecho=AreaDerecho.LABORAL,
        juzgado="Juzgado 3 Laboral del Circuito",
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


def _log_pre_sprint30(session, expediente) -> object:
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


def _preparar_recalculo(session, estado: EstadoProcesal, radicado="2026-00900"):
    expediente = _expediente(session, estado, radicado)
    session.add(_obligacion_laboral(expediente.id))
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)
    log_nuevo, diferencia = recalcular_liquidacion(session, log_viejo)
    return expediente, log_viejo, log_nuevo, diferencia


def test_tipo_memorial_por_estado_procesal_mapea_en_tramite_y_cpaca():
    assert tipo_memorial_por_estado_procesal(EstadoProcesal.EN_TRAMITE) == TIPO_ACTUALIZACION
    assert (
        tipo_memorial_por_estado_procesal(EstadoProcesal.PRESENTADO_JUZGADO_CPACA)
        == TIPO_ERROR_ARITMETICO_CPACA
    )


def test_tipo_memorial_por_estado_procesal_cosa_juzgada_lanza_excepcion():
    with pytest.raises(CosaJuzgadaNoRecalculableError, match="cosa juzgada"):
        tipo_memorial_por_estado_procesal(EstadoProcesal.COSA_JUZGADA)


def test_generar_memorial_actualizacion_para_expediente_en_tramite(session, tmp_path):
    expediente, log_viejo, log_nuevo, diferencia = _preparar_recalculo(
        session, EstadoProcesal.EN_TRAMITE, radicado="2026-00901"
    )
    ruta = tmp_path / "memorial_actualizacion.pdf"

    resultado = generar_memorial(
        session,
        expediente,
        log_viejo,
        log_nuevo,
        diferencia,
        ruta_salida=str(ruta),
        formato="pdf",
    )

    assert resultado == str(ruta)
    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_generar_memorial_error_aritmetico_para_expediente_presentado_cpaca(session, tmp_path):
    expediente, log_viejo, log_nuevo, diferencia = _preparar_recalculo(
        session, EstadoProcesal.PRESENTADO_JUZGADO_CPACA, radicado="2026-00902"
    )
    ruta = tmp_path / "memorial_error_aritmetico.docx"

    generar_memorial(
        session,
        expediente,
        log_viejo,
        log_nuevo,
        diferencia,
        ruta_salida=str(ruta),
        formato="word",
    )

    documento = Document(str(ruta))
    texto_completo = "\n".join(p.text for p in documento.paragraphs)
    assert "MEMORIAL DE CORRECCIÓN DE ERROR ARITMÉTICO (ART. 151 CPACA)" in texto_completo
    assert "artículo 151" in texto_completo
    assert f"AuditLog #{log_viejo.id}" in texto_completo
    assert "Radicado: 2026-00902" in texto_completo
    assert diferencia.resumen_texto in texto_completo


def test_preparar_recalculo_cosa_juzgada_ya_falla_en_recalcular_liquidacion(session):
    # Sprint 47, code review Critical #1: recalcular_liquidacion (la capa que
    # escribe AuditLog) ahora se niega a recalcular un expediente en cosa
    # juzgada por si sola -- ni siquiera llega a existir un log_nuevo/
    # diferencia para pasarle a generar_memorial. Antes de este fix, este
    # helper SI lograba recalcular (silenciosamente, sin ningun guardian) y
    # solo generar_memorial bloqueaba, DESPUES de que la fila ya se habia
    # escrito -- ver test_recalculo_historico.py para el test directo de
    # esa garantia (sin pasar por este modulo de reportes en absoluto).
    expediente = _expediente(session, EstadoProcesal.COSA_JUZGADA, "2026-00903")
    session.add(_obligacion_laboral(expediente.id))
    session.flush()
    log_viejo = _log_pre_sprint30(session, expediente)

    with pytest.raises(CosaJuzgadaNoRecalculableError):
        recalcular_liquidacion(session, log_viejo)


def test_generar_memorial_cosa_juzgada_no_genera_archivo_ni_confia_en_tipo_explicito(
    session, tmp_path
):
    # Defensa en profundidad de generar_memorial: aunque alguien lograra
    # construir un log_nuevo/diferencia validos (de OTRO expediente) y los
    # pasara junto con un `expediente` en cosa juzgada -- p.ej. un bug de
    # otro llamador que mezcle datos, o el `tipo=` forzado explicitamente --
    # generar_memorial se niega igual, sin generar ningun archivo.
    _expediente_valido, log_viejo, log_nuevo, diferencia = _preparar_recalculo(
        session, EstadoProcesal.EN_TRAMITE, radicado="2026-00906"
    )
    expediente_cosa_juzgada = _expediente(session, EstadoProcesal.COSA_JUZGADA, "2026-00903")
    ruta = tmp_path / "memorial_cosa_juzgada.pdf"

    with pytest.raises(CosaJuzgadaNoRecalculableError):
        generar_memorial(
            session,
            expediente_cosa_juzgada,
            log_viejo,
            log_nuevo,
            diferencia,
            ruta_salida=str(ruta),
            formato="pdf",
            tipo=TIPO_ACTUALIZACION,
        )

    assert not ruta.exists()


def test_generar_memorial_con_tipo_explicito_ignora_estado_procesal(session, tmp_path):
    # Permite al llamador forzar el tipo (p.ej. una UI que ya pregunto al
    # abogado) sin tener que mutar expediente.estado_procesal primero.
    expediente, log_viejo, log_nuevo, diferencia = _preparar_recalculo(
        session, EstadoProcesal.EN_TRAMITE, radicado="2026-00904"
    )
    ruta = tmp_path / "memorial_forzado.pdf"

    generar_memorial(
        session,
        expediente,
        log_viejo,
        log_nuevo,
        diferencia,
        ruta_salida=str(ruta),
        formato="pdf",
        tipo=TIPO_ERROR_ARITMETICO_CPACA,
    )

    assert ruta.exists()


def test_generar_memorial_formato_desconocido_lanza_value_error(session, tmp_path):
    expediente, log_viejo, log_nuevo, diferencia = _preparar_recalculo(
        session, EstadoProcesal.EN_TRAMITE, radicado="2026-00905"
    )

    with pytest.raises(ValueError, match="Formato de memorial desconocido"):
        generar_memorial(
            session,
            expediente,
            log_viejo,
            log_nuevo,
            diferencia,
            ruta_salida=str(tmp_path / "x.pdf"),
            formato="excel",
        )
