from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton,
    QSizePolicy, QVBoxLayout, QWidget,
)

from app.catalog.fuentes import Fuente, Slot
from app.ingest.validate import formato_permitido
from app.ingest.writer import ErrorDeCarga, cargar
from app.storage.files import EstadoSlot, eliminar_slot, estado_slot
from app.tasks.runner import POOL, Tarea
from app.ui.responsive import ContenedorFlow

FILTRO_ARCHIVOS = "Reportes (*.csv *.xls *.xlsx);;Todos los archivos (*)"


def _badge(texto: str, tono: str) -> QLabel:
    etiqueta = QLabel(texto)
    etiqueta.setObjectName("Badge")
    etiqueta.setProperty("tono", tono)
    etiqueta.setAlignment(Qt.AlignCenter)
    return etiqueta


class Desplegable(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._titulo = ""

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(4)

        self.boton = QPushButton()
        self.boton.setObjectName("Desplegable")
        self.boton.setCursor(Qt.PointingHandCursor)
        self.boton.setCheckable(True)
        self.boton.toggled.connect(self._alternar)
        raiz.addWidget(self.boton)

        self.lista = QLabel()
        self.lista.setObjectName("ListaColumnas")
        self.lista.setWordWrap(True)
        self.lista.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.lista.hide()
        raiz.addWidget(self.lista)

    def _alternar(self, abierto: bool) -> None:
        self.lista.setVisible(abierto)
        self.boton.setText(self._etiqueta(abierto))

    def _etiqueta(self, abierto: bool) -> str:
        return f"{'▾' if abierto else '▸'}  {self._titulo}"

    def poblar(self, titulo: str, items: list[str], tono: str = "",
               abierto: bool = False) -> None:
        self._titulo = f"{titulo} ({len(items)})"
        self.lista.setText("\n".join(f"·  {i}" for i in items))

        for widget in (self.lista, self.boton):
            widget.setProperty("tono", tono)
            widget.style().unpolish(widget)
            widget.style().polish(widget)

        self.boton.blockSignals(True)
        self.boton.setChecked(abierto)
        self.boton.blockSignals(False)
        self.lista.setVisible(abierto)
        self.boton.setText(self._etiqueta(abierto))
        self.setVisible(bool(items))


class SlotRow(QWidget):
    cambiado = Signal()
    ver_datos = Signal(object)
    alerta_error = Signal(bool)

    def __init__(self, slot: Slot, mostrar_label: bool, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slot = slot
        self._ocupado = False
        self._ultimas_faltantes: list[str] = []
        self.setAcceptDrops(True)

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

        self.meta = QLabel("Arrastra el archivo aquí o selecciónalo")
        self.meta.setObjectName("CardMeta")
        self.meta.setWordWrap(True)
        raiz.addWidget(self.meta)

        self.alerta = QFrame()
        self.alerta.setObjectName("Alerta")
        alerta_layout = QVBoxLayout(self.alerta)
        alerta_layout.setContentsMargins(10, 8, 10, 8)
        alerta_layout.setSpacing(4)

        self.alerta_titulo = QLabel()
        self.alerta_titulo.setObjectName("AlertaTitulo")
        self.alerta_titulo.setWordWrap(True)
        alerta_layout.addWidget(self.alerta_titulo)

        self.alerta_detalle = QLabel()
        self.alerta_detalle.setObjectName("AlertaDetalle")
        self.alerta_detalle.setWordWrap(True)
        alerta_layout.addWidget(self.alerta_detalle)

        self.alerta.hide()
        raiz.addWidget(self.alerta)


        self.desp_columnas = Desplegable()
        raiz.addWidget(self.desp_columnas)

        self.desp_archivos = Desplegable()
        self.desp_archivos.hide()
        raiz.addWidget(self.desp_archivos)

        self._pintar_columnas([])

        # Flow en vez de fila fija: con la card angosta (1 o 2 columnas) los
        # botones bajan de línea en lugar de forzar el ancho de toda la grilla.
        acciones = ContenedorFlow(espacio_h=6, espacio_v=6)

        self.btn_cargar = QPushButton("Seleccionar archivo")
        self.btn_cargar.setProperty("variante", "ghost")
        self.btn_cargar.setCursor(Qt.PointingHandCursor)
        self.btn_cargar.setToolTip("Buscar el archivo en el disco")
        self.btn_cargar.clicked.connect(self._elegir_archivos)
        acciones.agregar(self.btn_cargar)

        self.btn_ver = QPushButton("Ver datos")
        self.btn_ver.setProperty("variante", "ghost")
        self.btn_ver.setCursor(Qt.PointingHandCursor)
        self.btn_ver.setToolTip("Previsualizar las filas ya guardadas")
        self.btn_ver.clicked.connect(lambda: self.ver_datos.emit(self.slot))
        acciones.agregar(self.btn_ver)

        self.btn_borrar = QPushButton("Eliminar")
        self.btn_borrar.setProperty("variante", "ghost")
        self.btn_borrar.setProperty("tono", "peligro")
        self.btn_borrar.setCursor(Qt.PointingHandCursor)
        self.btn_borrar.setToolTip("Quitar del disco el archivo cargado")
        self.btn_borrar.clicked.connect(self._eliminar)
        acciones.agregar(self.btn_borrar)

        raiz.addWidget(acciones)

        self.refrescar()

    def refrescar(self) -> None:
        estado = estado_slot(self.slot)
        self._pintar(estado)

    def _pintar(self, estado: EstadoSlot) -> None:
        if self._ocupado:
            return
        if estado.existe:
            self.badge.setText("CARGADO")
            self.badge.setProperty("tono", "ok")

            partes = [
                f"{estado.filas:,} filas".replace(",", " "),
                f"{estado.columnas} columnas",
            ]
            if estado.total_archivos:
                plural = "archivos" if estado.total_archivos != 1 else "archivo"
                partes.append(f"{estado.total_archivos} {plural}")
            partes += [estado.tamano_texto, estado.modificado_texto]
            self.meta.setText(" · ".join(partes))

            self.btn_cargar.setText("Reemplazar")
            self.desp_archivos.poblar("Archivos cargados", estado.archivos)
        else:
            self.badge.setText("PENDIENTE")
            self.badge.setProperty("tono", "pendiente")
            self.meta.setText("Arrastra el archivo aquí o selecciónalo")
            self.btn_cargar.setText("Seleccionar archivo")
            self.desp_archivos.poblar("Archivos cargados", [])

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
        self._ocultar_alerta()
        nombres = ", ".join(Path(r).name for r in rutas[:2])
        if len(rutas) > 2:
            nombres += f" y {len(rutas) - 2} más"
        self._ocupar(f"Procesando {nombres}…")

        tarea = Tarea(cargar, self.slot, rutas)
        tarea.senales.ok.connect(self._al_cargar)
        tarea.senales.excepcion.connect(self._guardar_detalle)
        tarea.senales.error.connect(self._al_fallar)
        POOL.start(tarea)

    def _guardar_detalle(self, exc) -> None:
        self._ultimas_faltantes = list(getattr(exc, "faltantes", []) or [])

    def _pintar_columnas(self, faltantes: list[str]) -> None:
        if faltantes:
            self.desp_columnas.poblar(
                "Columnas faltantes", faltantes, tono="error", abierto=True
            )
        else:
            self.desp_columnas.poblar("Columnas requeridas", list(self.slot.columns))

    def _al_cargar(self, resultado) -> None:
        self._liberar()


        self._ocultar_alerta()
        self._pintar_columnas([])
        self.cambiado.emit()

    def _al_fallar(self, mensaje: str) -> None:
        self._ocupado = False
        self.btn_cargar.setEnabled(True)
        self.badge.setText("ERROR")
        self.badge.setProperty("tono", "error")
        self._repintar_estilo(self.badge)
        self.meta.setText("No se cargó ningún archivo")

        faltantes = self._ultimas_faltantes
        if faltantes:
            self._mostrar_alerta(
                f"Faltan {len(faltantes)} columna(s) requerida(s)",
                "Revisa el detalle en «Columnas faltantes».",
            )
            self._pintar_columnas(faltantes)
            self._ultimas_faltantes = []
        else:
            self._mostrar_alerta("No se pudo cargar el archivo", mensaje)
        self.cambiado.emit()

    def _mostrar_alerta(self, titulo: str, detalle: str = "", tono: str = "error") -> None:
        self.alerta.setProperty("tono", tono)
        self.alerta_titulo.setText(titulo)
        self.alerta_detalle.setText(detalle)
        self.alerta_detalle.setVisible(bool(detalle))
        self._repintar_estilo(self.alerta)
        self._repintar_estilo(self.alerta_titulo)
        self.alerta.show()
        self.alerta_error.emit(tono == "error")

    def _ocultar_alerta(self) -> None:
        self.alerta.hide()
        self.alerta_error.emit(False)

    def _rutas_validas(self, evento) -> list[str]:
        if not evento.mimeData().hasUrls():
            return []
        rutas = [
            url.toLocalFile() for url in evento.mimeData().urls()
            if url.isLocalFile() and formato_permitido(url.toLocalFile())
        ]
        if not self.slot.multiple and len(rutas) > 1:
            return []
        return rutas

    def _marcar_zona(self, activa: bool) -> None:
        self.setProperty("soltar", "activa" if activa else "")
        self._repintar_estilo(self)

    def dragEnterEvent(self, evento: QDragEnterEvent) -> None:
        if self._ocupado or not self._rutas_validas(evento):
            evento.ignore()
            return
        evento.acceptProposedAction()
        self._marcar_zona(True)

    def dragMoveEvent(self, evento) -> None:
        if self._ocupado or not self._rutas_validas(evento):
            evento.ignore()
            return
        evento.acceptProposedAction()

    def dragLeaveEvent(self, evento: QDragLeaveEvent) -> None:
        self._marcar_zona(False)
        evento.accept()

    def dropEvent(self, evento: QDropEvent) -> None:
        self._marcar_zona(False)
        rutas = self._rutas_validas(evento)
        if not rutas:
            evento.ignore()
            return
        evento.acceptProposedAction()
        self._cargar(rutas)

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
