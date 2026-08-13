from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QSizePolicy,
    QVBoxLayout, QWidget,
)

from app.catalog.hallazgos import Hallazgo
from app.storage.files import estado_slot

ANCHO_MIN = 250
ANCHO_MAX = 300


class FilaEstado(QFrame):
    ir_a = Signal(str)

    def __init__(self, slot, fuente_label: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.slot = slot
        self.setObjectName("FilaEstado")
        self.setCursor(Qt.PointingHandCursor)

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(10, 7, 10, 7)
        raiz.setSpacing(8)

        self.punto = QLabel("○")
        self.punto.setObjectName("PuntoEstado")
        raiz.addWidget(self.punto)

        texto = QVBoxLayout()
        texto.setSpacing(1)

        etiqueta = fuente_label
        if slot.label and slot.label != fuente_label:
            etiqueta = f"{fuente_label} · {slot.label}"
        self.titulo = QLabel(etiqueta)
        self.titulo.setObjectName("FilaEstadoTitulo")
        self.titulo.setWordWrap(True)
        texto.addWidget(self.titulo)

        self.meta = QLabel()
        self.meta.setObjectName("FilaEstadoMeta")
        texto.addWidget(self.meta)

        raiz.addLayout(texto, 1)
        self.refrescar()

    def refrescar(self) -> bool:
        estado = estado_slot(self.slot)
        if estado.existe:
            self.punto.setText("✓")
            self.punto.setProperty("tono", "ok")
            if estado.filas:
                texto = f"{estado.filas:,} filas · {estado.modificado_texto}"
            else:
                texto = f"En disco · {estado.modificado_texto}"
            self.meta.setText(texto.replace(",", " "))
            self.setToolTip(str(estado.path))
        else:
            self.punto.setText("○")
            self.punto.setProperty("tono", "falta")
            self.meta.setText("Sin archivo")
            self.setToolTip("Aún no se ha cargado este archivo")

        self.punto.style().unpolish(self.punto)
        self.punto.style().polish(self.punto)
        return estado.existe

    def mousePressEvent(self, evento) -> None:
        self.ir_a.emit(self.slot.key)
        super().mousePressEvent(evento)


class PanelEstado(QWidget):
    ir_a_slot = Signal(str)
    cerrar = Signal()

    def __init__(self, hallazgo: Hallazgo, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.hallazgo = hallazgo
        self.setObjectName("PanelEstado")
        self.setMinimumWidth(ANCHO_MIN)
        self.setMaximumWidth(ANCHO_MAX)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        cabecera = QWidget()
        cabecera.setObjectName("PanelEstadoCabecera")
        cab = QVBoxLayout(cabecera)
        cab.setContentsMargins(16, 14, 12, 12)
        cab.setSpacing(6)

        fila = QHBoxLayout()
        titulo = QLabel("Estado de archivos")
        titulo.setObjectName("PanelTitulo")
        fila.addWidget(titulo)
        fila.addStretch(1)

        btn_cerrar = QPushButton("✕")
        btn_cerrar.setObjectName("BotonCerrarPanel")
        btn_cerrar.setFixedSize(24, 24)
        btn_cerrar.setCursor(Qt.PointingHandCursor)
        btn_cerrar.setToolTip("Ocultar panel")
        btn_cerrar.clicked.connect(self.cerrar.emit)
        fila.addWidget(btn_cerrar)
        cab.addLayout(fila)

        self.resumen = QLabel()
        self.resumen.setObjectName("PanelResumen")
        self.resumen.setWordWrap(True)
        cab.addWidget(self.resumen)

        btn_verificar = QPushButton("Verificar en disco")
        btn_verificar.setProperty("variante", "ghost")
        btn_verificar.setToolTip(
            "Vuelve a revisar la carpeta de datos para confirmar qué archivos "
            "existen realmente en disco. No lee el contenido de los archivos."
        )
        btn_verificar.clicked.connect(self.refrescar)
        cab.addWidget(btn_verificar)

        raiz.addWidget(cabecera)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        contenido = QWidget()
        contenido.setObjectName("PanelEstado")
        self._lista = QVBoxLayout(contenido)
        self._lista.setContentsMargins(10, 10, 10, 16)
        self._lista.setSpacing(4)

        self.filas: list[FilaEstado] = []
        for fuente in hallazgo.fuentes:
            for slot in fuente.slots:
                fila_estado = FilaEstado(slot, fuente.label)
                fila_estado.ir_a.connect(self.ir_a_slot.emit)
                self._lista.addWidget(fila_estado)
                self.filas.append(fila_estado)

        self._lista.addStretch(1)
        scroll.setWidget(contenido)
        raiz.addWidget(scroll, 1)

        self.refrescar()

    def refrescar(self) -> None:
        cargados = sum(1 for fila in self.filas if fila.refrescar())
        total = len(self.filas)
        faltan = total - cargados

        if faltan == 0:
            self.resumen.setText(f"Los {total} archivos están guardados.")
            self.resumen.setProperty("tono", "ok")
        else:
            self.resumen.setText(
                f"{cargados} de {total} guardados · falta{'n' if faltan > 1 else ''} {faltan}"
            )
            self.resumen.setProperty("tono", "aviso")

        self.resumen.style().unpolish(self.resumen)
        self.resumen.style().polish(self.resumen)
