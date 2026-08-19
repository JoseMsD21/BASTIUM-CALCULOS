"""Sprint 81: cobertura de _TRAMOS_IBC_USURA/get_ibc_usura_for_date para el
rango 1971-10-29 a 1997-06-30, agregado a partir de docs/Archivos de
referencia abogado/_markdown/Historicocertificacionsuperfinancieratasasdeinteres.md
(columna "BANCARIO CORRIENTE" -- ver decision de mapeo documentada en el
bloque de comentarios que precede a _TRAMOS_IBC_USURA en historical_index.py
y en el docstring de scripts/migrate_ibc_usura_1971_1997.py).

Los tests de continuidad genericos (sin_vacios_ni_solapes, usura ==
1.5x ibc en TODOS los tramos) ya viven en tests/engine/test_historical_index.py
y cubren automaticamente estos tramos nuevos por ser generales sobre toda
_TRAMOS_IBC_USURA -- este archivo se enfoca en verificar valores puntuales
contra la fuente (al menos 3 tramos, en distintas decadas) y los limites del
rango extendido."""

from datetime import date, timedelta
from decimal import Decimal

import pytest

from app.engine.indexation.historical_index import (
    _TRAMOS_IBC_USURA,
    get_ibc_usura_for_date,
)


@pytest.fixture(autouse=True)
def _parametros_legales_en_memoria():
    # Mismo patron que tests/engine/test_historical_index.py: en una base en
    # memoria completamente nueva, migrate_parametros_legales.migrar() siembra
    # la clave entera desde cero -- incluye los tramos pre-1997 porque ya
    # estan en _TRAMOS_IBC_USURA al momento de la migracion.
    from scripts.migrate_parametros_legales import migrar

    migrar()


def test_primer_tramo_1971_10_29_coincide_con_la_fuente():
    # Resolucion 2865 (29-Oct-71 a 09-Feb-72), columna "Bancario corriente" =
    # 14.00% en la fuente.
    ibc, usura = get_ibc_usura_for_date(date(1971, 10, 29))
    assert ibc == Decimal("14.00")
    assert usura == Decimal("21.00")


def test_tramo_1984_resolucion_4815_coincide_con_la_fuente():
    # Resolucion 4815 (16-Oct-84 a 25-Mar-86), columna "Bancario corriente" =
    # 33.60% (CORRIENTE y BANCARIO CORRIENTE coinciden en esta fila de la
    # fuente).
    ibc, usura = get_ibc_usura_for_date(date(1985, 1, 1))
    assert ibc == Decimal("33.60")
    assert usura == Decimal("50.40")


def test_tramo_1993_resolucion_2150_coincide_con_la_fuente():
    # Resolucion 2150 (01-Jul-93 a 31-Ago-93), columna "Bancario corriente" =
    # 35.43%.
    ibc, usura = get_ibc_usura_for_date(date(1993, 7, 1))
    assert ibc == Decimal("35.43")
    assert usura == Decimal("53.15")


def test_ultimo_tramo_pre_1997_coincide_con_la_fuente():
    # Resolucion 0420 (01-May-97 a 30-Jun-97), columna "Bancario corriente" =
    # 36.99% -- el ultimo tramo antes de donde ya empezaba _TRAMOS_IBC_USURA
    # (1997-07-01, 36.50%/54.75%, sin cambios).
    ibc, usura = get_ibc_usura_for_date(date(1997, 6, 30))
    assert ibc == Decimal("36.99")
    assert usura == Decimal("55.49")


def test_limite_inferior_del_rango_extendido():
    with pytest.raises(ValueError):
        get_ibc_usura_for_date(date(1971, 10, 28))
    # No lanza para el primer dia cubierto.
    get_ibc_usura_for_date(date(1971, 10, 29))


def test_continuidad_en_la_frontera_1997_06_30_a_1997_07_01():
    ibc_antes, _ = get_ibc_usura_for_date(date(1997, 6, 30))
    ibc_despues, _ = get_ibc_usura_for_date(date(1997, 7, 1))
    assert ibc_antes == Decimal("36.99")
    assert ibc_despues == Decimal("36.50")


def test_tramos_pre_1997_sin_vacios_ni_solapes():
    tramos_pre_1997 = [t for t in _TRAMOS_IBC_USURA if t.fin < date(1997, 7, 1)]
    assert len(tramos_pre_1997) >= 40
    tramos_pre_1997.sort(key=lambda t: t.inicio)
    assert tramos_pre_1997[0].inicio == date(1971, 10, 29)
    assert tramos_pre_1997[-1].fin == date(1997, 6, 30)
    for anterior, actual in zip(tramos_pre_1997, tramos_pre_1997[1:], strict=False):
        assert actual.inicio == anterior.fin + timedelta(days=1), (
            f"Vacio o solape entre {anterior} y {actual}"
        )
