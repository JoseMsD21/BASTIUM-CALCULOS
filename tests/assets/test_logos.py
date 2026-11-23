"""Sprint 122: los logos oficiales existen y son imagenes validas."""

import pytest
from PIL import Image

from app.assets import logos


@pytest.mark.parametrize("ruta", logos.TODOS_LOS_LOGOS, ids=lambda ruta: ruta.name)
def test_cada_logo_existe_y_es_una_imagen_valida(ruta):
    assert ruta.is_file(), f"falta {ruta}"
    with Image.open(ruta) as imagen:
        imagen.verify()


def test_los_logos_viven_en_la_carpeta_de_marca():
    for ruta in logos.TODOS_LOS_LOGOS:
        assert ruta.parent == logos.DIRECTORIO_MARCA


def test_icono_de_app_es_cuadrado():
    with Image.open(logos.ICONO_APP_PNG) as imagen:
        ancho, alto = imagen.size
    assert ancho == alto


def test_lema_oficial():
    assert logos.LEMA == "La ciencia de resolver lo complejo"
