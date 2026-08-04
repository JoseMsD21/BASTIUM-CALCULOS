from collections.abc import Callable
from typing import Any

from PySide6.QtCore import QObject, QRunnable, Signal


class SenalesTareaEnHilo(QObject):
    """Señales para reportar resultado/error de una `TareaEnHilo` al hilo principal.

    Viven en un QObject aparte (no en el QRunnable) porque QRunnable no hereda de
    QObject y por lo tanto no puede declarar señales de Qt directamente.
    """

    completada = Signal(object)
    fallo = Signal(object)


class TareaEnHilo(QRunnable):
    """QRunnable generico (Sprint 26): ejecuta `funcion(*args, **kwargs)` en el
    QThreadPool global y reporta el resultado (o la excepcion) de vuelta al hilo
    principal via señales Qt, en vez de bloquear el hilo de UI.

    La `funcion` recibida debe abrir y cerrar su propia sesion de SQLAlchemy con
    `database.session.get_session()` si necesita la base de datos -- SQLAlchemy no
    es thread-safe si se comparte una sesion ya abierta entre hilos.
    """

    def __init__(self, funcion: Callable[..., Any], *args: Any, **kwargs: Any):
        super().__init__()
        self.senales = SenalesTareaEnHilo()
        self._funcion = funcion
        self._args = args
        self._kwargs = kwargs

    def run(self) -> None:
        try:
            resultado = self._funcion(*self._args, **self._kwargs)
        except Exception as error:  # noqa: BLE001 - se reenvia tal cual al hilo principal
            self.senales.fallo.emit(error)
        else:
            self.senales.completada.emit(resultado)
