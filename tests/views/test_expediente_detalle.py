from datetime import date
from decimal import Decimal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import database.session as session_module
from database.models import AreaDerecho, Base, Expediente, Obligacion, TipoObligacion, Abono
from app.views.expediente_detalle import ExpedienteDetallePage


def _expediente_con_obligacion(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
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

    page._liquidar()

    assert len(resultados_recibidos) == 1
    resultado, exp_id = resultados_recibidos[0]
    assert exp_id == expediente_id
    assert resultado.final_balance().principal == Decimal("427900.00")


from app.core.exceptions import TasaUsurariaError


def _expediente_comercial_con_obligacion_usuraria(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
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


def test_liquidar_area_comercial_con_tasa_usuraria_muestra_advertencia(qtbot, monkeypatch):
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

    page._liquidar()

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "Tasa usuraria"


def _expediente_honorarios_con_cuota_litis_excesiva(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
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
            cuota_litis_pactada_pct=Decimal("35.00"),  # excede el tope individual del 30%
            beneficio_obtenido=Decimal("10000000.00"),
            costas_pct_manual=Decimal("5.00"),
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _expediente_sancionatorio_con_hecho_posterior_a_2020(monkeypatch) -> int:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    monkeypatch.setattr(session_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False))

    session = session_module.get_session()
    expediente = Expediente(
        radicado="2026-051",
        demandante="Estado",
        demandado="Empresa XYZ",
        area_derecho=AreaDerecho.SANCIONATORIO,
        fecha_corte_default=date(2021, 6, 1),
    )
    session.add(expediente)
    session.flush()
    session.add(
        Obligacion(
            expediente_id=expediente.id,
            tipo=TipoObligacion.PUNTUAL,
            concepto="Multa SIC",
            categoria="MULTA_SANCIONATORIA",
            fecha_origen=date(2021, 1, 1),  # posterior a 2020-01-01: no hay tabla UVT
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
    mostrarse como advertencia amigable, igual que AreaNoImplementadaError/TasaUsurariaError.
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

    page._liquidar()  # no debe lanzar/crashear

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "Cuota litis excede el tope"


def test_liquidar_area_sancionatorio_con_hecho_posterior_a_2020_muestra_advertencia_sin_crash(
    qtbot, monkeypatch
):
    """
    Regresion: UVTNoDisponibleError (agregada en Sprint 4) no estaba en la lista de except
    de _liquidar(), asi que se propagaba como traceback no controlado en vez de mostrarse
    como advertencia amigable, igual que CuotaLitisExcedeTopeError.
    """
    expediente_id = _expediente_sancionatorio_con_hecho_posterior_a_2020(monkeypatch)

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

    page._liquidar()  # no debe lanzar/crashear

    assert len(resultados_recibidos) == 0
    assert len(avisos) == 1
    assert avisos[0][0] == "UVT no disponible"


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
