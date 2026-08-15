from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.services.reajuste_anual import generar_cuotas_mensuales
from database.models import (
    AreaDerecho,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
    TipoReajusteAnual,
)


def _expediente_civil(session, area: AreaDerecho = AreaDerecho.CIVIL_FAMILIA) -> int:
    expediente = Expediente(
        radicado="2026-041",
        demandante="Ana",
        demandado="Luis",
        area_derecho=area,
        fecha_corte_default=date(2026, 6, 1),
    )
    session.add(expediente)
    session.flush()
    return expediente.id


def _sembrar_smlmv(session, valores: dict[int, Decimal]) -> None:
    for anio, valor in valores.items():
        session.add(
            ParametroLegal(
                clave="SMLMV",
                valor=valor,
                vigente_desde=date(anio, 1, 1),
                vigente_hasta=None,
                usuario="test",
                motivo=None,
                creado_en=datetime.now(),
            )
        )


def _obligacion_recurrente_smmlv(session, expediente_id: int, *, fecha_fin=None) -> Obligacion:
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2024, 11, 5),
        fecha_inicio=date(2024, 11, 5),
        fecha_fin=fecha_fin,
        dia_pago=5,
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_reajuste_anual=TipoReajusteAnual.SMMLV,
    )
    session.add(obligacion)
    session.commit()
    return obligacion


def test_genera_cuotas_mensuales_con_capital_reajustado_por_smmlv_cada_enero(monkeypatch):
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    # Cifras sinteticas simples y redondas (no la serie SMLMV real) para poder
    # verificar el capital exacto de cada año a mano: 2024 -> 2025 sube 10%,
    # 2025 -> 2026 sube 5% (dos tasas distintas para confirmar que la formula
    # no esta hardcodeada a un solo porcentaje).
    _sembrar_smlmv(
        session,
        {
            2024: Decimal("1000000.00"),
            2025: Decimal("1100000.00"),
            2026: Decimal("1155000.00"),
        },
    )
    obligacion = _obligacion_recurrente_smmlv(session, expediente_id)
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(padre, fecha_corte=date(2026, 3, 5))
    session.close()

    # Nov/Dic 2024 (2) + Ene..Dic 2025 (12) + Ene..Mar 2026 (3) = 17 cuotas.
    assert len(cuotas) == 17
    assert all(c.tipo == TipoObligacion.PUNTUAL for c in cuotas)
    assert all(c.obligacion_padre_id == obligacion_id for c in cuotas)
    assert all(c.expediente_id == expediente_id for c in cuotas)
    assert all(c.categoria == "CHILD_SUPPORT" for c in cuotas)
    assert all(c.tasa_efectiva_anual == Decimal("6.00") for c in cuotas)

    por_fecha = {c.fecha_origen: c for c in cuotas}

    # Año de origen (2024): capital sin reajustar, igual al de la obligacion padre.
    assert por_fecha[date(2024, 11, 5)].valor == Decimal("100000.00")
    assert por_fecha[date(2024, 11, 5)].concepto == "CUOTA ALIMENTARIA DE NOVIEMBRE 2024"
    assert por_fecha[date(2024, 12, 5)].valor == Decimal("100000.00")
    assert por_fecha[date(2024, 12, 5)].concepto == "CUOTA ALIMENTARIA DE DICIEMBRE 2024"

    # 2025: reajustado +10% -> 110000.00, constante todo el año.
    assert por_fecha[date(2025, 1, 5)].valor == Decimal("110000.00")
    assert por_fecha[date(2025, 1, 5)].concepto == "CUOTA ALIMENTARIA DE ENERO 2025"
    assert por_fecha[date(2025, 6, 5)].valor == Decimal("110000.00")
    assert por_fecha[date(2025, 12, 5)].valor == Decimal("110000.00")

    # 2026: reajustado +5% sobre 110000 -> 115500.00.
    assert por_fecha[date(2026, 1, 5)].valor == Decimal("115500.00")
    assert por_fecha[date(2026, 1, 5)].concepto == "CUOTA ALIMENTARIA DE ENERO 2026"
    assert por_fecha[date(2026, 2, 5)].valor == Decimal("115500.00")
    assert por_fecha[date(2026, 3, 5)].valor == Decimal("115500.00")

    # No hay cuota de abril 2026: fecha_corte tope el 5 de marzo 2026.
    assert date(2026, 4, 5) not in por_fecha


