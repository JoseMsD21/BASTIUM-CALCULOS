from datetime import date
from datetime import datetime as _dt
from decimal import Decimal

import database.session as session_module
from app.engine.liquidation.engine import LiquidationCore
from app.engine.temporal.prescripcion import TipoAccion
from app.engine.temporal.schedulers.base import Event
from app.services.motor_universal import UniversalLiquidationService
from database.models import ParametroLegal


def _sembrar_parametro(clave: str, meses: int) -> None:
    session = session_module.get_session()
    session.add(
        ParametroLegal(
            clave=clave,
            valor=Decimal(meses),
            vigente_desde=date(1900, 1, 1),
            vigente_hasta=None,
            usuario="test",
            motivo=None,
            creado_en=_dt.now(),
        )
    )
    session.commit()
    session.close()


def test_liquidar_reenvia_usar_suma_unica_al_motor_core():
    eventos = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]

    resultado_legado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"),
        usar_suma_unica=False,
    )
    resultado_suma_unica = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"),
        usar_suma_unica=True,
    )

    assert resultado_legado.final_balance().interest == Decimal("100.00")
    assert resultado_suma_unica.final_balance().interest == Decimal("150.00")


def test_liquidar_usar_suma_unica_default_es_false():
    eventos = [
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("1000.00")}, event_type="INSTALLMENT"
        ),
        Event(
            date=date(2026, 1, 1), payload={"amount": Decimal("500.00")}, event_type="INDEXATION"
        ),
    ]

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=date(2026, 1, 11),
        tasa_estatica=Decimal("1.00"),
    )

    assert resultado.final_balance().interest == Decimal("100.00")


# --- Sprint 42: wiring del motor de prescripcion/caducidad ---------------
#
# UniversalLiquidationService.liquidar() es el unico punto por el que pasan
# las 6 AreaStrategy para invocar LiquidationCore (directo o via
# _liquidar_por_obligacion en app/services/area_strategy.py) -- centralizar
# aqui el wiring evita repetirlo 6 veces. Decision del despacho: la
# obligacion prescrita se sigue liquidando igual (el total NO cambia), solo
# se marca informativamente (LiquidationItem.prescrita).


def test_liquidar_marca_evento_prescrito_sin_excluirlo_del_calculo():
    _sembrar_parametro("PRESCRIPCION_EJECUTIVA_MESES", 60)  # 5 años (default TipoAccion.EJECUTIVA)

    eventos = [
        Event(
            date=date(2015, 1, 1),
            payload={"amount": Decimal("1000.00"), "label": "Capital antiguo"},
            event_type="INSTALLMENT",
        ),
    ]
    fecha_corte = date(2026, 1, 1)  # mas de 5 años despues de 2015-01-01 -> prescrita

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=fecha_corte,
    )

    fila_capital = next(
        item for item in resultado.items if item.balance.event_type == "INSTALLMENT"
    )
    assert fila_capital.prescrita is True

    # El total NO cambia por la marca: la obligacion prescrita sigue
    # calculandose exactamente igual que si el wiring no existiera -- se
    # compara contra LiquidationCore invocado directamente, sin ningun
    # conocimiento de prescripcion.
    referencia = LiquidationCore().process(chronological_events=eventos, cutoff_date=fecha_corte)
    assert resultado.final_balance() == referencia.final_balance()
    assert resultado.final_balance().total() == referencia.final_balance().total()


def test_liquidar_evento_no_vencido_no_se_marca_prescrito():
    _sembrar_parametro("PRESCRIPCION_EJECUTIVA_MESES", 60)

    eventos = [
        Event(
            date=date(2025, 1, 1),
            payload={"amount": Decimal("1000.00"), "label": "Capital reciente"},
            event_type="INSTALLMENT",
        ),
    ]
    fecha_corte = date(2026, 1, 1)  # menos de 5 años -> aun vigente

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=fecha_corte,
    )

    assert resultado.items[0].prescrita is False


def test_liquidar_sin_parametro_prescripcion_configurado_no_marca_ni_falla():
    # Sin PRESCRIPCION_EJECUTIVA_MESES sembrado en Parametros (fixture global
    # de tests/conftest.py da un engine en memoria sin datos), no se puede
    # determinar el estado -- se omite la marca en vez de tumbar la
    # liquidacion, mismo criterio que _refrescar_alertas_vencimiento en
    # app/views/dashboard.py (Sprint 33).
    eventos = [
        Event(
            date=date(2015, 1, 1),
            payload={"amount": Decimal("1000.00"), "label": "Capital antiguo"},
            event_type="INSTALLMENT",
        ),
    ]
    fecha_corte = date(2026, 1, 1)

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=fecha_corte,
    )

    assert resultado.items[0].prescrita is False
    assert resultado.final_balance().total() > Decimal("0.00")


def test_liquidar_solo_marca_eventos_de_causacion_nunca_pagos():
    _sembrar_parametro("PRESCRIPCION_EJECUTIVA_MESES", 60)
    from app.domain.obligation.payment import Payment

    eventos = [
        Event(
            date=date(2015, 1, 1),
            payload={"amount": Decimal("1000.00"), "label": "Capital antiguo"},
            event_type="INSTALLMENT",
        ),
    ]
    pagos = [Payment(date=date(2015, 1, 1), amount=Decimal("100.00"), reference="Abono")]
    fecha_corte = date(2026, 1, 1)

    resultado = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=pagos,
        fecha_corte=fecha_corte,
    )

    filas_por_tipo = {item.balance.event_type: item for item in resultado.items}
    assert filas_por_tipo["INSTALLMENT"].prescrita is True
    assert filas_por_tipo["PAYMENT"].prescrita is False


def test_liquidar_acepta_tipo_accion_explicito_para_calcular_prescripcion():
    # PRESCRIPCION_ORDINARIA_MESES (10 años) es mucho mas largo que
    # PRESCRIPCION_EJECUTIVA_MESES (5 años, el default) -- el mismo evento
    # esta prescrito bajo el default pero vigente bajo ORDINARIA.
    _sembrar_parametro("PRESCRIPCION_EJECUTIVA_MESES", 60)
    _sembrar_parametro("PRESCRIPCION_ORDINARIA_MESES", 120)

    eventos = [
        Event(
            date=date(2018, 1, 1),
            payload={"amount": Decimal("1000.00"), "label": "Capital"},
            event_type="INSTALLMENT",
        ),
    ]
    fecha_corte = date(2026, 1, 1)  # 8 años: prescrita bajo EJECUTIVA, vigente bajo ORDINARIA

    resultado_default = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=fecha_corte,
    )
    resultado_ordinaria = UniversalLiquidationService().liquidar(
        eventos_causacion=eventos,
        pagos=[],
        fecha_corte=fecha_corte,
        tipo_accion=TipoAccion.ORDINARIA,
    )

    assert resultado_default.items[0].prescrita is True
    assert resultado_ordinaria.items[0].prescrita is False
