
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QMenu, QPushButton, QScrollArea, QSizePolicy,
    QToolButton, QVBoxLayout, QWidget,
)

from app import config
from app.catalog import resumenes
from app.catalog.hallazgos import (
    Certificacion, certificaciones, get as get_hallazgo,
)
from app.ui import theme

INICIO = "inicio"


def ruta_hallazgo(hallazgo_id: str) -> str:
    return f"hallazgo:{hallazgo_id}"


def ruta_cargar(hallazgo_id: str) -> str:
    return f"cargar:{hallazgo_id}"


def ruta_resumen(hallazgo_id: str) -> str:
    return f"resumen:{hallazgo_id}"


class _Pulsable(QFrame):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.menu: QMenu | None = None

    def mousePressEvent(self, evento) -> None:
        if self.menu is not None and evento.button() == Qt.LeftButton:
            self.menu.exec(self.mapToGlobal(self.rect().bottomLeft()))
        super().mousePressEvent(evento)


class TopBar(QWidget):
    ir_inicio = Signal()
    ir_hallazgo = Signal(str)
    ir_cargar = Signal(str)
    ir_resumen = Signal(str)
    abrir_busqueda = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("BarraNav")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(theme.TOPBAR_ALTO)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._certs = certificaciones()
        self._activa: Certificacion = self._certs[0]
        self._ruta = INICIO
        self._submenus: dict[str, QMenu] = {}
        self._menus: dict[str, QToolButton] = {}

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(10, 0, 10, 0)
        raiz.setSpacing(4)

        raiz.addWidget(self._construir_switcher())
        raiz.addWidget(self._separador_vertical())

        self._zona_menus = QWidget()
        self._zona_menus.setObjectName("BarraNav")
        self._zona_menus.setAttribute(Qt.WA_StyledBackground, True)
        self._menus_layout = QHBoxLayout(self._zona_menus)
        self._menus_layout.setContentsMargins(0, 0, 0, 0)
        self._menus_layout.setSpacing(2)

        self._scroll_menus = QScrollArea()
        self._scroll_menus.setObjectName("TopBarScroll")
        self._scroll_menus.setWidgetResizable(True)
        self._scroll_menus.setFrameShape(QFrame.NoFrame)
        self._scroll_menus.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self._scroll_menus.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self._scroll_menus.setWidget(self._zona_menus)
        raiz.addWidget(self._scroll_menus, 1)

        self._raiz = raiz
        self._slot_badge = raiz.count()

        raiz.addWidget(self._construir_busqueda())

        self._reconstruir_menus()
        self.marcar(INICIO)


    def _separador_vertical(self) -> QFrame:
        linea = QFrame()
        linea.setObjectName("TopBarSep")
        linea.setFixedWidth(1)
        linea.setFixedHeight(24)
        return linea

    def _construir_switcher(self) -> QWidget:
        self.btn_switcher = _Pulsable()
        self.btn_switcher.setObjectName("CertSwitcher")
        self.btn_switcher.setCursor(Qt.PointingHandCursor)

        fila = QHBoxLayout(self.btn_switcher)
        fila.setContentsMargins(7, 5, 10, 5)
        fila.setSpacing(9)

        self.marca = QLabel("CA")
        self.marca.setObjectName("CertMarca")
        self.marca.setFixedSize(30, 30)
        self.marca.setAlignment(Qt.AlignCenter)
        fila.addWidget(self.marca)

        textos = QVBoxLayout()
        textos.setContentsMargins(0, 0, 0, 0)
        textos.setSpacing(0)

        eyebrow = QLabel("CERTIFICACIÓN")
        eyebrow.setObjectName("CertEyebrow")
        textos.addWidget(eyebrow)

        self.lbl_cert = QLabel(self._activa.label_corto)
        self.lbl_cert.setObjectName("CertNombre")
        textos.addWidget(self.lbl_cert)

        fila.addLayout(textos)

        chevron = QLabel("⌄")
        chevron.setObjectName("CertChevron")
        fila.addWidget(chevron)

        self.btn_switcher.setFixedHeight(theme.TOPBAR_ALTO - 14)

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
        self.btn_switcher.menu = menu

        return self.btn_switcher

    def _construir_busqueda(self) -> QWidget:
        self.btn_buscar = QPushButton("Buscar…      Ctrl K")
        self.btn_buscar.setObjectName("BuscarGlobal")
        self.btn_buscar.setCursor(Qt.PointingHandCursor)
        self.btn_buscar.setToolTip(
            "Buscar hallazgo, pantalla o fuente en todas las certificaciones"
            "   (Ctrl+K)"
        )
        self.btn_buscar.setFixedHeight(theme.TOPBAR_ALTO - 22)
        self.btn_buscar.clicked.connect(self.abrir_busqueda.emit)
        return self.btn_buscar

    def _reconstruir_menus(self) -> None:
        while self._menus_layout.count():
            item = self._menus_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.hide()
                widget.setParent(None)
                widget.deleteLater()
        self._menus.clear()

        menu = QMenu(self)
        menu.setObjectName("MenuNav")
        menu.addSection(self._activa.label_corto)

        for hallazgo in self._activa.hallazgos:
            sub = menu.addMenu(hallazgo.label)
            sub.setObjectName("MenuNav")
            sub.setToolTip(hallazgo.descripcion)

            accion = sub.addAction("Cargar Información")
            accion.setToolTip(f"Archivos fuente de {hallazgo.label}.")
            accion.triggered.connect(
                lambda _=False, hid=hallazgo.id: self.ir_cargar.emit(hid)
            )

            accion = sub.addAction("Ver Hallazgos")
            accion.setToolTip(hallazgo.descripcion)
            accion.triggered.connect(
                lambda _=False, hid=hallazgo.id: self.ir_hallazgo.emit(hid)
            )

            if resumenes.disponible(hallazgo.id):
                accion = sub.addAction("Generar Resumen")
                accion.setToolTip(
                    "Resumen por escenarios a partir del Excel de detalle."
                )
                accion.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.ir_resumen.emit(hid)
                )

            self._submenus[hallazgo.id] = sub

        self.btn_certificar = QToolButton()
        self.btn_certificar.setObjectName("BotonCertificar")
        self.btn_certificar.setCursor(Qt.PointingHandCursor)
        self.btn_certificar.setPopupMode(QToolButton.InstantPopup)
        self.btn_certificar.setText("Certificar   ⌄")
        self.btn_certificar.setToolTip(
            "Hallazgos de esta certificación y sus acciones"
        )
        self.btn_certificar.setMenu(menu)
        self._menus_layout.addWidget(self.btn_certificar)
        self._menus_layout.addStretch(1)


    def _elegir_cert(self, cert_id: str) -> None:
        cert = next(c for c in self._certs if c.id == cert_id)
        self.ir_hallazgo.emit(cert.landing)

    def marcar(self, ruta: str) -> None:
        self._ruta = ruta
        vista, _, hallazgo_id = ruta.partition(":")

        if hallazgo_id:
            cert_id = get_hallazgo(hallazgo_id).cert_id
            if cert_id != self._activa.id:
                self._activa = next(c for c in self._certs if c.id == cert_id)
                self._reconstruir_menus()

        self.lbl_cert.setText(self._activa.label_corto)
        self.btn_switcher.setToolTip(self._activa.descripcion)

        hojas = {
            "cargar": "Cargar Información",
            "hallazgo": "Ver Hallazgos",
            "resumen": "Generar Resumen",
        }

        if hallazgo_id and vista in hojas:
            etiqueta = get_hallazgo(hallazgo_id).label
            self.btn_certificar.setText(
                f"Certificar  /  {etiqueta}  /  {hojas[vista]}   ⌄"
            )
            self.btn_certificar.setProperty("activo", "si")
        else:
            self.btn_certificar.setText("Certificar   ⌄")
            self.btn_certificar.setProperty("activo", "")

        self.btn_certificar.style().unpolish(self.btn_certificar)
        self.btn_certificar.style().polish(self.btn_certificar)

    def montar_badge(self, badge: QWidget) -> None:
        badge.setParent(self)
        self._raiz.insertWidget(self._slot_badge, badge)

    def ruta_actual(self) -> str:
        return self._ruta

    def ruta_datos(self) -> str:
        try:
            return str(config.data_path())
        except RuntimeError:
            return "DATA_PATH no configurado"


class PieDatos(QLabel):

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PieDatos")
        try:
            ruta = str(config.data_path())
        except RuntimeError:
            ruta = "DATA_PATH no configurado"
        self.setText(f"Datos: {Path(ruta).name or ruta}")
        self.setToolTip(ruta)
