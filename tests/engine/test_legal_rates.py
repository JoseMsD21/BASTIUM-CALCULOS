from datetime import date, datetime
from decimal import Decimal

import pytest

import database.session as session_module
from app.engine.interest.legal_rates import LegalRates
from database.models import ParametroLegal


@pytest.fixture(autouse=True)
def _db_en_memoria():
    session = session_module.get_session()
    session.add(ParametroLegal(
        clave="CIVIL_ANNUAL_RATE", valor=Decimal("0.06"), vigente_desde=date(1900, 1, 1),
        vigente_hasta=None, usuario="test", motivo=None, creado_en=datetime.now(),
    ))
    session.commit()
    session.close()


def test_get_civil_daily_rate_365_dias():
    tasa = LegalRates.get_civil_daily_rate(date(2026, 1, 1))
    assert tasa == Decimal("0.06") / Decimal("365")


def test_get_civil_daily_rate_360_dias():
    tasa = LegalRates.get_civil_daily_rate(date(2026, 1, 1), use_360_days=True)
    assert tasa == Decimal("0.06") / Decimal("360")
