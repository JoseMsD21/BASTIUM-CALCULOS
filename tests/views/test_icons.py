import pytest
from PySide6.QtGui import QIcon

from app.views.icons import ICONOS_DISPONIBLES, icon, icono_aplicacion


def test_iconos_disponibles_tiene_exactamente_el_set_minimo_del_sprint_31():
    assert ICONOS_DISPONIBLES == frozenset(
        {"home", "back", "settings", "save", "cancel", "delete", "export"}
    )


@pytest.mark.parametrize(
    "nombre", sorted({"home", "back", "settings", "save", "cancel", "delete", "export"})
)
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
