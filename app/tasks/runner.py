from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class SenalesTarea(QObject):
    ok = Signal(object)
    error = Signal(str)
    excepcion = Signal(object)
    terminada = Signal()


class Tarea(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.senales = SenalesTarea()

    def run(self) -> None:
        try:
            resultado = self._fn(*self._args, **self._kwargs)
        except Exception as exc:
            traceback.print_exc()
            self.senales.excepcion.emit(exc)
            self.senales.error.emit(str(exc) or exc.__class__.__name__)
        else:
            self.senales.ok.emit(resultado)
        finally:
            self.senales.terminada.emit()


POOL = QThreadPool.globalInstance()
