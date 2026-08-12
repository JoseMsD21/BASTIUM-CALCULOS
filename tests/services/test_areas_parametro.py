import pytest

from database.models import AreaDerecho


def test_serializar_y_deserializar_son_inversas():
    from app.services.areas_parametro import deserializar_areas, serializar_areas

    areas = [AreaDerecho.CIVIL_FAMILIA, AreaDerecho.LABORAL]
    texto = serializar_areas(areas)
    assert deserializar_areas(texto) == areas


def test_serializar_rechaza_lista_vacia():
    from app.services.areas_parametro import serializar_areas

    with pytest.raises(ValueError):
        serializar_areas([])


def test_serializar_guarda_como_lista_json_de_codigos():
    from app.services.areas_parametro import serializar_areas

    texto = serializar_areas([AreaDerecho.CIVIL_FAMILIA, AreaDerecho.LABORAL])
    assert texto == '["CIVIL_FAMILIA", "LABORAL"]'


def test_area_unidad_por_clave_cubre_las_40_claves_del_catalogo():
    """39 claves del Sprint 57 + IPC_VARIACION_ANUAL (Sprint 58, dato crudo
    del que se deriva IPC_INDICE_ACUMULADO -- ver CLAVE_CRUDA_DE)."""
    from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE
    from app.services.parametro_service import CATALOGO_PARAMETROS

    assert set(AREA_UNIDAD_POR_CLAVE.keys()) == set(CATALOGO_PARAMETROS.keys())
    assert len(AREA_UNIDAD_POR_CLAVE) == 40


def test_area_unidad_por_clave_cada_entrada_tiene_al_menos_un_area_y_una_unidad():
    from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE

    for clave, (areas, unidad) in AREA_UNIDAD_POR_CLAVE.items():
        assert len(areas) >= 1, f"{clave} sin area"
        assert all(isinstance(area, AreaDerecho) for area in areas), clave
        assert unidad.strip(), f"{clave} sin unidad"


def test_area_unidad_por_clave_casos_conocidos_de_la_spec():
    from app.services.areas_parametro import AREA_UNIDAD_POR_CLAVE

    assert AREA_UNIDAD_POR_CLAVE["USURA_MULTIPLICADOR"] == ([AreaDerecho.COMERCIAL], "veces")
    assert AREA_UNIDAD_POR_CLAVE["PRESCRIPCION_EJECUTIVA_MESES"] == (
        [
            AreaDerecho.CIVIL_FAMILIA,
            AreaDerecho.COMERCIAL,
            AreaDerecho.LABORAL,
            AreaDerecho.SANCIONATORIO,
            AreaDerecho.HONORARIOS,
            AreaDerecho.TRIBUTARIO,
        ],
        "meses",
    )
    assert AREA_UNIDAD_POR_CLAVE["SMLMV"] == (
        [
            AreaDerecho.CIVIL_FAMILIA,
            AreaDerecho.LABORAL,
            AreaDerecho.SANCIONATORIO,
            AreaDerecho.COMERCIAL,
            AreaDerecho.HONORARIOS,
        ],
        "COP",
    )
    assert AREA_UNIDAD_POR_CLAVE["CADUCIDAD_ENRIQUECIMIENTO_SIN_CAUSA_MESES"] == (
        [AreaDerecho.CIVIL_FAMILIA, AreaDerecho.COMERCIAL],
        "meses",
    )
