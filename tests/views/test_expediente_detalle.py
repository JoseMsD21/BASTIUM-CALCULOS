from datetime import date, datetime
from decimal import Decimal

from PySide6.QtWidgets import QMessageBox
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.database as database_module
import database.session as session_module
from app.engine.audit.service import registrar_liquidacion
from app.engine.indexation.historical_index import _IPC_INDICE_ACUMULADO
from app.engine.liquidation.registry import AreaRegistry
from app.services.reajuste_anual import generar_cuotas_mensuales
from app.views.expediente_detalle import ExpedienteDetallePage
from database.models import (
    AreaDerecho,
    Base,
    Beneficiario,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoBeneficiario,
    TipoObligacion,
)


def _expediente_con_obligacion(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-030",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Gastos medicos",
            categoria="DANO_EMERGENTE",
            fecha_origen=date(2025, 11, 20),
            valor=Decimal("427900.00"),
            tasa_efectiva_anual=Decimal("6.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_cargar_expediente_muestra_sus_obligaciones(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.tabla_obligaciones.rowCount() == 1
    assert page.tabla_obligaciones.item(0, 0).text() == "Gastos medicos"


def test_liquidar_invoca_callback_con_resultado(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")


def _expediente_comercial_con_obligacion_usuraria(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="USURA_MULTIPLICADOR",
            valor=Decimal("1.5"),
            vigente_desde=date(1997, 7, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    expediente = Expediente(
        radicado="2026-040",
        demandante="Comercial SAS",
        demandado="Deudor SAS",
        area_derecho=AreaDerecho.COMERCIAL,
        fecha_corte_default=date(2025, 3, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Capital de pagare",
            categoria="CAPITAL_PAGARE",
            fecha_origen=date(2025, 1, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            tasa_moratoria_anual=Decimal("35.00"),
            fecha_vencimiento=date(2025, 2, 1),
            ibc_vigente_anual=Decimal("20.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _expediente_civil_con_obligacion_indexada(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    # Tarea 12: CivilFamiliaStrategy ahora resuelve el indice IPC via
    # get_ipc_interpolado_for_date -> parametro_service, en vez del diccionario
    # en memoria de historical_index.py -- se siembra IPC_INDICE_ACUMULADO
    # completo desde el mismo diccionario congelado que usa
    # scripts/migrate_parametros_legales.py, para no re-transcribir a mano.
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(
            ParametroLegal(
                clave="IPC_INDICE_ACUMULADO",
                valor=valor,
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=datetime.now(),
            )
        )
    expediente = Expediente(
        radicado="2026-070",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2025, 12, 31),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Dano emergente",
            categoria="DANO_EMERGENTE",
            fecha_origen=date(2024, 7, 1),
            valor=Decimal("1000000.00"),
            tasa_efectiva_anual=Decimal("6.00"),
            aplica_indexacion_ipc=True,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_civil_con_indexacion_ipc_incluye_evento_de_indexacion(qtbot, monkeypatch):
    expediente_id = _expediente_civil_con_obligacion_indexada(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id

    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "INDEXATION" in tipos_evento
    assert resultado.final_balance().indexation == Decimal("77633.53")


def test_liquidar_area_comercial_con_tasa_usuraria_no_muestra_advertencia_y_aplica_sancion(
    qtbot, monkeypatch
):
    # Respuesta del despacho (docs/Preguntas-Para-Abogado-Respondidas.md, Sprint 2): una
    # tasa por encima de la usura ya no rechaza la liquidacion -- se liquida igual y se
    # aplica la sancion legal (perdida doblada del exceso) como un rubro mas del resultado.
    expediente_id = _expediente_comercial_con_obligacion_usuraria(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert len(avisos) == 0
    assert len(resultados_recibidos) == 1
    resultado, _exp_id = resultados_recibidos[0]
    assert "usura" in resultado.items[-1].concept.lower()


def _expediente_honorarios_con_cuota_litis_excesiva(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="HONORARIOS_TOTAL_PCT",
            valor=Decimal("50"),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    expediente = Expediente(
        radicado="2026-050",
        demandante="Abogado",
        demandado="Cliente",
        area_derecho=AreaDerecho.HONORARIOS,
        fecha_corte_default=date(2026, 1, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Honorarios proceso ejecutivo",
            categoria="HONORARIOS_PROFESIONALES",
            fecha_origen=date(2026, 1, 1),
            valor=Decimal("0.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            honorarios_fijos_pactados=Decimal("1000000.00"),
            cuota_litis_pactada_pct=Decimal(
                "45.00"
            ),  # total (1M + 4.5M = 5.5M) excede el 50% (5M)
            beneficio_obtenido=Decimal("10000000.00"),
            costas_pct_manual=Decimal("5.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _expediente_sancionatorio_con_hecho_posterior_a_2026(monkeypatch) -> int:
    """
    Siembra la tabla historica UVT real (via scripts.migrate_parametros_legales.migrar(),
    mismo patron que tests/engine/test_historical_index.py) para que el hecho de 2027
    genuinamente quede fuera de rango (la serie historica cubre 2006-2026), en vez de
    que la resolucion falle solo porque la BD en memoria esta vacia.
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    from scripts.migrate_parametros_legales import migrar

    migrar()

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-051",
        demandante="Estado",
        demandado="Empresa XYZ",
        area_derecho=AreaDerecho.SANCIONATORIO,
        fecha_corte_default=date(2027, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Multa SIC",
            categoria="MULTA_SANCIONATORIA",
            # posterior a 2026: fuera del rango de la tabla historica UVT (2006-2026),
            # aun no publicada por la DIAN
            fecha_origen=date(2027, 1, 1),
            valor=Decimal("0.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            cantidad_smlmv_uvt=Decimal("2"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_honorarios_con_cuota_litis_excesiva_muestra_advertencia_sin_crash(
    qtbot, monkeypatch
):
    """
    Regresion: CuotaLitisExcedeTopeError (agregada en Sprint 4) no estaba en la lista de
    except de _liquidar(), asi que se propagaba como traceback no controlado en vez de
    mostrarse como advertencia amigable, igual que AreaNoImplementadaError/UVTNoDisponibleError.
    """
    expediente_id = _expediente_honorarios_con_cuota_litis_excesiva(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "Cuota litis excede el tope"


def test_liquidar_area_sancionatorio_con_hecho_posterior_a_2026_muestra_advertencia_sin_crash(
    qtbot, monkeypatch
):
    """
    Regresion: UVTNoDisponibleError (agregada en Sprint 4) no estaba en la lista de except
    de _liquidar(), asi que se propagaba como traceback no controlado en vez de mostrarse
    como advertencia amigable, igual que CuotaLitisExcedeTopeError.

    Sprint 14 agrego la tabla historica UVT (2006-2026) y desbloqueo la conversion real
    via UVT para hechos sancionatorios en ese rango, asi que este test siembra esa tabla
    real (via migrar()) y usa un hecho de 2027 -- genuinamente fuera de rango -- para
    seguir probando la ruta de UVTNoDisponibleError sin depender de que la BD este vacia.
    """
    expediente_id = _expediente_sancionatorio_con_hecho_posterior_a_2026(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "UVT no disponible"


def _expediente_tributario_sin_parametros_de_sancion(monkeypatch) -> int:
    """
    DB en memoria SIN sembrar ningun ParametroLegal -- reproduce el escenario real de un
    bastium.db donde EXTEMPORANEIDAD_PCT_MENSUAL (u otro parametro ABIERTO cualquiera)
    todavia no fue sembrado. get_parametro() debe lanzar ParametroNoDisponibleError, y
    _liquidar() debe mostrarlo como advertencia amigable, no como traceback sin control.
    """
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-060",
        demandante="DIAN",
        demandado="Contribuyente XYZ",
        area_derecho=AreaDerecho.TRIBUTARIO,
        fecha_corte_default=date(2024, 3, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Sancion extemporaneidad renta 2024",
            categoria="SANCION_EXTEMPORANEIDAD",
            fecha_origen=date(2024, 3, 1),
            valor=Decimal("0.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            base_sancion_tributaria=Decimal("10000000.00"),
            meses_extemporaneidad=2,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_tributaria_sin_parametros_de_sancion_muestra_advertencia_sin_crash(
    qtbot, monkeypatch
):
    """
    Regresion: ParametroNoDisponibleError no estaba en la lista de except de _liquidar(),
    asi que un parametro ABIERTO no sembrado (ej. EXTEMPORANEIDAD_PCT_MENSUAL, si alguna
    vez se agrega uno nuevo sin sembrarlo) se propagaria como traceback no controlado en
    vez de mostrarse como advertencia amigable, igual que los demas errores de dominio.
    """
    expediente_id = _expediente_tributario_sin_parametros_de_sancion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "Parámetro legal no configurado"


def test_liquidar_registra_auditoria_y_refresca_historial(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert page.tabla_historial.rowCount() == 1
    assert page.tabla_historial.item(0, 2).text() == "CIVIL_FAMILIA"
    assert page.tabla_historial.item(0, 3).text() == "2026-06-01"


def test_abrir_dialogo_obligacion_pasa_el_area_del_expediente(qtbot, monkeypatch):
    expediente_id = _expediente_comercial_con_obligacion_usuraria(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    dialogos_creados = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.ObligacionFormDialog",
        lambda expediente_id, area, parent: dialogos_creados.append(area) or _DialogStub(),
    )

    page._abrir_dialogo_obligacion()

    assert dialogos_creados == ["COMERCIAL"]


class _DialogStub:
    def exec(self):
        return False


def _expediente_laboral_con_mora_fase1(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-060",
        demandante="Trabajador",
        demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL,
        # ~152 dias despues de fecha_fin (2020-12-31): mora solo fase 1
        # (muy por debajo del tope de 720 dias de la fase 1).
        fecha_corte_default=date(2021, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Liquidacion de contrato",
            categoria="LIQUIDACION_CONTRATO_LABORAL",
            fecha_origen=date(2020, 1, 1),
            valor=Decimal("3000000.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
            pagada=False,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _expediente_laboral_pagado_a_tiempo(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-061",
        demandante="Trabajador",
        demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2021, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Liquidacion de contrato",
            categoria="LIQUIDACION_CONTRATO_LABORAL",
            fecha_origen=date(2020, 1, 1),
            valor=Decimal("3000000.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
            pagada=True,
            # Pagado el mismo dia de terminacion del contrato: sin mora.
            fecha_pago_total=date(2020, 12, 31),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_laboral_con_mora_incluye_sancion_moratoria(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_con_mora_fase1(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear

    assert len(avisos) == 0
    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id

    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "SANCION_MORATORIA" in tipos_evento
    # Sin mora, las prestaciones (cesantias + intereses + prima x2 + vacaciones)
    # de este contrato liquidan exactamente en 7860000.00 (Sprint 30: conteo
    # inclusivo, base comercial de 360 dias -- ver TestLaboralStrategy en
    # tests/services/test_area_strategy.py). Si el saldo final supera ese
    # monto, la sancion moratoria realmente sumo un valor distinto de cero.
    assert resultado.final_balance().principal > Decimal("7860000.00")


def test_liquidar_area_laboral_con_mora_e_indexacion_ipc_muestra_toast_de_alerta(
    qtbot, monkeypatch
):
    # Sprint 43: cuando la liquidacion trae LiquidationResult.alertas no vacio (ej.
    # "Doble Actualización Prohibida" en Laboral), _on_liquidar_completado debe
    # mostrarlas via mostrar_toast (tipo "warning") -- mismo mecanismo del Sprint 36,
    # no un QMessageBox modal (la liquidacion ya se completo sin bloquear nada).
    expediente_id = _expediente_laboral_con_mora_fase1(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    obligacion.aplica_indexacion_ipc = True
    session.commit()
    session.close()

    toasts_mostrados = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.mostrar_toast",
        lambda parent, mensaje, tipo="success", duracion_ms=3000: toasts_mostrados.append(
            (mensaje, tipo)
        ),
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    assert len(toasts_mostrados) == 1
    mensaje, tipo = toasts_mostrados[0]
    assert "Doble Actualización Prohibida" in mensaje
    assert tipo == "warning"


def test_reconstruir_desde_historial_con_mora_e_indexacion_ipc_muestra_toast_de_alerta(
    qtbot, monkeypatch
):
    # Revision de calidad tras el Sprint 43: el toast de alertas solo se probaba en el
    # camino de liquidacion en vivo (_liquidar) -- _reconstruir_desde_historial (doble
    # clic en una fila del historial de auditoria) usa un camino de codigo distinto
    # (reconstruir_liquidacion -> deserializar_resultado) que tambien debe mostrar las
    # mismas alertas, ahora que LiquidationResult.alertas sobrevive el round-trip de
    # serializacion (commit 1906ebe). Sin este test, una regresion futura en
    # _reconstruir_desde_historial pasaria desapercibida aunque
    # test_liquidar_area_laboral_con_mora_e_indexacion_ipc_muestra_toast_de_alerta
    # (arriba, camino en vivo) siguiera en verde.
    expediente_id = _expediente_laboral_con_mora_fase1(monkeypatch)
    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    obligacion.aplica_indexacion_ipc = True
    session.commit()

    # Corre y registra la liquidacion (mismo flujo que _liquidar(), pero sincrono aqui
    # para no depender del hilo de fondo) -- deja una fila real en AuditLog con
    # alertas ya serializadas, exactamente como quedaria despues de un _liquidar()
    # real.
    obligaciones = list(expediente.obligaciones)
    estrategia = AreaRegistry.get_strategy(expediente.area_derecho.value)
    resultado = estrategia.liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=expediente.fecha_corte_default
    )
    assert resultado.alertas  # confirma que el caso de prueba realmente genera la alerta
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho=expediente.area_derecho.value,
        fecha_corte=expediente.fecha_corte_default,
        resultado=resultado,
        usuario="jsilva",
    )
    session.close()

    toasts_mostrados = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.mostrar_toast",
        lambda parent, mensaje, tipo="success", duracion_ms=3000: toasts_mostrados.append(
            (mensaje, tipo)
        ),
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_historial.rowCount() == 1

    page._reconstruir_desde_historial(0, 0)

    assert len(toasts_mostrados) == 1
    mensaje, tipo = toasts_mostrados[0]
    assert "Doble Actualización Prohibida" in mensaje
    assert tipo == "warning"


def test_liquidar_area_laboral_pagado_a_tiempo_no_incluye_sancion_moratoria(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_pagado_a_tiempo(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar/crashear

    assert len(avisos) == 0
    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id

    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "SANCION_MORATORIA" not in tipos_evento
    # LIQUIDATION_CUTOFF es la fila de cierre que agrega el motor cuando el
    # ultimo evento (fecha_fin) es anterior a fecha_corte -- no es una
    # prestacion, no altera el saldo.
    assert tipos_evento == {
        "CESANTIAS",
        "INTERESES_CESANTIAS",
        "PRIMA_JUNIO",
        "PRIMA_DICIEMBRE",
        "VACACIONES",
        "LIQUIDATION_CUTOFF",
    }
    assert resultado.final_balance().principal == Decimal("7860000.00")


def _expediente_laboral_con_seguridad_social(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-062",
        demandante="Trabajador",
        demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2021, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Liquidacion de contrato",
            categoria="LIQUIDACION_CONTRATO_LABORAL",
            fecha_origen=date(2020, 1, 1),
            valor=Decimal("3000000.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            fecha_inicio=date(2020, 1, 1),
            fecha_fin=date(2020, 12, 31),
            pagada=True,
            fecha_pago_total=date(2020, 12, 31),
            incluir_seguridad_social=True,
            nivel_riesgo_arl="I",
        )
    )
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("877803.00"),
            vigente_desde=date(2020, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    for clave, valor in {
        "SS_PENSION_PCT": Decimal("0.16"),
        "SS_SALUD_PCT": Decimal("0.125"),
        "SS_ARL_NIVEL_I_PCT": Decimal("0.00522"),
    }.items():
        session.add(
            ParametroLegal(
                clave=clave,
                valor=valor,
                vigente_desde=date(1900, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=datetime.now(),
            )
        )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_laboral_con_seguridad_social_no_lanza_detached_instance_error(
    qtbot, monkeypatch
):
    # Regresion: obligacion.eventos_laborales se accede por primera vez dentro
    # de LaboralStrategy.liquidar() (para calcular dias_suspension) cuando
    # incluir_seguridad_social=True. _liquidar() debe forzar ese lazy-load
    # ANTES de session.close(), igual que ya hacia con abonos -- de lo
    # contrario SQLAlchemy lanza DetachedInstanceError en la GUI real (no se
    # ve en tests que usan una Obligacion transiente, nunca adjunta a sesion).
    expediente_id = _expediente_laboral_con_seguridad_social(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar DetachedInstanceError

    assert len(avisos) == 0
    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id

    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "COTIZACION_PENSION" in tipos_evento


def _expediente_civil_familia_con_beneficiario(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-074",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota alimentaria",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 5),
        fecha_inicio=date(2026, 1, 5),
        dia_pago=5,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.flush()
    session.add(
        Beneficiario(
            obligacion_id=obligacion.id,
            nombre="Juan Perez",
            fecha_nacimiento=date(2015, 3, 10),
            tipo=TipoBeneficiario.NINO,
            estudia=False,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_civil_familia_con_beneficiario_no_lanza_detached_instance_error(
    qtbot, monkeypatch
):
    """Sprint 74: obligacion.beneficiario se accede dentro de
    CivilFamiliaStrategy._eventos_de_obligacion (para topar la generacion de
    cuotas por vigencia) -- _liquidar_en_hilo_de_fondo debe forzar ese
    lazy-load ANTES de session.close(), igual que ya hace con
    eventos_laborales/descuentos_laborales, o SQLAlchemy lanza
    DetachedInstanceError en la GUI real."""
    expediente_id = _expediente_civil_familia_con_beneficiario(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()  # no debe lanzar DetachedInstanceError

    assert len(avisos) == 0
    assert len(resultados_recibidos) == 1


def test_cargar_expediente_muestra_historial_de_auditoria_existente(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    obligaciones = list(expediente.obligaciones)
    estrategia = AreaRegistry.get_strategy(expediente.area_derecho.value)
    resultado = estrategia.liquidar(
        obligaciones=obligaciones, abonos=[], fecha_corte=expediente.fecha_corte_default
    )
    registrar_liquidacion(
        session,
        expediente_id=expediente_id,
        area_derecho=expediente.area_derecho.value,
        fecha_corte=expediente.fecha_corte_default,
        resultado=resultado,
        usuario="jsilva",
    )
    session.close()

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.tabla_historial.rowCount() == 1
    assert page.tabla_historial.item(0, 1).text() == "jsilva"
    assert page.tabla_historial.item(0, 2).text() == "CIVIL_FAMILIA"
    assert page.tabla_historial.item(0, 3).text() == "2026-06-01"


def test_doble_clic_en_historial_reconstruye_liquidacion(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
    resultados_recibidos.clear()

    page._reconstruir_desde_historial(0, 0)

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")


def _expediente_laboral_sin_mora(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-070",
        demandante="Trabajador",
        demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL,
        fecha_corte_default=date(2026, 6, 1),
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
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_grupo_eventos_contractuales_visible_solo_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_sin_mora(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_eventos_laborales.isVisible() is True


def test_grupo_eventos_contractuales_oculto_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(
        monkeypatch
    )  # CIVIL_FAMILIA, ya existe en este archivo

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_eventos_laborales.isVisible() is False


def test_refrescar_eventos_laborales_lista_los_eventos_de_todas_las_obligaciones(
    qtbot, monkeypatch
):
    from database.models import EventoLaboral, TipoEventoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        EventoLaboral(
            obligacion_id=obligacion.id,
            tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1),
            fecha_fin=date(2020, 5, 4),
        )
    )
    session.commit()
    session.close()

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    assert pagina.tabla_eventos_laborales.rowCount() == 1


def test_liquidar_deshabilita_el_boton_mientras_esta_en_curso(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.boton_liquidar.isEnabled() is True

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
        assert page.boton_liquidar.isEnabled() is False

    assert page.boton_liquidar.isEnabled() is True


def test_liquidar_ignora_llamada_concurrente_mientras_hay_una_en_curso(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    llamadas = []

    def capturar(resultado, exp_id):
        llamadas.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()
        page._liquidar()  # concurrente -- debe ser ignorada, el boton ya esta deshabilitado

    assert len(llamadas) == 1


def test_boton_liquidar_tiene_clase_primaria(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.boton_liquidar.property("class") == "primary"


def test_botones_agregar_tienen_clase_secundaria(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.boton_agregar_obligacion.property("class") == "secondary"
    assert page.boton_agregar_abono.property("class") == "secondary"
    assert page.boton_agregar_evento_laboral.property("class") == "secondary"
    assert page.boton_agregar_descuento_laboral.property("class") == "secondary"


# --- Sprint 44 -------------------------------------------------------------


def test_fecha_corte_liquidacion_se_precarga_con_la_del_expediente(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)  # fecha_corte_default = 2026-06-01

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.campo_fecha_corte_liquidacion.date().toPython() == date(2026, 6, 1)


def test_override_de_fecha_de_corte_afecta_la_liquidacion_pero_no_el_expediente(
    qtbot, monkeypatch
):
    # _expediente_laboral_con_mora_fase1 tiene fecha_corte_default = 2021-06-01, que
    # produce mora (contrato termina 2020-12-31). Si se cambia el override a la misma
    # fecha de terminacion del contrato (sin mora) y se liquida, el resultado no debe
    # tener SANCION_MORATORIA -- pero fecha_corte_default en la BD debe seguir intacta.
    expediente_id = _expediente_laboral_con_mora_fase1(monkeypatch)

    resultados_recibidos = []

    def capturar(resultado, exp_id):
        resultados_recibidos.append((resultado, exp_id))

    page = ExpedienteDetallePage(on_liquidado=capturar)
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    page.campo_fecha_corte_liquidacion.setDate(date(2020, 12, 31))

    with qtbot.waitSignal(page.liquidacion_finalizada, timeout=5000):
        page._liquidar()

    resultado, _exp_id = resultados_recibidos[0]
    tipos_evento = {item.balance.event_type for item in resultado.items}
    assert "SANCION_MORATORIA" not in tipos_evento
    assert resultado.final_balance().principal == Decimal("7860000.00")

    session = session_module.get_session()
    expediente = session.get(Expediente, expediente_id)
    assert expediente.fecha_corte_default == date(2021, 6, 1)  # sin cambios
    session.close()


def test_grupo_descuentos_laborales_visible_para_area_laboral(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_sin_mora(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_descuentos_laborales.isVisible() is True


def test_grupo_descuentos_laborales_oculto_para_area_civil_familia(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)  # CIVIL_FAMILIA

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_descuentos_laborales.isVisible() is False


def test_refrescar_descuentos_laborales_lista_los_descuentos(qtbot, monkeypatch):
    from database.models import DescuentoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        DescuentoLaboral(
            obligacion_id=obligacion.id,
            fecha=date(2021, 1, 15),
            monto=Decimal("500000.00"),
            es_legal=True,
            motivo="Prestamo",
        )
    )
    session.commit()
    session.close()

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    assert pagina.tabla_descuentos_laborales.rowCount() == 1
    assert pagina.tabla_descuentos_laborales.item(0, 2).text() == "Legal"


def test_abrir_dialogo_descuento_laboral_sin_seleccion_muestra_advertencia(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_sin_mora(monkeypatch)

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._abrir_dialogo_descuento_laboral()

    assert len(avisos) == 1


def test_editar_obligacion_actualiza_la_fila_en_vez_de_agregar_una_nueva(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    obligacion_id = page._obligacion_ids_por_fila[0]

    def _simular_edicion_y_guardado(self):
        self.campo_concepto.setText("Editado")
        self.guardar()
        return True

    monkeypatch.setattr(
        "app.views.expediente_detalle.ObligacionFormDialog.exec",
        _simular_edicion_y_guardado,
    )

    page._editar_obligacion(obligacion_id)

    assert page.tabla_obligaciones.rowCount() == 1  # no se agrego una fila nueva
    assert page.tabla_obligaciones.item(0, 0).text() == "Editado"
    session = session_module.get_session()
    assert session.query(Obligacion).count() == 1
    session.close()


def test_eliminar_evento_laboral_lo_quita_de_la_tabla(qtbot, monkeypatch):
    from database.models import EventoLaboral, TipoEventoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        EventoLaboral(
            obligacion_id=obligacion.id,
            tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1),
            fecha_fin=date(2020, 5, 4),
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_eventos_laborales.rowCount() == 1

    session = session_module.get_session()
    evento_id = session.query(EventoLaboral).filter_by(obligacion_id=obligacion.id).one().id
    session.close()

    page._eliminar_evento_laboral(evento_id)

    assert page.tabla_eventos_laborales.rowCount() == 0
    session = session_module.get_session()
    assert session.query(EventoLaboral).count() == 0
    session.close()


def test_eliminar_evento_laboral_cancelado_no_lo_elimina(qtbot, monkeypatch):
    from database.models import EventoLaboral, TipoEventoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        EventoLaboral(
            obligacion_id=obligacion.id,
            tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
            fecha_inicio=date(2020, 5, 1),
            fecha_fin=date(2020, 5, 4),
        )
    )
    session.commit()
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    session = session_module.get_session()
    evento_id = session.query(EventoLaboral).filter_by(obligacion_id=obligacion.id).one().id
    session.close()

    page._eliminar_evento_laboral(evento_id)

    session = session_module.get_session()
    assert session.query(EventoLaboral).count() == 1
    session.close()


# --- Sprint 41 -------------------------------------------------------------


def _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch) -> tuple[int, int]:
    """Sprint 41: expediente Civil/Familia con una obligacion RECURRENTE con
    tipo_reajuste_anual=SMMLV, lista para 'Generar cuotas' en la UI. Retorna
    (expediente_id, obligacion_id)."""
    from database.models import TipoReajusteAnual

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1000000.00"),
            vigente_desde=date(2024, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1100000.00"),
            vigente_desde=date(2025, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    expediente = Expediente(
        radicado="2026-080",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2025, 3, 5),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2024, 11, 5),
        fecha_inicio=date(2024, 11, 5),
        dia_pago=5,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(obligacion)
    session.commit()
    expediente_id = expediente.id
    obligacion_id = obligacion.id
    session.close()
    return expediente_id, obligacion_id


def _expediente_civil_con_obligacion_recurrente_fechas_fijas(monkeypatch) -> tuple[int, int]:
    """Sprint 73: expediente Civil/Familia con una obligacion RECURRENTE con
    tipo_recurrencia=FECHAS_ANUALES_FIJAS (gastos de vestuario), lista para
    'Generar cuotas' en la UI -- espejo de
    _expediente_civil_con_obligacion_recurrente_con_reajuste (Sprint 41) pero
    para la nueva cadencia. Retorna (expediente_id, obligacion_id)."""
    from app.services.recurrencia_fechas_fijas import serializar_fechas_anuales
    from database.models import TipoRecurrencia

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-081",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2026, 12, 31),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="GASTOS DE VESTUARIO",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2026, 1, 1),
        fecha_inicio=date(2026, 1, 1),
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_recurrencia=TipoRecurrencia.FECHAS_ANUALES_FIJAS,
        fechas_anuales_fijas=serializar_fechas_anuales(["06-15", "12-15", "03-22"]),
    )
    session.add(obligacion)
    session.commit()
    expediente_id = expediente.id
    obligacion_id = obligacion.id
    session.close()
    return expediente_id, obligacion_id


def test_generar_cuotas_dispatcha_a_fechas_fijas_segun_tipo_recurrencia(qtbot, monkeypatch):
    """Definicion de Hecho del Sprint 73, verificada end-to-end a traves del
    boton 'Generar cuotas' (no solo del servicio directamente): una obligacion
    de gastos de vestuario con 3 fechas anuales fijas genera exactamente esas
    3 cuotas -- no las 12 que produciria generar_cuotas_mensuales si el boton
    no supiera distinguir el tipo_recurrencia."""
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_fechas_fijas(
        monkeypatch
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()

    session = session_module.get_session()
    cuotas = (
        session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id).all()
    )
    session.close()
    assert len(cuotas) == 3
    assert {c.fecha_origen for c in cuotas} == {
        date(2026, 3, 22),
        date(2026, 6, 15),
        date(2026, 12, 15),
    }


def test_generar_cuotas_fechas_fijas_dos_veces_no_duplica_filas(qtbot, monkeypatch):
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_fechas_fijas(
        monkeypatch
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()
    primer_conteo = page.tabla_obligaciones.rowCount()

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()

    assert page.tabla_obligaciones.rowCount() == primer_conteo


def test_boton_generar_cuotas_visible_para_civil_familia_y_comercial_oculto_para_otras_areas(
    qtbot, monkeypatch
):
    """Sprint 75 (hallazgo de revision de codigo posterior a Task 3): Comercial ya
    soporta generar_cuotas_mensuales igual que Civil/Familia (ver
    app/services/area_strategy.py::ComercialStrategy._eventos_de_obligacion), asi que
    el boton ya no puede quedar oculto para esa area -- de lo contrario un usuario de
    Comercial no tendria forma de llegar a esa funcionalidad desde la UI. Sigue oculto
    para el resto de areas (Laboral aqui, representativa de las que no soportan cuotas
    recurrentes reajustables)."""
    expediente_id_civil, _ = _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.show()
    page.cargar_expediente(expediente_id_civil)
    assert page.boton_generar_cuotas.isVisible() is True

    expediente_id_comercial = _expediente_comercial_con_obligacion_usuraria(monkeypatch)
    page.cargar_expediente(expediente_id_comercial)
    assert page.boton_generar_cuotas.isVisible() is True

    expediente_id_laboral = _expediente_laboral_sin_mora(monkeypatch)
    page.cargar_expediente(expediente_id_laboral)
    assert page.boton_generar_cuotas.isVisible() is False


def test_generar_cuotas_sin_seleccion_muestra_advertencia(qtbot, monkeypatch):
    expediente_id, _obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(
        monkeypatch
    )

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._generar_cuotas()

    assert len(avisos) == 1
    assert avisos[0][0] == "Seleccion requerida"


def test_generar_cuotas_persiste_y_refresca_la_tabla_de_obligaciones(qtbot, monkeypatch):
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(
        monkeypatch
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    assert page.tabla_obligaciones.rowCount() == 1  # solo la obligacion RECURRENTE padre

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()

    # Nov/Dic 2024 (2) + Ene..Mar 2025 (3) = 5 cuotas + la obligacion padre = 6 filas.
    assert page.tabla_obligaciones.rowCount() == 6

    session = session_module.get_session()
    total_cuotas = (
        session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id).count()
    )
    session.close()
    assert total_cuotas == 5


def test_generar_cuotas_dos_veces_no_duplica_filas(qtbot, monkeypatch):
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(
        monkeypatch
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()
    primer_conteo = page.tabla_obligaciones.rowCount()

    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()

    assert page.tabla_obligaciones.rowCount() == primer_conteo


def test_generar_cuotas_sobre_obligacion_sin_reajuste_muestra_advertencia(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)  # PUNTUAL, sin reajuste

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.warning",
        lambda parent, titulo, mensaje: avisos.append((titulo, mensaje)),
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    page.tabla_obligaciones.setCurrentCell(0, 0)

    page._generar_cuotas()

    assert len(avisos) == 1
    assert avisos[0][0] == "No se pudo generar cuotas"


def test_boton_generar_cuotas_tiene_clase_secundaria(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.boton_generar_cuotas.property("class") == "secondary"


def test_flujo_completo_crear_obligacion_recurrente_generar_cuotas_y_abonar_una_cuota(
    qtbot, monkeypatch
):
    """Flujo completo del Sprint 41 (Task 4): crear una obligacion RECURRENTE con
    reajuste anual desde el formulario real (ObligacionFormDialog) -> generar
    cuotas desde ExpedienteDetallePage -> verlas en la tabla de Obligaciones ->
    agregar un abono a UNA cuota especifica (no a la obligacion padre),
    reutilizando AbonoFormDialog tal cual, sin ningun campo nuevo en Abono."""
    from app.views.abonos import AbonoFormDialog
    from app.views.obligaciones import ObligacionFormDialog
    from database.models import Abono

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1000000.00"),
            vigente_desde=date(2024, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="SMLMV",
            valor=Decimal("1100000.00"),
            vigente_desde=date(2025, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    expediente = Expediente(
        radicado="2026-090",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2025, 2, 5),
    )
    session.add(expediente)
    session.commit()
    expediente_id = expediente.id
    session.close()

    # 1. Crear la obligacion RECURRENTE con reajuste SMMLV desde el formulario real.
    dialogo_obligacion = ObligacionFormDialog(expediente_id=expediente_id, area="CIVIL_FAMILIA")
    qtbot.addWidget(dialogo_obligacion)
    dialogo_obligacion.combo_tipo.setCurrentIndex(1)  # RECURRENTE
    dialogo_obligacion.campo_concepto.setText("CUOTA ALIMENTARIA")
    dialogo_obligacion.campo_valor.setText("500000.00")
    dialogo_obligacion.campo_tasa.setText("6.00")
    dialogo_obligacion.campo_fecha_inicio.setDate(date(2024, 11, 5))
    dialogo_obligacion.campo_dia_pago.setValue(5)
    indice_smmlv = dialogo_obligacion.combo_tipo_reajuste_anual.findData("SMMLV")
    dialogo_obligacion.combo_tipo_reajuste_anual.setCurrentIndex(indice_smmlv)
    dialogo_obligacion.guardar()

    # 2. Abrir el expediente y generar las cuotas desde la pagina real.
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_obligaciones.rowCount() == 1  # solo la obligacion padre, todavia

    page.tabla_obligaciones.setCurrentCell(0, 0)
    page._generar_cuotas()

    # Nov/Dic 2024 (2) + Ene/Feb 2025 (2) = 4 cuotas + la obligacion padre = 5 filas.
    assert page.tabla_obligaciones.rowCount() == 5
    for fila in range(1, 5):
        assert page.tabla_obligaciones.item(fila, 0).text().startswith("CUOTA ALIMENTARIA DE")

    # 3. Agregar un abono a la PRIMERA cuota (fila 1, no la obligacion padre de la fila 0).
    fila_primera_cuota = 1
    cuota_id = page._obligacion_ids_por_fila[fila_primera_cuota]
    obligacion_padre_id = page._obligacion_ids_por_fila[0]
    assert cuota_id != obligacion_padre_id

    page.tabla_obligaciones.setCurrentCell(fila_primera_cuota, 0)
    dialogo_abono = AbonoFormDialog(obligacion_id=cuota_id)
    qtbot.addWidget(dialogo_abono)
    dialogo_abono.campo_monto.setText("50000.00")
    dialogo_abono.campo_referencia.setText("Transferencia parcial")
    dialogo_abono.guardar()

    session = session_module.get_session()
    abono_guardado = session.query(Abono).filter_by(obligacion_id=cuota_id).one()
    assert abono_guardado.monto == Decimal("50000.00")
    # El abono quedo atado a la cuota especifica, no a la obligacion RECURRENTE padre.
    abonos_del_padre = session.query(Abono).filter_by(obligacion_id=obligacion_padre_id).count()
    session.close()
    assert abonos_del_padre == 0


# --- Sprint 60 ---------------------------------------------------------------


def test_eliminar_obligacion_simple_la_quita_de_la_tabla_y_la_base(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_obligaciones.rowCount() == 1
    obligacion_id = page._obligacion_ids_por_fila[0]

    page._eliminar_obligacion(obligacion_id)

    assert page.tabla_obligaciones.rowCount() == 0
    session = session_module.get_session()
    assert session.query(Obligacion).count() == 0
    session.close()


def test_eliminar_obligacion_cancelada_no_la_elimina(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    obligacion_id = page._obligacion_ids_por_fila[0]

    page._eliminar_obligacion(obligacion_id)

    assert page.tabla_obligaciones.rowCount() == 1
    session = session_module.get_session()
    assert session.query(Obligacion).count() == 1
    session.close()


def test_eliminar_obligacion_con_abonos_los_elimina_en_cascada(qtbot, monkeypatch):
    from database.models import Abono

    expediente_id = _expediente_con_obligacion(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 10), monto=Decimal("50000.00"))
    )
    session.add(
        Abono(obligacion_id=obligacion.id, fecha=date(2026, 2, 10), monto=Decimal("30000.00"))
    )
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._eliminar_obligacion(obligacion_id)

    session = session_module.get_session()
    assert session.query(Obligacion).count() == 0
    assert session.query(Abono).count() == 0
    session.close()


def test_eliminar_obligacion_con_abonos_refresca_la_tabla_de_abonos(qtbot, monkeypatch):
    """Regresion directa de un bug reportado en produccion (2026-08-12):
    eliminar una obligacion borraba sus abonos en cascada en la base de
    datos, pero _eliminar_obligacion solo llamaba _refrescar_obligaciones()
    -- tabla_abonos se quedaba mostrando la fila fantasma del abono ya
    borrado, con su boton "Eliminar" todavia conectado a un abono_id que ya
    no existia. Un clic ahi disparaba session.delete(None) ->
    UnmappedInstanceError (traceback crudo, reportado por el usuario)."""
    from database.models import Abono

    expediente_id = _expediente_con_obligacion(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(
        Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 10), monto=Decimal("50000.00"))
    )
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_abonos.rowCount() == 1

    page._eliminar_obligacion(obligacion_id)

    assert page.tabla_obligaciones.rowCount() == 0
    assert page.tabla_abonos.rowCount() == 0


def test_eliminar_abono_con_id_inexistente_no_crashea(qtbot, monkeypatch):
    """El caso puntual que reprodujo el traceback real: llamar
    _eliminar_abono con un id que ya no existe (fila fantasma tras un
    refresco que no llego a tiempo, o dos ventanas/clics compitiendo) debe
    avisar y refrescar, no lanzar UnmappedInstanceError."""
    expediente_id = _expediente_con_obligacion(monkeypatch)

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.information",
        lambda *a, **k: avisos.append(a) or QMessageBox.StandardButton.Ok,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._eliminar_abono(999999)  # id que nunca existio

    assert len(avisos) == 1


def test_editar_abono_con_id_inexistente_no_crashea(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.information",
        lambda *a, **k: avisos.append(a) or QMessageBox.StandardButton.Ok,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._editar_abono(999999)

    assert len(avisos) == 1


def test_eliminar_evento_laboral_con_id_inexistente_no_crashea(qtbot, monkeypatch):
    expediente_id = _expediente_laboral_sin_mora(monkeypatch)

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )
    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.information",
        lambda *a, **k: avisos.append(a) or QMessageBox.StandardButton.Ok,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._eliminar_evento_laboral(999999)

    assert len(avisos) == 1


def test_eliminar_obligacion_con_id_inexistente_no_crashea(qtbot, monkeypatch):
    expediente_id = _expediente_con_obligacion(monkeypatch)

    avisos = []
    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.information",
        lambda *a, **k: avisos.append(a) or QMessageBox.StandardButton.Ok,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._eliminar_obligacion(999999)

    assert len(avisos) == 1


def test_eliminar_obligacion_recurrente_con_cuotas_hijas_las_elimina_todas(qtbot, monkeypatch):
    """Caso especial del Sprint 60: obligacion_padre_id NO es una relationship()
    de SQLAlchemy (ver comentario en database/models.py cerca de esa columna),
    asi que las cuotas hijas generadas por generar_cuotas_mensuales (Sprint 41)
    no se borran por cascada del ORM -- _eliminar_obligacion debe consultarlas
    y borrarlas explicitamente. Este test genera cuotas REALES (mismo fixture
    y flujo que los tests de "Generar cuotas" de arriba), no un mock."""
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(
        monkeypatch
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    fila = page._obligacion_ids_por_fila.index(obligacion_id)
    page.tabla_obligaciones.setCurrentCell(fila, 0)
    page._generar_cuotas()
    assert page.tabla_obligaciones.rowCount() == 6  # obligacion padre + 5 cuotas

    session = session_module.get_session()
    total_cuotas = (
        session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id).count()
    )
    session.close()
    assert total_cuotas == 5  # confirma que las cuotas realmente se generaron

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page._eliminar_obligacion(obligacion_id)

    assert page.tabla_obligaciones.rowCount() == 0
    session = session_module.get_session()
    # Ni la obligacion padre ni ninguna de sus 5 cuotas hijas sobreviven.
    assert session.query(Obligacion).count() == 0
    session.close()


def test_tabla_obligaciones_tiene_columna_eliminar(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.tabla_obligaciones.columnCount() == 5
    encabezados = [
        page.tabla_obligaciones.horizontalHeaderItem(i).text() for i in range(5)
    ]
    assert encabezados == ["Concepto", "Tipo", "Valor", "Editar", "Eliminar"]


def test_editar_abono_abre_el_dialogo_con_el_id_y_refresca(qtbot, monkeypatch):
    from database.models import Abono

    expediente_id = _expediente_con_obligacion(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    abono = Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 10), monto=Decimal("50000.00"))
    session.add(abono)
    session.commit()
    abono_id = abono.id
    session.close()

    ids_recibidos = {}

    def _simular_edicion_y_guardado(self):
        ids_recibidos["abono_id"] = self._abono_id
        self.campo_referencia.setText("Editado")
        self.guardar()
        return True

    monkeypatch.setattr(
        "app.views.expediente_detalle.AbonoFormDialog.exec",
        _simular_edicion_y_guardado,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._editar_abono(abono_id)

    assert ids_recibidos["abono_id"] == abono_id
    session = session_module.get_session()
    assert session.query(Abono).count() == 1  # no se creo uno nuevo
    guardado = session.query(Abono).filter_by(id=abono_id).one()
    assert guardado.referencia == "Editado"
    session.close()


def test_eliminar_abono_lo_quita_de_la_tabla_y_la_base(qtbot, monkeypatch):
    from database.models import Abono

    expediente_id = _expediente_con_obligacion(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    abono = Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 10), monto=Decimal("50000.00"))
    session.add(abono)
    session.commit()
    abono_id = abono.id
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)
    assert page.tabla_abonos.rowCount() == 1

    page._eliminar_abono(abono_id)

    assert page.tabla_abonos.rowCount() == 0
    session = session_module.get_session()
    assert session.query(Abono).count() == 0
    session.close()


def test_eliminar_abono_cancelado_no_lo_elimina(qtbot, monkeypatch):
    from database.models import Abono

    expediente_id = _expediente_con_obligacion(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    abono = Abono(obligacion_id=obligacion.id, fecha=date(2026, 1, 10), monto=Decimal("50000.00"))
    session.add(abono)
    session.commit()
    abono_id = abono.id
    session.close()

    monkeypatch.setattr(
        "app.views.expediente_detalle.QMessageBox.question",
        lambda *a, **k: QMessageBox.StandardButton.No,
    )

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.cargar_expediente(expediente_id)

    page._eliminar_abono(abono_id)

    session = session_module.get_session()
    assert session.query(Abono).count() == 1
    session.close()


def test_tabla_abonos_tiene_columnas_editar_y_eliminar(qtbot):
    page = ExpedienteDetallePage()
    qtbot.addWidget(page)

    assert page.tabla_abonos.columnCount() == 5
    encabezados = [page.tabla_abonos.horizontalHeaderItem(i).text() for i in range(5)]
    assert encabezados == ["Fecha", "Monto", "Referencia", "Editar", "Eliminar"]


# --- Sprint 75 (Task 5): seleccion por rango + boton "Pagar cuotas seleccionadas" -----


def _expediente_civil_con_cuotas_generadas(monkeypatch) -> tuple[int, int]:
    """Expediente Civil/Familia con una obligacion RECURRENTE (tipo_reajuste_anual =
    NINGUNO, deterministico, sin necesitar parametros SMLMV/IPC en memoria) que ya
    genero 3 cuotas hijas reales (Feb/Mar/Abr 2024) via generar_cuotas_mensuales.
    Retorna (expediente_id, obligacion_padre_id). Segun _refrescar_obligaciones(), la
    fila 0 de tabla_obligaciones es la obligacion RECURRENTE padre y las filas 1-3 son
    sus 3 cuotas hijas, en el mismo orden que list(expediente.obligaciones) -- mismo
    patron ya verificado por
    test_flujo_completo_crear_obligacion_recurrente_generar_cuotas_y_abonar_una_cuota
    (lineas 1471-1474 de este archivo)."""
    from database.models import TipoReajusteAnual

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(
        session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-095",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=date(2024, 4, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2024, 2, 1),
        fecha_inicio=date(2024, 2, 1),
        dia_pago=1,
        valor=Decimal("150000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion)
    session.commit()
    expediente_id = expediente.id
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    obligacion_recargada = session.get(Obligacion, obligacion_id)
    generar_cuotas_mensuales(obligacion_recargada, fecha_corte=date(2024, 4, 1))
    session.close()

    return expediente_id, obligacion_id


def _seleccionar_filas(page: ExpedienteDetallePage, fila_desde: int, fila_hasta: int) -> None:
    from PySide6.QtWidgets import QTableWidgetSelectionRange

    page.tabla_obligaciones.clearSelection()
    page.tabla_obligaciones.setRangeSelected(
        QTableWidgetSelectionRange(
            fila_desde, 0, fila_hasta, page.tabla_obligaciones.columnCount() - 1
        ),
        True,
    )


def test_boton_pagar_cuotas_seleccionadas_solo_habilita_con_cuotas_hija_de_la_misma_recurrente(
    qtbot, monkeypatch
):
    expediente_id, _obligacion_padre_id = _expediente_civil_con_cuotas_generadas(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)
    assert pagina.tabla_obligaciones.rowCount() == 4  # padre + 3 cuotas

    # Sin seleccion: deshabilitado.
    assert not pagina.boton_pagar_cuotas_seleccionadas.isEnabled()

    # Selecciona las 2 primeras cuotas (filas 1 y 2, contiguas, misma recurrente).
    _seleccionar_filas(pagina, 1, 2)
    pagina._actualizar_boton_pagar_cuotas_seleccionadas()
    assert pagina.boton_pagar_cuotas_seleccionadas.isEnabled()


def test_boton_pagar_cuotas_seleccionadas_deshabilita_si_incluye_la_obligacion_padre(
    qtbot, monkeypatch
):
    expediente_id, _obligacion_padre_id = _expediente_civil_con_cuotas_generadas(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    # Fila 0 es la obligacion RECURRENTE padre (obligacion_padre_id=None): mezclar el
    # padre con sus propias cuotas hijas no es un rango valido para pagar en cascada.
    _seleccionar_filas(pagina, 0, 1)
    pagina._actualizar_boton_pagar_cuotas_seleccionadas()
    assert not pagina.boton_pagar_cuotas_seleccionadas.isEnabled()


def test_cuotas_hija_de_una_misma_recurrente_retorna_false_para_seleccion_vacia(qtbot):
    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)

    assert pagina._cuotas_hija_de_una_misma_recurrente([]) is False


def test_boton_pagar_cuotas_seleccionadas_visible_para_civil_familia_y_comercial(
    qtbot, monkeypatch
):
    """Mismo criterio de visibilidad que boton_generar_cuotas (ver fix de este mismo
    sprint): el pago por rango solo tiene sentido en las 2 areas que soportan cuotas-
    hija recurrentes -- _ESTRATEGIA_POR_AREA de PagoPorRangoDialog
    (app/views/pago_por_rango.py) solo tiene entradas para CIVIL_FAMILIA/COMERCIAL."""
    expediente_id_civil, _ = _expediente_civil_con_cuotas_generadas(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id_civil)
    assert pagina.boton_pagar_cuotas_seleccionadas.isVisible() is True

    expediente_id_comercial = _expediente_comercial_con_obligacion_usuraria(monkeypatch)
    pagina.cargar_expediente(expediente_id_comercial)
    assert pagina.boton_pagar_cuotas_seleccionadas.isVisible() is True

    expediente_id_laboral = _expediente_laboral_sin_mora(monkeypatch)
    pagina.cargar_expediente(expediente_id_laboral)
    assert pagina.boton_pagar_cuotas_seleccionadas.isVisible() is False


def test_abrir_dialogo_pago_por_rango_crea_abonos_y_refresca_tablas(qtbot, monkeypatch):
    from database.models import Abono

    expediente_id, _obligacion_padre_id = _expediente_civil_con_cuotas_generadas(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    _seleccionar_filas(pagina, 1, 3)  # las 3 cuotas hijas
    pagina._actualizar_boton_pagar_cuotas_seleccionadas()
    assert pagina.boton_pagar_cuotas_seleccionadas.isEnabled()

    ids_cuotas_seleccionadas = [pagina._obligacion_ids_por_fila[fila] for fila in (1, 2, 3)]

    def _dialogo_falso(cuotas, area, parent=None):
        assert area == "CIVIL_FAMILIA"
        assert {c.id for c in cuotas} == set(ids_cuotas_seleccionadas)
        # Cascada real: capital de cada cuota es 150.000, tasa 0% -> 450.000 alcanza
        # exacto para las 3 sin dejar remanente.
        session = session_module.get_session()
        for cuota in cuotas:
            session.add(Abono(obligacion_id=cuota.id, fecha=date(2024, 4, 1), monto=cuota.valor))
        session.commit()
        session.close()

        class _Resultado:
            def exec(self_inner):
                return True

        return _Resultado()

    monkeypatch.setattr("app.views.expediente_detalle.PagoPorRangoDialog", _dialogo_falso)

    pagina._abrir_dialogo_pago_por_rango()

    session = session_module.get_session()
    total_abonos = (
        session.query(Abono).filter(Abono.obligacion_id.in_(ids_cuotas_seleccionadas)).count()
    )
    session.close()
    assert total_abonos == 3


def test_obligacion_por_fila_retorna_la_obligacion_real(qtbot, monkeypatch):
    expediente_id, obligacion_padre_id = _expediente_civil_con_cuotas_generadas(monkeypatch)

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.cargar_expediente(expediente_id)

    obligacion = pagina._obligacion_por_fila(0)
    assert obligacion.id == obligacion_padre_id
    assert obligacion.concepto == "CUOTA ALIMENTARIA"
