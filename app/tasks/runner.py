"""
Ejecución de trabajo pesado fuera del hilo de la interfaz.

Leer un Excel de 200 MB o consolidar 30 archivos tarda segundos. Si eso corre en
el hilo de Qt, la ventana se congela y Windows la marca como "no responde".

`Tarea` envuelve cualquier función en un QRunnable y emite el resultado por
señales, que Qt entrega de vuelta en el hilo de la UI de forma segura. Es el
equivalente a lo que en Next resolvían async/await y SWR.

Uso:
    tarea = Tarea(cargar, slot, paths)
    tarea.senales.ok.connect(self._al_terminar)
    tarea.senales.error.connect(self._al_fallar)
    POOL.start(tarea)
"""

from __future__ import annotations

import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class SenalesTarea(QObject):
    ok = Signal(object)       # resultado de la función
    error = Signal(str)       # mensaje apto para mostrar al usuario
    terminada = Signal()      # siempre, haya ido bien o mal


class Tarea(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.senales = SenalesTarea()

    def run(self) -> None:  # se ejecuta en un hilo del pool
        try:
            resultado = self._fn(*self._args, **self._kwargs)
        except Exception as exc:
            traceback.print_exc()
            self.senales.error.emit(str(exc) or exc.__class__.__name__)
        else:
            self.senales.ok.emit(resultado)
        finally:
            self.senales.terminada.emit()


POOL = QThreadPool.globalInstance()
