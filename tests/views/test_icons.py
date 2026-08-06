import pytest
from PySide6.QtGui import QIcon

from app.views.icons import ICONOS_DISPONIBLES, icon, icono_aplicacion

_NOMBRES_ICONOS_SPRINT_34 = {
    "home", "back", "settings", "save", "cancel", "delete", "export", "info", "warning",
}


def test_iconos_disponibles_incluye_info_y_warning_agregados_en_sprint_34():
    assert ICONOS_DISPONIBLES == frozenset(_NOMBRES_ICONOS_SPRINT_34)


@pytest.mark.parametrize("nombre", sorted(_NOMBRES_ICONOS_SPRINT_34))
def test_icon_carga_cada_icono_del_set_minimo_sin_estar_vacio(qtbot, nombre):
    resultado = icon(nombre)

    assert isinstance(resultado, QIcon)
    assert not resultado.isNull()


def test_icon_con_nombre_desconocido_lanza_valueerror(qtbot):
    with pytest.raises(ValueError):
        icon("no_existe")


def test_icono_aplicacion_carga_el_icono_de_ventana(qtbot):
    resultado = icono_aplicacion()

    assert isinstance(resultado, QIcon)
    assert not resultado.isNull()
