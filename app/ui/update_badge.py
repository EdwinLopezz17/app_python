from __future__ import annotations

from pathlib import Path

from app.update.bitacora import abrir_sesion, anotar, carpeta_logs, cerrar_sesion
from app.update.installer import carpeta_instalacion, es_escribible, lanzar_instalador

from PySide6.QtCore import QObject, QThread, Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QProgressBar, QPushButton, QSizePolicy,
    QTextEdit, QToolButton, QVBoxLayout, QWidget,
)

from app.__version__ import __version__
from app.update.checker import Actualizacion, buscar_actualizacion
from app.update.downloader import descargar, limpiar_descargas
from app.update.installer import lanzar_instalador


class _HiloBusqueda(QObject):
    listo = Signal(object)
    fallo = Signal(str)

    def ejecutar(self) -> None:
        try:
            self.listo.emit(buscar_actualizacion())
        except Exception as exc:
            self.fallo.emit(str(exc))


class _HiloDescarga(QObject):
    progreso = Signal(int, int)
    listo = Signal(object)
    fallo = Signal(str)

    def __init__(self, info: Actualizacion) -> None:
        super().__init__()
        self._info = info
        self._cancelado = False

    def cancelar(self) -> None:
        self._cancelado = True

    def ejecutar(self) -> None:
        try:
            ruta = descargar(
                self._info,
                progreso=lambda leido, total: self.progreso.emit(leido, total),
                cancelado=lambda: self._cancelado,
            )
            self.listo.emit(ruta)
        except Exception as exc:
            self.fallo.emit(str(exc))


def _mb(valor: int) -> str:
    return f"{valor / (1024 * 1024):.1f} MB"


