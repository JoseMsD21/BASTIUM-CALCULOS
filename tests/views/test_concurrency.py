import threading

from PySide6.QtCore import QThreadPool

from app.views.concurrency import TareaEnHilo


def test_tarea_en_hilo_emite_completada_con_el_resultado_de_la_funcion(qtbot):
    tarea = TareaEnHilo(lambda x, y: x + y, 2, 3)

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert blocker.args == [5]


def test_tarea_en_hilo_emite_fallo_con_la_excepcion_si_la_funcion_lanza(qtbot):
    def funcion_que_falla():
        raise ValueError("boom")

    tarea = TareaEnHilo(funcion_que_falla)

    with qtbot.waitSignal(tarea.senales.fallo, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert isinstance(blocker.args[0], ValueError)
    assert str(blocker.args[0]) == "boom"


def test_tarea_en_hilo_se_ejecuta_en_un_hilo_distinto_al_principal(qtbot):
    hilo_de_ejecucion = []
    tarea = TareaEnHilo(lambda: hilo_de_ejecucion.append(threading.current_thread().ident))

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000):
        QThreadPool.globalInstance().start(tarea)

    assert hilo_de_ejecucion[0] != threading.main_thread().ident


def test_tarea_en_hilo_pasa_kwargs_a_la_funcion(qtbot):
    tarea = TareaEnHilo(lambda base, exponente=1: base**exponente, 2, exponente=10)

    with qtbot.waitSignal(tarea.senales.completada, timeout=2000) as blocker:
        QThreadPool.globalInstance().start(tarea)

    assert blocker.args == [1024]
