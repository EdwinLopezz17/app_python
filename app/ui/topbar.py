"""Barra superior de navegación, equivalente al `TopBar.tsx` del Next.js.

Reemplaza al sidebar lateral. La app de referencia no tiene sidebar: su
`AppShell` son tres franjas apiladas — barra oscura de navegación, cabecera de
control panel (migas + título + acciones, que cada vista ya construye), y el
contenido con scroll.

La barra tiene tres zonas:

    [ switcher de certificación ] │ [ menús de hallazgos ]        [ buscar ]

Cada menú es un hallazgo, y su desplegable lleva las hojas de ese hallazgo
(Hallazgos / Cargar Información / Generar Resumen). El botón muestra la hoja
activa a su derecha —«Aplicaciones / Cargar Información»— igual que el
`subPath` del `MenuButton` de la referencia, para desambiguar hojas que se
llaman igual en distintos hallazgos.
"""

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
    """Contenedor que despliega un QMenu al pulsarlo, alineado a su borde."""

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
        # Un QWidget plano no pinta el `background` del QSS salvo que se le
        # active WA_StyledBackground; sin esto la barra salía del color del
        # canvas y los botones flotaban sobre fondo claro.
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setFixedHeight(theme.TOPBAR_ALTO)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)

        self._certs = certificaciones()
        self._activa: Certificacion = self._certs[0]
        self._ruta = INICIO
        #: hallazgo_id -> botón de menú, para poder marcar el activo.
        self._menus: dict[str, QToolButton] = {}

        raiz = QHBoxLayout(self)
        raiz.setContentsMargins(10, 0, 10, 0)
        raiz.setSpacing(4)

        raiz.addWidget(self._construir_switcher())
        raiz.addWidget(self._separador_vertical())

        # Los menús viven en un scroll horizontal: con la certificación de
        # Usuarios son varios botones y en una ventana de 900 px no caben.
        # Antes que truncarlos o apilarlos, se desplazan.
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

        raiz.addWidget(self._construir_busqueda())

        self._reconstruir_menus()
        self.marcar(INICIO)

    # ------------------------------------------------------------------
    # Construcción
    # ------------------------------------------------------------------

    def _separador_vertical(self) -> QFrame:
        linea = QFrame()
        linea.setObjectName("TopBarSep")
        linea.setFixedWidth(1)
        linea.setFixedHeight(24)
        return linea

    def _construir_switcher(self) -> QWidget:
        """Icono + «CERTIFICACIÓN / <nombre>» + chevron, como la referencia.

        Es un QFrame y no un QToolButton: el QToolButton calcula su ancho a
        partir de su propio texto e ignora el del layout hijo, así que el
        contenido quedaba colapsado a la primera letra. El menú se abre desde
        `mousePressEvent`.
        """
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
            "Paleta de navegación (disponible en la próxima entrega)"
        )
        self.btn_buscar.setFixedHeight(theme.TOPBAR_ALTO - 22)
        # Deshabilitado pero legible: un disabled con el gris por defecto de Qt
        # sobre el navy queda invisible. El QSS le da su propio color atenuado.
        self.btn_buscar.setEnabled(False)
        self.btn_buscar.clicked.connect(self.abrir_busqueda.emit)
        return self.btn_buscar

    def _reconstruir_menus(self) -> None:
        """Menús de primer nivel, con el árbol de `certifications.ts`.

        La referencia NO pone un botón por hallazgo. El árbol de cada
        certificación es:

            Hallazgos                (grupo, sin destino propio)
              └ Aplicaciones         → Generar Resumen
              └ Active Directory     → Generar Resumen
            Cargar Información       (hoja directa)

        O sea dos botones de primer nivel. Los hallazgos son el SEGUNDO nivel,
        dentro del desplegable de «Hallazgos», y «Generar Resumen» cuelga del
        hallazgo al que pertenece.

        Divergencia consciente: en la web «Cargar Información» es una sola
        pantalla por certificación; aquí cada hallazgo tiene sus propias
        fuentes, así que ese botón despliega la lista de hallazgos en vez de
        navegar directo. Es la única forma de mantener la jerarquía de la web
        sin inventarse una pantalla que no existe.
        """
        while self._menus_layout.count():
            item = self._menus_layout.takeAt(0)
            if item.widget() is not None:
                item.widget().deleteLater()
        self._menus.clear()

        hallazgos = self._activa.hallazgos

        # ── Botón 1: Hallazgos ──────────────────────────────────────────
        menu_hallazgos = QMenu(self)
        for hallazgo in hallazgos:
            if resumenes.disponible(hallazgo.id):
                # Nodo con hijos: submenú que repite el propio hallazgo como
                # primera fila, igual que el `treeItems` del MenuButton.
                sub = menu_hallazgos.addMenu(hallazgo.label)
                accion = sub.addAction("Hallazgos")
                accion.setToolTip(hallazgo.descripcion)
                accion.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.ir_hallazgo.emit(hid)
                )
                accion = sub.addAction("Generar Resumen")
                accion.setToolTip(
                    "Resumen por escenarios a partir del Excel de detalle."
                )
                accion.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.ir_resumen.emit(hid)
                )
            else:
                accion = menu_hallazgos.addAction(hallazgo.label)
                accion.setToolTip(hallazgo.descripcion)
                accion.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.ir_hallazgo.emit(hid)
                )

        self._agregar_menu("hallazgos", "Hallazgos", menu_hallazgos)

        # ── Botón 2: Cargar Información ─────────────────────────────────
        menu_cargar = QMenu(self)
        for hallazgo in hallazgos:
            accion = menu_cargar.addAction(hallazgo.label)
            accion.setToolTip(f"Archivos fuente de {hallazgo.label}.")
            accion.triggered.connect(
                lambda _=False, hid=hallazgo.id: self.ir_cargar.emit(hid)
            )

        self._agregar_menu("cargar", "Cargar Información", menu_cargar)

        self._menus_layout.addStretch(1)

    def _agregar_menu(self, clave: str, etiqueta: str, menu: QMenu) -> None:
        boton = QToolButton()
        boton.setObjectName("TopBarMenu")
        boton.setCursor(Qt.PointingHandCursor)
        boton.setPopupMode(QToolButton.InstantPopup)
        boton.setText(etiqueta)
        boton.setMenu(menu)
        boton.setProperty("base", etiqueta)
        self._menus_layout.addWidget(boton)
        self._menus[clave] = boton

    # ------------------------------------------------------------------
    # Estado
    # ------------------------------------------------------------------

    def _elegir_cert(self, cert_id: str) -> None:
        cert = next(c for c in self._certs if c.id == cert_id)
        self.ir_hallazgo.emit(cert.landing)

    def marcar(self, ruta: str) -> None:
        """Sincroniza la barra con la vista abierta."""
        self._ruta = ruta
        vista, _, hallazgo_id = ruta.partition(":")

        if hallazgo_id:
            cert_id = get_hallazgo(hallazgo_id).cert_id
            if cert_id != self._activa.id:
                self._activa = next(c for c in self._certs if c.id == cert_id)
                self._reconstruir_menus()

        self.lbl_cert.setText(self._activa.label_corto)
        self.btn_switcher.setToolTip(self._activa.descripcion)

        # Qué botón de primer nivel está activo, y qué camino cuelga de él.
        # Equivale al `subPath` del MenuButton: los segmentos más profundos que
        # el propio botón, para desambiguar hojas homónimas entre hallazgos.
        activo = ""
        cola: list[str] = []
        if hallazgo_id:
            etiqueta = get_hallazgo(hallazgo_id).label
            if vista == "cargar":
                activo, cola = "cargar", [etiqueta]
            elif vista == "hallazgo":
                activo, cola = "hallazgos", [etiqueta]
            elif vista == "resumen":
                activo, cola = "hallazgos", [etiqueta, "Generar Resumen"]

        for clave, boton in self._menus.items():
            base = boton.property("base")
            if clave == activo and cola:
                boton.setText(f"{base}  /  {'  /  '.join(cola)}")
            else:
                boton.setText(base)
            boton.setProperty("activo", "si" if clave == activo else "")
            boton.style().unpolish(boton)
            boton.style().polish(boton)

    def ruta_actual(self) -> str:
        return self._ruta

    def ruta_datos(self) -> str:
        try:
            return str(config.data_path())
        except RuntimeError:
            return "DATA_PATH no configurado"


class PieDatos(QLabel):
    """Ruta de datos, que antes vivía en el pie del sidebar.

    Se conserva porque es la única pista visible de dónde escribe la app, y al
    quitar el sidebar se habría perdido. Va en la esquina inferior de la
    ventana, discreta.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("PieDatos")
        try:
            ruta = str(config.data_path())
        except RuntimeError:
            ruta = "DATA_PATH no configurado"
        self.setText(f"PACÍFICO SEGUROS  ·  Datos: {Path(ruta).name or ruta}")
        self.setToolTip(ruta)
