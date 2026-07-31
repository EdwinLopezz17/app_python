from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup, QFrame, QHBoxLayout, QLabel, QMainWindow, QMenu, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)

from app import config
from app.catalog.hallazgos import certificaciones, get as get_hallazgo
from app.ui import theme
from app.ui.cargar_view import CargarView
from app.ui.hallazgo_view import HallazgoView
from app.ui.launcher_view import LauncherView

INICIO = "__inicio__"


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Certificación de Accesos · Pacífico Seguros")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)

        self._cargar_views: dict[str, CargarView] = {}
        self._hallazgo_views: dict[str, HallazgoView] = {}
        self._botones: dict[str, QPushButton] = {}
        self._botones_cert: dict[str, QPushButton] = {}

        central = QWidget()
        central.setObjectName("Canvas")
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        raiz.addWidget(self._construir_navbar())

        self.stack = QStackedWidget()
        self.stack.setObjectName("Canvas")

        self.launcher = LauncherView()
        self.launcher.ir_cargar.connect(self.abrir_cargar)
        self.launcher.ir_generar.connect(self.abrir_hallazgo)
        self.stack.addWidget(self.launcher)

        raiz.addWidget(self.stack, 1)
        self.setCentralWidget(central)

        self.abrir_inicio()

    def _construir_navbar(self) -> QWidget:
        barra = QWidget()
        barra.setObjectName("NavBar")
        barra.setFixedHeight(58)

        layout = QHBoxLayout(barra)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(4)

        marca_box = QVBoxLayout()
        marca_box.setSpacing(0)
        marca = QLabel("Certificación de Accesos")
        marca.setObjectName("Marca")
        marca_box.addWidget(marca)
        submarca = QLabel("PACÍFICO SEGUROS")
        submarca.setObjectName("Submarca")
        marca_box.addWidget(submarca)
        layout.addLayout(marca_box)

        separador = QFrame()
        separador.setFrameShape(QFrame.VLine)
        separador.setStyleSheet(f"color: {theme.OUTLINE_VARIANT};")
        layout.addSpacing(16)
        layout.addWidget(separador)
        layout.addSpacing(8)

        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)

        inicio = QPushButton("Inicio")
        inicio.setObjectName("NavTab")
        inicio.setCheckable(True)
        inicio.setCursor(Qt.PointingHandCursor)
        inicio.clicked.connect(self.abrir_inicio)
        self._grupo.addButton(inicio)
        self._botones[INICIO] = inicio
        layout.addWidget(inicio)

        for cert in certificaciones():
            boton = QPushButton(cert.label.replace("Certificación de ", ""))
            boton.setObjectName("NavTab")
            boton.setCheckable(True)
            boton.setCursor(Qt.PointingHandCursor)

            menu = QMenu(boton)
            for hallazgo in cert.hallazgos:
                accion = menu.addAction(hallazgo.label)
                accion.setToolTip(hallazgo.descripcion)
                accion.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.abrir_hallazgo(hid)
                )
                sub = menu.addAction(f"      Cargar información…")
                sub.triggered.connect(
                    lambda _=False, hid=hallazgo.id: self.abrir_cargar(hid)
                )
                menu.addSeparator()
            boton.setMenu(menu)

            self._grupo.addButton(boton)
            self._botones_cert[cert.id] = boton
            layout.addWidget(boton)

        layout.addStretch(1)

        try:
            ruta = str(config.data_path())
        except RuntimeError:
            ruta = "DATA_PATH no configurado"
        destino = QLabel(f"Datos: {Path(ruta).name or ruta}")
        destino.setObjectName("Submarca")
        destino.setToolTip(ruta)
        layout.addWidget(destino)

        return barra

    def abrir_inicio(self) -> None:
        self.launcher.refrescar()
        self.stack.setCurrentWidget(self.launcher)
        self._botones[INICIO].setChecked(True)

    def abrir_cargar(self, hallazgo_id: str) -> None:
        vista = self._cargar_views.get(hallazgo_id)
        if vista is None:
            vista = CargarView(get_hallazgo(hallazgo_id))
            vista.ir_hallazgo.connect(self.abrir_hallazgo)
            vista.ir_inicio.connect(self.abrir_inicio)
            vista.progreso_cambiado.connect(self._al_cambiar_carga)
            self._cargar_views[hallazgo_id] = vista
            self.stack.addWidget(vista)
        else:
            vista.refrescar()

        self.stack.setCurrentWidget(vista)
        self._marcar_cert(hallazgo_id)

    def abrir_hallazgo(self, hallazgo_id: str) -> None:
        vista = self._hallazgo_views.get(hallazgo_id)
        if vista is None:
            vista = HallazgoView(get_hallazgo(hallazgo_id))
            vista.ir_cargar.connect(self.abrir_cargar)
            vista.cambiado.connect(self.launcher.refrescar)
            self._hallazgo_views[hallazgo_id] = vista
            self.stack.addWidget(vista)
        else:
            vista.refrescar()

        self.stack.setCurrentWidget(vista)
        self._marcar_cert(hallazgo_id)

    def _marcar_cert(self, hallazgo_id: str) -> None:
        boton = self._botones_cert.get(get_hallazgo(hallazgo_id).cert_id)
        if boton:
            boton.setChecked(True)

    def _al_cambiar_carga(self, hallazgo_id: str, cargadas: int, total: int) -> None:
        self.launcher.refrescar()
        for hid, vista in self._hallazgo_views.items():
            if hid != hallazgo_id:
                vista.refrescar()