class DialogoActualizacion(QDialog):

    def __init__(self, info: Actualizacion, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._info = info
        self._hilo: QThread | None = None
        self._tarea: _HiloDescarga | None = None
        self._archivo: Path | None = None

        self.setWindowTitle("Actualización disponible")
        self.setMinimumWidth(520)
        self.setObjectName("DialogoActualizacion")

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(24, 24, 24, 20)
        raiz.setSpacing(14)

        titulo = QLabel(f"Versión {info.version.lstrip('vV')} disponible")
        titulo.setObjectName("TituloDialogo")
        raiz.addWidget(titulo)

        actual = QLabel(f"Tenés instalada la versión {__version__}.")
        actual.setObjectName("SubtituloDialogo")
        raiz.addWidget(actual)

        if info.notas:
            notas = QTextEdit()
            notas.setReadOnly(True)
            notas.setPlainText(info.notas)
            notas.setMaximumHeight(180)
            notas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
            raiz.addWidget(notas)

        self.barra = QProgressBar()
        self.barra.setRange(0, 100)
        self.barra.setValue(0)
        self.barra.setVisible(False)
        self.barra.setTextVisible(True)
        raiz.addWidget(self.barra)

        self.estado = QLabel("")
        self.estado.setObjectName("EstadoDialogo")
        self.estado.setWordWrap(True)
        self.estado.setVisible(False)
        raiz.addWidget(self.estado)

        botones = QHBoxLayout()
        botones.addStretch(1)

        self.btn_despues = QPushButton("Después")
        self.btn_despues.clicked.connect(self.reject)
        botones.addWidget(self.btn_despues)

        self.btn_actualizar = QPushButton("Actualizar ahora")
        self.btn_actualizar.setDefault(True)
        self.btn_actualizar.setProperty("variante", "primario")
        self.btn_actualizar.clicked.connect(self._iniciar)
        botones.addWidget(self.btn_actualizar)

        raiz.addLayout(botones)

    def _iniciar(self) -> None:
        abrir_sesion(__version__, self._info.version)

        carpeta = carpeta_instalacion()
        if not es_escribible(carpeta):
            cerrar_sesion(False, f"Sin permiso de escritura en {carpeta}")
            self.estado.setVisible(True)
            self.estado.setText(
                f"No hay permiso de escritura en:\n{carpeta}\n\n"
                "Descargá el instalador manualmente desde GitHub y ejecutalo "
                "como administrador."
            )
            self.btn_actualizar.setEnabled(False)
            return

        anotar("Permisos OK. Iniciando descarga.")
        self.btn_actualizar.setEnabled(False)
        self.btn_despues.setText("Cancelar")
        self.barra.setVisible(True)
        self.estado.setVisible(True)
        self.estado.setText("Descargando actualización...")

        self._hilo = QThread(self)
        self._tarea = _HiloDescarga(self._info)
        self._tarea.moveToThread(self._hilo)
        self._hilo.started.connect(self._tarea.ejecutar)
        self._tarea.progreso.connect(self._al_progresar)
        self._tarea.listo.connect(self._al_descargar)
        self._tarea.fallo.connect(self._al_fallar)
        self._hilo.start()

    def _al_progresar(self, leido: int, total: int) -> None:
        if total > 0:
            self.barra.setRange(0, 100)
            self.barra.setValue(int(leido * 100 / total))
            self.estado.setText(f"Descargando  {_mb(leido)} de {_mb(total)}")
        else:
            self.barra.setRange(0, 0)
            self.estado.setText(f"Descargando  {_mb(leido)}")

    def _al_descargar(self, ruta: Path) -> None:
        self._archivo = ruta
        self._detener_hilo()
        self.barra.setRange(0, 100)
        self.barra.setValue(100)
        self.estado.setText(
            "Descarga verificada. La aplicación se cerrará para instalar "
            "la nueva versión y volverá a abrirse automáticamente."
        )
        self.btn_despues.setEnabled(False)

        anotar("Descarga verificada (SHA-256 coincide).")
        try:
            limpiar_descargas(conservar=ruta)
            lanzar_instalador(ruta)
        except Exception as exc:
            cerrar_sesion(False, str(exc))
            self._al_fallar(str(exc))
            return
        self.accept()

    def _al_fallar(self, mensaje: str) -> None:
        cerrar_sesion(False, mensaje)
        self._detener_hilo()
        self.barra.setVisible(False)
        self.estado.setVisible(True)
        self.estado.setText(mensaje)
        self.btn_actualizar.setEnabled(True)
        self.btn_despues.setEnabled(True)
        self.btn_despues.setText("Cerrar")
        self.estado.setText(f"{mensaje}\n\nDetalle en: {carpeta_logs()}")

    def _detener_hilo(self) -> None:
        if self._hilo is not None:
            self._hilo.quit()
            self._hilo.wait(3000)
            self._hilo = None
            self._tarea = None

    def reject(self) -> None:
        if self._tarea is not None:
            self._tarea.cancelar()
        self._detener_hilo()
        super().reject()


class BadgeActualizacion(QToolButton):
    actualizacion_lista = Signal(object)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("BadgeUpdate")
        self.setCursor(Qt.PointingHandCursor)
        self.setText("Actualizar")
        self.setVisible(False)
        self.setStyleSheet(
            "QToolButton#BadgeUpdate {"
            "  background: #fff1e0;"
            "  color: #964400;"
            "  border: 1px solid #ffb68c;"
            "  border-radius: 4px;"
            "  padding: 4px 12px;"
            "  font-size: 12px;"
            "  font-weight: 600;"
            "}"
            "QToolButton#BadgeUpdate:hover {"
            "  background: #ffe3c7;"
            "  border-color: #bc5800;"
            "}"
        )
        self.clicked.connect(self._abrir_dialogo)

        self._info: Actualizacion | None = None
        self._hilo: QThread | None = None
        self._tarea: _HiloBusqueda | None = None

    def buscar(self) -> None:
        if self._hilo is not None:
            return

        self._hilo = QThread(self)
        self._tarea = _HiloBusqueda()
        self._tarea.moveToThread(self._hilo)
        self._hilo.started.connect(self._tarea.ejecutar)
        self._tarea.listo.connect(self._al_encontrar)
        self._tarea.fallo.connect(self._al_fallar)
        self._hilo.start()

    def _al_encontrar(self, info: object) -> None:
        self._limpiar()
        if isinstance(info, Actualizacion):
            self._info = info
            version = info.version.lstrip("vV")
            self.setText(f"Versión {version} disponible")
            self.setToolTip(f"Actualizar a la versión {version}")
            self.setVisible(True)
            self.actualizacion_lista.emit(info)

    def _al_fallar(self, mensaje: str) -> None:
        self._limpiar()
        self.setToolTip(mensaje)

    def _limpiar(self) -> None:
        if self._hilo is not None:
            self._hilo.quit()
            self._hilo.wait(3000)
            self._hilo = None
            self._tarea = None

    def _abrir_dialogo(self) -> None:
        if self._info is None:
            return
        dialogo = DialogoActualizacion(self._info, self.window())
        if dialogo.exec() == QDialog.Accepted:
            from PySide6.QtWidgets import QApplication
            QApplication.quit()
