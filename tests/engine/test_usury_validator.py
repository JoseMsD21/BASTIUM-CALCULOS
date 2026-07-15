from decimal import Decimal

import pytest

from app.core.exceptions import TasaUsurariaError
from app.engine.interest.usury_validator import validar_tasa_usura


def test_tasa_por_debajo_del_tope_no_lanza_error():
    validar_tasa_usura(Decimal("20.00"), Decimal("20.00"), "remuneratoria")


def test_tasa_exactamente_en_el_tope_no_lanza_error():
    validar_tasa_usura(Decimal("30.00"), Decimal("20.00"), "moratoria")


def test_tasa_por_encima_del_tope_lanza_tasa_usuraria_error():
    with pytest.raises(TasaUsurariaError):
        validar_tasa_usura(Decimal("30.01"), Decimal("20.00"), "moratoria")


def test_mensaje_de_error_nombra_la_etiqueta_y_el_tope():
    with pytest.raises(TasaUsurariaError, match="moratoria"):
        validar_tasa_usura(Decimal("35.00"), Decimal("20.00"), "moratoria")
