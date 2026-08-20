"""Tests de scripts/migrate_ibc_usura_1971_1997.py (Sprint 81).

El escenario real que este script existe para resolver: una bastium.db donde
IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO YA tienen filas (sembradas
desde 1997 por scripts/migrate_parametros_legales.py en un sprint anterior),
asi que el chequeo de idempotencia de ESE script ("la clave ya tiene alguna
fila") siempre es cierto y nunca vuelve a sembrar nada -- sin importar
cuantos tramos nuevos se agreguen a _TRAMOS_IBC_USURA. Los tests de
"extension" de abajo simulan exactamente ese estado sembrando a mano solo las
filas 1997+ (sin usar migrate_parametros_legales.migrar(), que en una base
nueva sembraria TODO de una, incluidos los tramos pre-1997, y no
reproduciria el escenario real)."""

from datetime import date, datetime
from decimal import ROUND_HALF_UP, Decimal

import database.session as session_module
from app.engine.indexation.historical_index import _TRAMOS_IBC_USURA
from database.models import ParametroLegal
from scripts.migrate_ibc_usura_1971_1997 import _TRAMOS_PRE_1997, migrar

_LIMITE_1997 = date(1997, 7, 1)
_TRAMOS_1997_EN_ADELANTE = [t for t in _TRAMOS_IBC_USURA if t.inicio >= _LIMITE_1997]


def _sembrar_solo_1997_en_adelante(session):
    """Reproduce el estado de una bastium.db real anterior al Sprint 81:
    IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO con filas SOLO desde
    1997-07-01 (lo que sembraba migrate_parametros_legales.py antes de que
    este sprint extendiera _TRAMOS_IBC_USURA hacia atras)."""
    for tramo in _TRAMOS_1997_EN_ADELANTE:
        session.add(
            ParametroLegal(
                clave="IBC_CONSUMO_ORDINARIO",
                valor=tramo.ibc_anual,
                vigente_desde=tramo.inicio,
                vigente_hasta=tramo.fin,
                usuario="sistema",
                motivo="Estado pre-Sprint-81 simulado para el test.",
                creado_en=datetime.now(),
                areas_derecho='["TR", "LA"]',
                unidad="%",
                creado_por_sistema=True,
            )
        )
        session.add(
            ParametroLegal(
                clave="USURA_CONSUMO_ORDINARIO",
                valor=tramo.usura_anual,
                vigente_desde=tramo.inicio,
                vigente_hasta=tramo.fin,
                usuario="sistema",
                motivo="Estado pre-Sprint-81 simulado para el test.",
                creado_en=datetime.now(),
                areas_derecho='["TR", "LA"]',
                unidad="%",
                creado_por_sistema=True,
            )
        )
    session.commit()


def test_tramos_pre_1997_no_esta_vacio():
    # Salvaguarda: si _TRAMOS_IBC_USURA alguna vez perdiera los tramos
    # pre-1997, este modulo entero pasaria de forma vacua sin fallar nada.
    assert len(_TRAMOS_PRE_1997) >= 40
    assert all(t.fin < _LIMITE_1997 for t in _TRAMOS_PRE_1997)


def test_migrar_extiende_una_clave_ya_parcialmente_sembrada():
    session = session_module.get_session()
    _sembrar_solo_1997_en_adelante(session)
    session.close()

    sembradas = migrar()

    assert sembradas == 2 * len(_TRAMOS_PRE_1997)

    session = session_module.get_session()
    total_ibc = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO")
        .count()
    )
    total_usura = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "USURA_CONSUMO_ORDINARIO")
        .count()
    )
    session.close()

    # Ni un tramo pre-1997 de mas ni uno de los 1997+ duplicado.
    assert total_ibc == len(_TRAMOS_IBC_USURA)
    assert total_usura == len(_TRAMOS_IBC_USURA)


def test_migrar_primer_tramo_1971_coincide_con_ibc_anual_y_vigencia():
    session = session_module.get_session()
    _sembrar_solo_1997_en_adelante(session)
    session.close()

    migrar()

    session = session_module.get_session()
    fila = (
        session.query(ParametroLegal)
        .filter(
            ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO",
            ParametroLegal.vigente_desde == date(1971, 10, 29),
        )
        .one()
    )
    session.close()
    assert fila.valor == Decimal("14.00")
    assert fila.vigente_hasta == date(1972, 2, 9)
    assert fila.creado_por_sistema is True


