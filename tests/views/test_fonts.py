from app.assets.fonts import FAMILIA_ANCIZAR_SANS, cargar_fuentes_ancizar_sans


def test_familia_ancizar_sans_es_el_nombre_registrado_por_qt():
    assert FAMILIA_ANCIZAR_SANS == "Ancizar Sans"


def test_cargar_fuentes_ancizar_sans_registra_la_familia_esperada(qtbot):
    familia = cargar_fuentes_ancizar_sans()

    assert familia == FAMILIA_ANCIZAR_SANS


def test_cargar_fuentes_ancizar_sans_es_idempotente(qtbot):
    primera = cargar_fuentes_ancizar_sans()
    segunda = cargar_fuentes_ancizar_sans()

    assert primera == segunda == FAMILIA_ANCIZAR_SANS
