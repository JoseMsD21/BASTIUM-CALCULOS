"""Sprint 107: vista de sensibilidad "Ver con/sin indexación" (respuesta del
despacho, implementacion hibrida). Recalcula en memoria, sin tocar la base de
datos: ni las obligaciones guardadas ni el AuditLog de la liquidacion oficial."""

from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest

import database.session as session_module
from app.engine.indexation.historical_index import _IPC_INDICE_ACUMULADO
from app.services.vista_sensibilidad_indexacion import (
    ObligacionVistaSensibilidad,
    liquidar_vista_sensibilidad,
)
from database.models import (
    AreaDerecho,
    AuditLog,
    Expediente,
    Obligacion,
    ParametroLegal,
    TipoObligacion,
)

FECHA_CORTE = date(2025, 12, 31)


def _expediente_civil(aplica_indexacion_ipc: bool, interes_sobre_capital_indexado: bool) -> int:
    session = session_module.get_session()
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
        radicado="2026-107",
        demandante="Ana",
        demandado="Luis",
        area_derecho=AreaDerecho.CIVIL_FAMILIA,
        fecha_corte_default=FECHA_CORTE,
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
            aplica_indexacion_ipc=aplica_indexacion_ipc,
            interes_sobre_capital_indexado=interes_sobre_capital_indexado,
        )
    )
    session.commit()
    expediente_id = expediente.id
    session.close()
    return expediente_id


def _banderas_guardadas(expediente_id: int) -> tuple[bool, bool]:
    session = session_module.get_session()
    obligacion = session.query(Obligacion).filter_by(expediente_id=expediente_id).one()
    banderas = (obligacion.aplica_indexacion_ipc, obligacion.interes_sobre_capital_indexado)
    session.close()
    return banderas


def _cantidad_audit_logs() -> int:
    session = session_module.get_session()
    cantidad = session.query(AuditLog).count()
    session.close()
    return cantidad


def test_proxy_sobrescribe_solo_las_dos_banderas_y_delega_el_resto():
    original = SimpleNamespace(
        id=7, concepto="Capital", aplica_indexacion_ipc=True, interes_sobre_capital_indexado=True
    )

    proxy = ObligacionVistaSensibilidad(
        original, aplica_indexacion_ipc=False, interes_sobre_capital_indexado=False
    )

    assert proxy.aplica_indexacion_ipc is False
    assert proxy.interes_sobre_capital_indexado is False
    assert proxy.id == 7
    assert proxy.concepto == "Capital"
    # El objeto original no se toca.
    assert original.aplica_indexacion_ipc is True
    assert original.interes_sobre_capital_indexado is True


def test_proxy_es_de_solo_lectura():
    original = SimpleNamespace(concepto="Capital")
    proxy = ObligacionVistaSensibilidad(
        original, aplica_indexacion_ipc=False, interes_sobre_capital_indexado=False
    )

    with pytest.raises(AttributeError):
        proxy.concepto = "Otro"
    assert original.concepto == "Capital"


def test_sin_indexacion_quita_la_indexacion_y_no_toca_la_base_de_datos():
    expediente_id = _expediente_civil(
        aplica_indexacion_ipc=True, interes_sobre_capital_indexado=True
    )

    resultado = liquidar_vista_sensibilidad(expediente_id, FECHA_CORTE, con_indexacion=False)

    assert "INDEXATION" not in {item.balance.event_type for item in resultado.items}
    assert resultado.final_balance().indexation == Decimal("0.00")
    assert resultado.final_balance().principal == Decimal("1000000.00")
    # A mano: 6% anual lineal simple sobre el capital historico, 1.000.000 x 0,06 /
    # 365 = 164,3835... -> 164,38 diarios (politica LEGADA_DIARIA_REDONDEADA) x 548
    # dias (2024-07-01 -> 2025-12-31: 365 + 183) = 90.080,24.
    assert resultado.final_balance().interest == Decimal("90080.24")
    assert _banderas_guardadas(expediente_id) == (True, True)
    assert _cantidad_audit_logs() == 0


def test_con_indexacion_agrega_la_indexacion_ipc_y_no_toca_la_base_de_datos():
    expediente_id = _expediente_civil(
        aplica_indexacion_ipc=False, interes_sobre_capital_indexado=False
    )

    resultado = liquidar_vista_sensibilidad(expediente_id, FECHA_CORTE, con_indexacion=True)

    # Mismo capital/fechas que
    # tests/views/test_expediente_detalle.py::test_liquidar_area_civil_con_indexacion_ipc_...
    # (indice IPC mensual real, Sprint 80): 61933.78.
    assert resultado.final_balance().indexation == Decimal("61933.78")
    assert _banderas_guardadas(expediente_id) == (False, False)
    assert _cantidad_audit_logs() == 0


def test_con_indexacion_conserva_el_interes_sobre_capital_indexado_guardado():
    # "Con indexación" solo enciende aplica_indexacion_ipc; la eleccion de Suma
    # Única (interes_sobre_capital_indexado) sigue siendo la guardada.
    original = SimpleNamespace(aplica_indexacion_ipc=False, interes_sobre_capital_indexado=True)
    from app.services.vista_sensibilidad_indexacion import obligaciones_para_vista_sensibilidad

    (proxy,) = obligaciones_para_vista_sensibilidad([original], con_indexacion=True)
    assert proxy.aplica_indexacion_ipc is True
    assert proxy.interes_sobre_capital_indexado is True

    (proxy_sin,) = obligaciones_para_vista_sensibilidad([original], con_indexacion=False)
    assert proxy_sin.aplica_indexacion_ipc is False
    assert proxy_sin.interes_sobre_capital_indexado is False
