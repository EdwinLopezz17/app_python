from __future__ import annotations

import threading
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal

from app.telemetry import uso


class SenalesTarea(QObject):
    ok = Signal(object)
    error = Signal(str)
    excepcion = Signal(object)
    terminada = Signal()

_VIVAS: set["Tarea"] = set()
_CANDADO = threading.Lock()


class Tarea(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.senales = SenalesTarea()

        self.setAutoDelete(False)
        with _CANDADO:
            _VIVAS.add(self)

        self.senales.terminada.connect(self._olvidar)

    def _olvidar(self) -> None:
        with _CANDADO:
            _VIVAS.discard(self)

    def run(self) -> None:
        try:
            resultado = self._fn(*self._args, **self._kwargs)
        except Exception as exc:
            traceback.print_exc()
            uso.registrar_excepcion(
                "tarea_error", exc, funcion=getattr(self._fn, "__qualname__", str(self._fn))
            )
            self.senales.excepcion.emit(exc)
            self.senales.error.emit(str(exc) or exc.__class__.__name__)
        else:
            self.senales.ok.emit(resultado)
        finally:
            self.senales.terminada.emit()


def tareas_en_vuelo() -> int:
    with _CANDADO:
        return len(_VIVAS)


POOL = QThreadPool.globalInstance()
