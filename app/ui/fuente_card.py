"""
Card de una fuente en la pantalla de Cargar Información.

Equivale a `FuenteCard.tsx`. Cada card puede tener uno o varios slots (Active
Directory tiene AD PPS y AD Vida; GDH tiene Activos y Cesados), y cada slot es
un archivo independiente en disco.

El estado NO se guarda en ningún lado: se lee del disco cada vez que se llama a
`refrescar()`. Por eso, si el usuario carga DNI vs Usuarios desde el hallazgo de
Aplicaciones y luego entra al de Base de Datos, la card ya aparece cargada.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import Fuente, Slot
from app.ingest.writer import ErrorDeCarga, cargar
from app.storage.files import EstadoSlot, eliminar_slot, estado_slot
from app.tasks.runner import POOL, Tarea

FILTRO_ARCHIVOS = "Reportes (*.csv *.xls *.xlsx);;Todos los archivos (*)"


def _badge(texto: str, tono: str) -> QLabel:
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("Badge")
    etiqueta.setProperty("tono", tono)
    etiqueta.setAlignment(Qt.AlignCenter)
    return etiqueta


class SlotRow(QWidget):
    """Una fila dentro de la card: un archivo concreto."""

    cambiado = Signal()
    ver_datos = Signal(object)  # Slot

    def __init__(self, slot: Slot, mostrar_label: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slot = slot
        self._ocupado = False

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(6)

        cabecera = QHBoxLayout()
        cabecera.setSpacing(8)

        if mostrar_label:
            titulo = QLabel(slot.display_label)
            titulo.setStyleSheet("font-weight:600; font-size:13px;")
            cabecera.addWidget(titulo)

        self.badge = _badge("PENDIENTE", "pendiente")
        cabecera.addWidget(self.badge)
        cabecera.addStretch(1)
        raiz.addLayout(cabecera)

        self.meta = QLabel("Sin archivo cargado")
        self.meta.setObjectName("CardMeta")
        self.meta.setWordWrap(True)
        raiz.addWidget(self.meta)

        acciones = QHBoxLayout()
        acciones.setSpacing(6)

        self.btn_cargar = QPushButton("Seleccionar archivo")
        self.btn_cargar.setProperty("variante", "ghost")
        self.btn_cargar.clicked.connect(self._elegir_archivos)
        acciones.addWidget(self.btn_cargar)

        self.btn_ver = QPushButton("Ver")
        self.btn_ver.setProperty("variante", "ghost")
        self.btn_ver.clicked.connect(lambda: self.ver_datos.emit(self.slot))
        acciones.addWidget(self.btn_ver)

        self.btn_borrar = QPushButton("Eliminar")
        self.btn_borrar.setProperty("variante", "ghost")
        self.btn_borrar.clicked.connect(self._eliminar)
        acciones.addWidget(self.btn_borrar)

        acciones.addStretch(1)
        raiz.addLayout(acciones)

        self.refrescar()

    # ── estado ─────────────────────────────────────────────────────────────
    def refrescar(self) -> None:
        estado = estado_slot(self.slot)
        self._pintar(estado)

    def _pintar(self, estado: EstadoSlot) -> None:
        if self._ocupado:
            return
        if estado.existe:
            self.badge.setText("CARGADO")
            self.badge.setProperty("tono", "ok")
            self.meta.setText(
                f"{estado.filas:,} filas · {estado.columnas} columnas · "
                f"{estado.tamano_texto} · {estado.modificado_texto}".replace(",", " ")
            )
            self.btn_cargar.setText("Reemplazar")
        else:
            self.badge.setText("PENDIENTE")
            self.badge.setProperty("tono", "pendiente")
            self.meta.setText("Sin archivo cargado")
            self.btn_cargar.setText("Seleccionar archivo")

        self.btn_ver.setEnabled(estado.existe)
        self.btn_borrar.setEnabled(estado.existe)
        self._repintar_estilo(self.badge)

    @staticmethod
    def _repintar_estilo(widget: QWidget) -> None:
        widget.style().unpolish(widget)
        widget.style().polish(widget)

    def _ocupar(self, mensaje: str) -> None:
        self._ocupado = True
        self.badge.setText("PROCESANDO")
        self.badge.setProperty("tono", "aviso")
        self._repintar_estilo(self.badge)
        self.meta.setText(mensaje)
        self.btn_cargar.setEnabled(False)
        self.btn_borrar.setEnabled(False)
        self.btn_ver.setEnabled(False)

    def _liberar(self) -> None:
        self._ocupado = False
        self.btn_cargar.setEnabled(True)
        self.refrescar()

    # ── acciones ───────────────────────────────────────────────────────────
    def _elegir_archivos(self) -> None:
        if self.slot.multiple:
            rutas, _ = QFileDialog.getOpenFileNames(
                self, f"Seleccionar archivos · {self.slot.display_label}", "", FILTRO_ARCHIVOS
            )
        else:
            ruta, _ = QFileDialog.getOpenFileName(
                self, f"Seleccionar archivo · {self.slot.display_label}", "", FILTRO_ARCHIVOS
            )
            rutas = [ruta] if ruta else []

        if rutas:
            self._cargar(rutas)

    def _cargar(self, rutas: list[str]) -> None:
        nombres = ", ".join(Path(r).name for r in rutas[:2])
        if len(rutas) > 2:
            nombres += f" y {len(rutas) - 2} más"
        self._ocupar(f"Procesando {nombres}…")

        tarea = Tarea(cargar, self.slot, rutas)
        tarea.senales.ok.connect(self._al_cargar)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _al_cargar(self, resultado) -> None:
        self._liberar()
        if resultado.validacion.extra:
            self.meta.setText(
                f"{self.meta.text()} · {len(resultado.validacion.extra)} columna(s) "
                "adicional(es) ignorada(s)"
            )
        self.cambiado.emit()

    def _al_fallar(self, mensaje: str) -> None:
        self._ocupado = False
        self.btn_cargar.setEnabled(True)
        self.badge.setText("ERROR")
        self.badge.setProperty("tono", "error")
        self._repintar_estilo(self.badge)
        self.meta.setText(mensaje)
        self.cambiado.emit()

    def _eliminar(self) -> None:
        confirmar = QMessageBox.question(
            self, "Eliminar archivo",
            f"¿Eliminar el archivo cargado de «{self.slot.display_label}»?\n\n"
            "Es el mismo archivo que usan los demás hallazgos que dependen de "
            "esta fuente.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No,
        )
        if confirmar != QMessageBox.Yes:
            return
        eliminar_slot(self.slot)
        self.refrescar()
        self.cambiado.emit()


class FuenteCard(QFrame):
    cambiado = Signal()
    ver_datos = Signal(object)

    def __init__(self, fuente: Fuente, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.fuente = fuente
        self.setObjectName("Card")
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(16, 14, 16, 14)
        raiz.setSpacing(10)

        titulo = QLabel(fuente.label)
        titulo.setObjectName("CardTitulo")
        titulo.setWordWrap(True)
        raiz.addWidget(titulo)

        self.filas: list[SlotRow] = []
        mostrar_label = len(fuente.slots) > 1
        for indice, slot in enumerate(fuente.slots):
            if indice:
                separador = QFrame()
                separador.setFrameShape(QFrame.HLine)
                separador.setStyleSheet("color:#e2e7ff;")
                raiz.addWidget(separador)
            fila = SlotRow(slot, mostrar_label, self)
            fila.cambiado.connect(self.cambiado.emit)
            fila.ver_datos.connect(self.ver_datos.emit)
            raiz.addWidget(fila)
            self.filas.append(fila)

    def refrescar(self) -> None:
        for fila in self.filas:
            fila.refrescar()
        completo = all(estado_slot(f.slot).existe for f in self.filas)
        self.setProperty("estado", "cargado" if completo else "")
        self.style().unpolish(self)
        self.style().polish(self)
