import pytest

from app.core.exceptions import AreaNoImplementadaError
from app.engine.liquidation.registry import AreaRegistry
from app.services.area_strategy import (
    CivilFamiliaStrategy,
    ComercialStrategy,
    HonorariosStrategy,
    LaboralStrategy,
    SancionatorioStrategy,
)


def test_registry_expone_las_5_areas():
    areas = AreaRegistry.get_available_areas()
    assert set(areas.keys()) == {
        "CIVIL_FAMILIA",
        "COMERCIAL",
        "LABORAL",
        "SANCIONATORIO",
        "HONORARIOS",
    }


def test_civil_familia_es_la_unica_area_operable():
    strategy = AreaRegistry.get_strategy("CIVIL_FAMILIA")
    assert isinstance(strategy, CivilFamiliaStrategy)


@pytest.mark.parametrize(
    "area_name,strategy_cls",
    [
        ("COMERCIAL", ComercialStrategy),
        ("LABORAL", LaboralStrategy),
        ("SANCIONATORIO", SancionatorioStrategy),
        ("HONORARIOS", HonorariosStrategy),
    ],
)
def test_areas_no_implementadas_lanzan_error_claro_al_liquidar(area_name, strategy_cls):
    strategy = AreaRegistry.get_strategy(area_name)
    assert isinstance(strategy, strategy_cls)
    with pytest.raises(AreaNoImplementadaError):
        strategy.liquidar(obligaciones=[], abonos=[], fecha_corte=None)
