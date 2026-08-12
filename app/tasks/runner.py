from __future__ import annotations

import threading
import traceback
from typing import Any, Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal


class SenalesTarea(QObject):
    ok = Signal(object)
    error = Signal(str)
    excepcion = Signal(object)
    terminada = Signal()


# Referencias fuertes a las tareas en vuelo.
#
# QThreadPool destruye el QRunnable en cuanto run() retorna (autoDelete). Si
# nadie guarda una referencia, el objeto SenalesTarea muere con él y las
# señales encoladas hacia el hilo de UI se descartan en silencio: la UI se
# queda con el botón en "Generando…" aunque el trabajo haya terminado bien.
# Mantenemos la tarea viva hasta que 'terminada' se procesa en el hilo de UI.
_VIVAS: set["Tarea"] = set()
_CANDADO = threading.Lock()


class Tarea(QRunnable):
    def __init__(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self._fn = fn
        self._args = args
        self._kwargs = kwargs
        self.senales = SenalesTarea()

        # Qt no borra el objeto; la vida la controla Python vía _VIVAS.
        self.setAutoDelete(False)
        with _CANDADO:
            _VIVAS.add(self)
        # SenalesTarea se crea en el hilo de UI, así que esta conexión es
        # encolada y el descarte ocurre después de que los slots del usuario
        # ya corrieron.
        self.senales.terminada.connect(self._olvidar)

    def _olvidar(self) -> None:
        with _CANDADO:
            _VIVAS.discard(self)

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


def tareas_en_vuelo() -> int:
    with _CANDADO:
        return len(_VIVAS)


POOL = QThreadPool.globalInstance()
