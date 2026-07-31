"""
Ventana principal: sidebar de navegación + área de contenido.

El sidebar se construye SOLO a partir de `app/catalog/hallazgos.py`. Agregar una
certificación o un hallazgo no requiere tocar este archivo: aparece solo.

Cada hallazgo tiene su propia entrada "Cargar Información". Las vistas se crean
de forma perezosa (la primera vez que se entra) y luego se reutilizan, así el
arranque es inmediato aunque haya seis pantallas con decenas de cards.
"""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QHBoxLayout, QLabel, QMainWindow, QPushButton, QStackedWidget,
    QVBoxLayout, QWidget,
)

from app import config
from app.catalog.hallazgos import Hallazgo, certificaciones
from app.ui import theme
from app.ui.cargar_view import CargarView


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Certificación de Accesos · Pacífico Seguros")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)

        self._vistas: dict[str, CargarView] = {}
        self._botones: dict[str, QPushButton] = {}

        central = QWidget()
        central.setObjectName("Canvas")
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._construir_sidebar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("Canvas")
        raiz.addWidget(self.stack, 1)

        self.setCentralWidget(central)

        primero = next(iter(self._botones.values()), None)
        if primero:
            primero.click()

    # ── sidebar ────────────────────────────────────────────────────────────
    def _construir_sidebar(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("Sidebar")
        barra.setFixedWidth(theme.SIDEBAR_WIDTH)

        layout = QVBoxLayout(barra)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        marca = QLabel("Certificación")
        marca.setObjectName("SidebarMarca")
        layout.addWidget(marca)

        submarca = QLabel("PACÍFICO SEGUROS")
        submarca.setObjectName("SidebarSubmarca")
        layout.addWidget(submarca)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)

        for cert in certificaciones():
            titulo = QLabel(cert.label.replace("Certificación de ", "").upper())
            titulo.setObjectName("SidebarGrupo")
            titulo.setWordWrap(True)
            layout.addWidget(titulo)

            for hallazgo in cert.hallazgos:
                boton = QPushButton(f"  {hallazgo.label}")
                boton.setObjectName("NavItem")
                boton.setCheckable(True)
                boton.setCursor(Qt.PointingHandCursor)
                boton.setToolTip(
                    f"{hallazgo.descripcion}\n"
                    f"{len(hallazgo.fuente_ids)} fuentes requeridas"
                )
                boton.clicked.connect(
                    lambda _=False, h=hallazgo: self._mostrar(h)
                )
                self._grupo.addButton(boton)
                self._botones[hallazgo.id] = boton
                layout.addWidget(boton)

        layout.addStretch(1)

        try:
            ruta = str(config.data_path())
        except RuntimeError:
            ruta = "DATA_PATH no configurado"
        pie = QLabel(ruta)
        pie.setObjectName("SidebarSubmarca")
        pie.setWordWrap(True)
        pie.setToolTip(ruta)
        layout.addWidget(pie)

        return barra

    # ── navegación ─────────────────────────────────────────────────────────
    def _mostrar(self, hallazgo: Hallazgo) -> None:
        vista = self._vistas.get(hallazgo.id)
        if vista is None:
            vista = CargarView(hallazgo)
            vista.progreso_cambiado.connect(self._actualizar_nav)
            self._vistas[hallazgo.id] = vista
            self.stack.addWidget(vista)
        else:
            # Otra pantalla pudo haber cargado o eliminado una fuente compartida.
            vista.refrescar()

        self.stack.setCurrentWidget(vista)
        self._botones[hallazgo.id].setChecked(True)

    def _actualizar_nav(self, hallazgo_id: str, cargadas: int, total: int) -> None:
        boton = self._botones.get(hallazgo_id)
        if not boton:
            return
        from app.catalog.hallazgos import get as get_hallazgo

        etiqueta = get_hallazgo(hallazgo_id).label
        marca = "  ●" if cargadas == total and total else ""
        boton.setText(f"  {etiqueta}{marca}")
        boton.setToolTip(f"{cargadas} de {total} archivos cargados")
