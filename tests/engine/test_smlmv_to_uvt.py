from datetime import date
from decimal import Decimal

import pytest

from app.core.exceptions import UVTNoDisponibleError
from app.engine.indexation.smlmv_to_uvt import resolver_base_sancion


def test_hecho_pre_2020_usa_smlmv_del_anio_del_hecho():
    # SMLMV 2019 = 828116.00 (ver historical_index.py, verificado contra el PDF pag. 55-57).
    resultado = resolver_base_sancion(date(2019, 6, 1), Decimal("2"))
    assert resultado == Decimal("1656232.00")


def test_hecho_dia_anterior_al_corte_2020_usa_smlmv_2019():
    resultado = resolver_base_sancion(date(2019, 12, 31), Decimal("1"))
    assert resultado == Decimal("828116.00")


def test_hecho_exactamente_2020_01_01_ya_requiere_uvt_y_lanza_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2020, 1, 1), Decimal("1"))


def test_hecho_posterior_a_2020_lanza_uvt_no_disponible_error():
    with pytest.raises(UVTNoDisponibleError):
        resolver_base_sancion(date(2021, 1, 1), Decimal("1"))