def test_migrar_usura_es_1_5_veces_ibc_en_las_filas_nuevas():
    session = session_module.get_session()
    _sembrar_solo_1997_en_adelante(session)
    session.close()

    migrar()

    session = session_module.get_session()
    filas_ibc = {
        fila.vigente_desde: fila.valor
        for fila in session.query(ParametroLegal)
        .filter(
            ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO",
            ParametroLegal.vigente_desde < _LIMITE_1997,
        )
        .all()
    }
    filas_usura = {
        fila.vigente_desde: fila.valor
        for fila in session.query(ParametroLegal)
        .filter(
            ParametroLegal.clave == "USURA_CONSUMO_ORDINARIO",
            ParametroLegal.vigente_desde < _LIMITE_1997,
        )
        .all()
    }
    session.close()

    assert len(filas_ibc) == len(_TRAMOS_PRE_1997)
    for vigente_desde, ibc in filas_ibc.items():
        esperado = (ibc * Decimal("1.5")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        assert filas_usura[vigente_desde] == esperado


def test_migrar_es_idempotente_segunda_corrida_no_duplica():
    session = session_module.get_session()
    _sembrar_solo_1997_en_adelante(session)
    session.close()

    primera = migrar()
    segunda = migrar()

    assert primera == 2 * len(_TRAMOS_PRE_1997)
    assert segunda == 0

    session = session_module.get_session()
    total = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO")
        .count()
    )
    session.close()
    assert total == len(_TRAMOS_IBC_USURA)


def test_migrar_sobre_bd_completamente_vacia_no_siembra_nada():
    # Guarda contra el footgun reportado en code review: si alguien invoca
    # este script suelto sobre una bastium.db nueva (sin ninguna fila
    # todavia de IBC_CONSUMO_ORDINARIO/USURA_CONSUMO_ORDINARIO), ANTES de
    # scripts/migrate_parametros_legales.py -- saltandose
    # aplicar_migraciones_pendientes(), que ya respeta el orden correcto --
    # este script debia abstenerse en vez de sembrar solo los tramos
    # pre-1997. Sembrar solo esos dejaba la clave en un estado que
    # migrate_parametros_legales.py ya no reconoce como "vacia" (su chequeo
    # es "la clave tiene alguna fila"), y esa clave se saltaria ENTERA para
    # siempre, sin que ningun otro script lo detectara ni corrigiera despues.
    sembradas = migrar()

    assert sembradas == 0
    session = session_module.get_session()
    total_ibc = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO")
        .count()
    )
    total_usura = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "USURA_CONSUMO_ORDINARIO")
        .count()
    )
    session.close()
    assert total_ibc == 0
    assert total_usura == 0


def test_migrar_sobre_bd_vacia_no_bloquea_la_siembra_completa_posterior():
    # Complemento del test anterior: confirma que abstenerse no deja la base
    # en un estado peor -- si despues (como hace aplicar_migraciones_pendientes()
    # en el orden correcto, o alguien que corrija el error de secuencia a mano)
    # se corre migrate_parametros_legales.py, este SI encuentra la clave
    # realmente vacia y siembra las 313 filas completas (1971-2026), sin que
    # la corrida previa de migrate_ibc_usura_1971_1997 haya dejado ningun
    # residuo pre-1997 a medias que estorbe.
    from scripts.migrate_parametros_legales import migrar as migrar_parametros_legales

    migrar()  # se abstiene (bd vacia) -- no debe dejar nada sembrado a medias
    migrar_parametros_legales()

    session = session_module.get_session()
    total_ibc = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO")
        .count()
    )
    session.close()
    assert total_ibc == len(_TRAMOS_IBC_USURA)


def test_migrar_sobre_clave_ya_extendida_desde_cero_no_hace_nada():
    # Si la clave ya se sembro entera (ej. migrate_parametros_legales.migrar()
    # en una bastium.db nueva, que ahora incluye los tramos pre-1997 porque ya
    # estan en _TRAMOS_IBC_USURA), este script no debe agregar nada.
    from scripts.migrate_parametros_legales import migrar as migrar_parametros_legales

    migrar_parametros_legales()

    sembradas = migrar()

    assert sembradas == 0
    session = session_module.get_session()
    total = (
        session.query(ParametroLegal)
        .filter(ParametroLegal.clave == "IBC_CONSUMO_ORDINARIO")
        .count()
    )
    session.close()
    assert total == len(_TRAMOS_IBC_USURA)
