from PySide6.QtCore import Qt
from PySide6.QtWidgets import QPushButton, QWidget

from app.views.toast import mostrar_toast


def _parent_visible(qtbot) -> QWidget:
    parent = QWidget()
    qtbot.addWidget(parent)
    parent.resize(400, 300)
    parent.show()
    qtbot.waitExposed(parent)
    return parent


def test_mostrar_toast_aparece_con_el_mensaje_correcto(qtbot):
    parent = _parent_visible(qtbot)

    toast = mostrar_toast(parent, "Obligación guardada")

    assert toast.isVisible()
    assert toast.text() == "Obligación guardada"


def test_mostrar_toast_se_autooculta_tras_su_timeout(qtbot):
    parent = _parent_visible(qtbot)

    toast = mostrar_toast(parent, "Listo", duracion_ms=50)

    assert toast.isVisible()
    qtbot.waitUntil(lambda: not toast.isVisible(), timeout=1000)


def test_mostrar_toast_no_bloquea_la_interaccion_con_el_resto_de_la_ventana(qtbot):
    parent = _parent_visible(qtbot)
    boton = QPushButton("Clic", parent)
    boton.move(10, 10)
    boton.show()
    contador = {"clics": 0}
    boton.clicked.connect(lambda: contador.__setitem__("clics", contador["clics"] + 1))

    mostrar_toast(parent, "Guardado", duracion_ms=5000)

    qtbot.mouseClick(boton, Qt.MouseButton.LeftButton)

    assert contador["clics"] == 1