def test_generar_cuotas_mensuales_es_idempotente_no_duplica(monkeypatch):
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    _sembrar_smlmv(
        session,
        {
            2024: Decimal("1000000.00"),
            2025: Decimal("1100000.00"),
        },
    )
    obligacion = _obligacion_recurrente_smmlv(session, expediente_id)
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    primera_llamada = generar_cuotas_mensuales(padre, fecha_corte=date(2025, 3, 5))
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    segunda_llamada = generar_cuotas_mensuales(padre, fecha_corte=date(2025, 3, 5))
    session.close()

    assert len(primera_llamada) == len(segunda_llamada)
    assert {c.id for c in primera_llamada} == {c.id for c in segunda_llamada}

    session = session_module.get_session()
    total_en_bd = (
        session.query(Obligacion).filter(Obligacion.obligacion_padre_id == obligacion_id).count()
    )
    session.close()
    assert total_en_bd == len(primera_llamada)


def test_generar_cuotas_mensuales_respeta_fecha_fin_de_la_obligacion(monkeypatch):
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    _sembrar_smlmv(session, {2024: Decimal("1000000.00")})
    obligacion = _obligacion_recurrente_smmlv(session, expediente_id, fecha_fin=date(2024, 12, 5))
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(padre, fecha_corte=date(2026, 6, 1))
    session.close()

    assert len(cuotas) == 2
    assert {c.fecha_origen for c in cuotas} == {date(2024, 11, 5), date(2024, 12, 5)}


def test_generar_cuotas_mensuales_con_reajuste_ipc_usa_ipcindexation(monkeypatch):
    from app.engine.indexation.ipc import IPCIndexation

    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    session.add(
        ParametroLegal(
            clave="IPC_INDICE_ACUMULADO",
            valor=Decimal("100.00"),
            vigente_desde=date(2024, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    session.add(
        ParametroLegal(
            clave="IPC_INDICE_ACUMULADO",
            valor=Decimal("110.00"),
            vigente_desde=date(2025, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=datetime.now(),
        )
    )
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="CUOTA ALIMENTARIA",
        categoria="CHILD_SUPPORT",
        fecha_origen=date(2024, 11, 5),
        fecha_inicio=date(2024, 11, 5),
        dia_pago=5,
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
        tipo_reajuste_anual=TipoReajusteAnual.IPC,
    )
    session.add(obligacion)
    session.commit()
    obligacion_id = obligacion.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(padre, fecha_corte=date(2025, 1, 5))
    session.close()

    por_fecha = {c.fecha_origen: c.valor for c in cuotas}
    delta_esperado = IPCIndexation.calculate(
        capital=Decimal("100000.00"),
        initial_index=Decimal("100.00"),
        final_index=Decimal("110.00"),
    )
    assert por_fecha[date(2025, 1, 5)] == Decimal("100000.00") + delta_esperado


def test_generar_cuotas_mensuales_rechaza_obligacion_puntual():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session)
    obligacion = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.PUNTUAL,
        concepto="Dano emergente",
        categoria="DANO_EMERGENTE",
        fecha_origen=date(2024, 1, 1),
        valor=Decimal("100000.00"),
        tasa_efectiva_anual=Decimal("6.00"),
    )
    session.add(obligacion)
    session.commit()
    session.close()

    with pytest.raises(ValueError, match="RECURRENTE"):
        generar_cuotas_mensuales(obligacion, fecha_corte=date(2025, 1, 1))


def test_genera_cuotas_con_capital_constante_cuando_no_hay_reajuste():
    session = session_module.get_session()
    expediente_id = _expediente_civil(session, area=AreaDerecho.COMERCIAL)
    obligacion_recurrente = Obligacion(
        expediente_id=expediente_id,
        tipo=TipoObligacion.RECURRENTE,
        concepto="Cuota de arrendamiento",
        categoria="CAPITAL_PAGARE",
        fecha_origen=date(2024, 1, 1),
        fecha_inicio=date(2024, 1, 1),
        fecha_fin=date(2024, 4, 1),
        dia_pago=1,
        valor=Decimal("500000.00"),
        tasa_efectiva_anual=Decimal("0.00"),
        tipo_reajuste_anual=TipoReajusteAnual.NINGUNO,
    )
    session.add(obligacion_recurrente)
    session.commit()
    obligacion_id = obligacion_recurrente.id
    session.close()

    session = session_module.get_session()
    padre = session.get(Obligacion, obligacion_id)
    cuotas = generar_cuotas_mensuales(padre, fecha_corte=date(2024, 4, 1))
    session.close()

    assert len(cuotas) == 4
    assert all(cuota.valor == Decimal("500000.00") for cuota in cuotas)
