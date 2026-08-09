from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import database.database as database_module
import database.session as session_module
from app.engine.indexation.historical_index import _IPC_INDICE_ACUMULADO
from app.views.expediente_detalle import ExpedienteDetallePage
from database.models import (
    AreaDerecho,
    Base,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)


def _expediente_con_obligacion(monkeypatch) -> int:
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="USURA_MULTIPLICADOR", valor=Decimal("1.5"), vigente_desde=date(1997, 7, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    # Tarea 12: CivilFamiliaStrategy ahora resuelve el indice IPC via
    # get_ipc_interpolado_for_date -> parametro_service, en vez del diccionario
    # en memoria de historical_index.py -- se siembra IPC_INDICE_ACUMULADO
    # completo desde el mismo diccionario congelado que usa
    # scripts/migrate_parametros_legales.py, para no re-transcribir a mano.
    for anio, valor in _IPC_INDICE_ACUMULADO.items():
        session.add(ParametroLegal(
            clave="IPC_INDICE_ACUMULADO", valor=valor, vigente_desde=date(anio, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
        ))
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


def test_liquidar_area_comercial_con_tasa_usuraria_no_muestra_advertencia_y_aplica_sancion(qtbot, monkeypatch):
    # Respuesta del despacho (Preguntas-Para-Abogado.md, Sprint 2): una tasa por encima
    # de la usura ya no rechaza la liquidacion -- se liquida igual y se aplica la sancion
    # legal (perdida doblada del exceso) como un rubro mas del resultado.
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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="HONORARIOS_TOTAL_PCT", valor=Decimal("50"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
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
            cuota_litis_pactada_pct=Decimal("45.00"),  # total (1M + 4.5M = 5.5M) excede el 50% (5M)
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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))
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
            fecha_origen=date(2027, 1, 1),  # posterior a 2026: fuera del rango de la tabla historica UVT (2006-2026), aun no publicada por la DIAN
            valor=Decimal("0.00"),
            tasa_efectiva_anual=Decimal("0.00"),
            cantidad_smlmv_uvt=Decimal("2"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_honorarios_con_cuota_litis_excesiva_muestra_advertencia_sin_crash(qtbot, monkeypatch):
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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

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


def test_liquidar_area_tributaria_sin_parametros_de_sancion_muestra_advertencia_sin_crash(qtbot, monkeypatch):
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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

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
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("877803.00"), vigente_desde=date(2020, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    for clave, valor in {
        "SS_PENSION_PCT": Decimal("0.16"),
        "SS_SALUD_PCT": Decimal("0.125"),
        "SS_ARL_NIVEL_I_PCT": Decimal("0.00522"),
    }.items():
        session.add(ParametroLegal(
            clave=clave, valor=valor, vigente_desde=date(1900, 1, 1),
            vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
        ))
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def test_liquidar_area_laboral_con_seguridad_social_no_lanza_detached_instance_error(qtbot, monkeypatch):
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


from app.engine.audit.service import registrar_liquidacion
from app.engine.liquidation.registry import AreaRegistry


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
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-070", demandante="Trabajador", demandado="Empleador SAS",
        area_derecho=AreaDerecho.LABORAL, fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    obligacion = Obligacion(
        expediente_id=expediente.id, tipo=TipoObligacion.PUNTUAL,
        concepto="Liquidacion de contrato", categoria="LIQUIDACION_CONTRATO_LABORAL",
        fecha_origen=date(2020, 1, 1), valor=Decimal("3000000.00"),
        tasa_efectiva_anual=Decimal("0.00"), fecha_inicio=date(2020, 1, 1), fecha_fin=date(2020, 12, 31),
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
    expediente_id = _expediente_con_obligacion(monkeypatch)  # CIVIL_FAMILIA, ya existe en este archivo

    pagina = ExpedienteDetallePage()
    qtbot.addWidget(pagina)
    pagina.show()
    pagina.cargar_expediente(expediente_id)

    assert pagina.grupo_eventos_laborales.isVisible() is False


def test_refrescar_eventos_laborales_lista_los_eventos_de_todas_las_obligaciones(qtbot, monkeypatch):
    from database.models import EventoLaboral, TipoEventoLaboral

    expediente_id = _expediente_laboral_sin_mora(monkeypatch)
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    session.add(EventoLaboral(
        obligacion_id=obligacion.id, tipo=TipoEventoLaboral.INCAPACIDAD_COMUN,
        fecha_inicio=date(2020, 5, 1), fecha_fin=date(2020, 5, 4),
    ))
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


def _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch) -> tuple[int, int]:
    """Sprint 41: expediente Civil/Familia con una obligacion RECURRENTE con
    tipo_reajuste_anual=SMMLV, lista para 'Generar cuotas' en la UI. Retorna
    (expediente_id, obligacion_id)."""
    from database.models import TipoReajusteAnual

    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("1000000.00"), vigente_desde=date(2024, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.add(ParametroLegal(
        clave="SMLMV", valor=Decimal("1100000.00"), vigente_desde=date(2025, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
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


def test_boton_generar_cuotas_visible_solo_para_civil_familia(qtbot, monkeypatch):
    expediente_id_civil, _ = _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch)

    page = ExpedienteDetallePage()
    qtbot.addWidget(page)
    page.show()
    page.cargar_expediente(expediente_id_civil)
    assert page.boton_generar_cuotas.isVisible() is True

    expediente_id_comercial = _expediente_comercial_con_obligacion_usuraria(monkeypatch)
    page.cargar_expediente(expediente_id_comercial)
    assert page.boton_generar_cuotas.isVisible() is False


def test_generar_cuotas_sin_seleccion_muestra_advertencia(qtbot, monkeypatch):
    expediente_id, _obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch)

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
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch)

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
    expediente_id, obligacion_id = _expediente_civil_con_obligacion_recurrente_con_reajuste(monkeypatch)

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
