"""Sidebar de navegación.

Réplica del árbol del front Next.js (`src/config/certifications.ts` +
`Sidebar.tsx`): un switcher de certificación arriba —estilo menú de apps— y
debajo el árbol de la certificación activa.

    Certificación de Usuarios      ← switcher
      HALLAZGOS                    ← grupo (no navegable)
        Aplicaciones               ← /hallazgos/aplicaciones
          Cargar Información       ← /hallazgos/aplicaciones/cargar-informacion
        Active Directory
          Cargar Información

Diferencia deliberada con el front: allá «Cargar Información» cuelga de la
certificación; aquí cuelga de cada hallazgo, porque `CargarView` recibe un
`Hallazgo` y cada uno tiene su propio juego de fuentes. La forma del árbol
(grupo → hallazgo → hoja) es la misma.

Las rutas se identifican con una clave de texto (`inicio`,
`hallazgo:<id>`, `cargar:<id>`) que hace de pathname.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QLabel, QMenu, QPushButton, QScrollArea,
    QStackedWidget, QVBoxLayout, QWidget,
)

from app import config
from app.catalog.hallazgos import Certificacion, certificaciones, get as get_hallazgo
from app.ui import theme

INICIO = "inicio"


def ruta_hallazgo(hallazgo_id: str) -> str:
    return f"hallazgo:{hallazgo_id}"


def ruta_cargar(hallazgo_id: str) -> str:
    return f"cargar:{hallazgo_id}"


class Sidebar(QWidget):

    ir_inicio = Signal()
    ir_hallazgo = Signal(str)
    ir_cargar = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("Sidebar")
        self.setFixedWidth(theme.SIDEBAR_WIDTH)

        self._certs = certificaciones()
        self._activa: Certificacion = self._certs[0]
        self._botones: dict[str, QPushButton] = {}
        self._paneles: dict[str, QWidget] = {}

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._construir_switcher())
        raiz.addWidget(self._separador())

        self._stack = QStackedWidget()
        for cert in self._certs:
            panel = self._construir_nav(cert)
            self._paneles[cert.id] = panel
            self._stack.addWidget(panel)
        raiz.addWidget(self._stack, 1)

        raiz.addWidget(self._separador())
        raiz.addWidget(self._construir_pie())

        self.marcar(INICIO)

    # ── Construcción ──────────────────────────────────────────────────────

    def _separador(self) -> QFrame:
        linea = QFrame()
        linea.setObjectName("SidebarSep")
        linea.setFixedHeight(1)
        return linea

    def _construir_switcher(self) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("Sidebar")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        eyebrow = QLabel("CERTIFICACIÓN DE ACCESOS")
        eyebrow.setObjectName("SidebarEyebrow")
        layout.addWidget(eyebrow)

        self.btn_switcher = QPushButton()
        self.btn_switcher.setObjectName("CertSwitcher")
        self.btn_switcher.setCursor(Qt.PointingHandCursor)

        menu = QMenu(self.btn_switcher)
        for cert in self._certs:
            accion = menu.addAction(cert.label_corto)
            accion.setToolTip(cert.descripcion)
            accion.triggered.connect(
                lambda _=False, cid=cert.id: self._elegir_cert(cid)
            )
        menu.addSeparator()
        todas = menu.addAction("Todas las certificaciones")
        todas.triggered.connect(self.ir_inicio.emit)
        self.btn_switcher.setMenu(menu)

        layout.addWidget(self.btn_switcher)
        return contenedor

    def _construir_nav(self, cert: Certificacion) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        contenido = QWidget()
        contenido.setObjectName("Sidebar")
        layout = QVBoxLayout(contenido)
        layout.setContentsMargins(0, 6, 0, 12)
        layout.setSpacing(1)

        grupo = QLabel("HALLAZGOS")
        grupo.setObjectName("SidebarGrupo")
        layout.addWidget(grupo)

        for hallazgo in cert.hallazgos:
            layout.addWidget(self._item(
                hallazgo.label,
                ruta_hallazgo(hallazgo.id),
                lambda hid=hallazgo.id: self.ir_hallazgo.emit(hid),
                nivel=1,
                tooltip=hallazgo.descripcion,
            ))
            layout.addWidget(self._item(
                "Cargar Información",
                ruta_cargar(hallazgo.id),
                lambda hid=hallazgo.id: self.ir_cargar.emit(hid),
                nivel=2,
                tooltip=f"Archivos fuente de {hallazgo.label}.",
            ))

        layout.addStretch(1)
        scroll.setWidget(contenido)
        return scroll

    def _item(self, etiqueta: str, ruta: str, accion, nivel: int,
              tooltip: str = "") -> QPushButton:
        boton = QPushButton(etiqueta)
        boton.setObjectName("NavItem")
        boton.setCheckable(True)
        boton.setCursor(Qt.PointingHandCursor)
        boton.setToolTip(tooltip)
        boton.setStyleSheet(f"padding-left: {10 + nivel * 12}px;")
        boton.clicked.connect(lambda: accion())
        self._grupo.addButton(boton)
        self._botones[ruta] = boton
        return boton

    def _construir_pie(self) -> QWidget:
        contenedor = QWidget()
        contenedor.setObjectName("Sidebar")
        layout = QVBoxLayout(contenedor)
        layout.setContentsMargins(14, 10, 14, 12)
        layout.setSpacing(2)

        marca = QLabel("PACÍFICO SEGUROS")
        marca.setObjectName("SidebarEyebrow")
        layout.addWidget(marca)

        try:
            ruta = str(config.data_path())
        except RuntimeError:
            ruta = "DATA_PATH no configurado"
        destino = QLabel(f"Datos: {Path(ruta).name or ruta}")
        destino.setObjectName("SidebarPie")
        destino.setToolTip(ruta)
        layout.addWidget(destino)
        return contenedor

    # ── Navegación ────────────────────────────────────────────────────────

    def _elegir_cert(self, cert_id: str) -> None:
        """Entrar a una certificación abre su hallazgo de entrada (landing)."""
        cert = next(c for c in self._certs if c.id == cert_id)
        self.ir_hallazgo.emit(cert.landing)

    def marcar(self, ruta: str) -> None:
        """Sincroniza el sidebar con la vista visible (equivale al `pathname`)."""
        if ruta != INICIO:
            hallazgo_id = ruta.split(":", 1)[1]
            cert_id = get_hallazgo(hallazgo_id).cert_id
            self._activa = next(c for c in self._certs if c.id == cert_id)

        self._stack.setCurrentWidget(self._paneles[self._activa.id])
        self.btn_switcher.setText(self._activa.label_corto)
        self.btn_switcher.setToolTip(self._activa.descripcion)

        self._grupo.setExclusive(False)
        for clave, boton in self._botones.items():
            boton.setChecked(clave == ruta)
        self._grupo.setExclusive(True)
