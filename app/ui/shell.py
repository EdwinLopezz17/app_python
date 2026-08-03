from __future__ import annotations

from PySide6.QtWidgets import (
    QHBoxLayout, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from app.catalog.hallazgos import get as get_hallazgo
from app.ui.cargar_view import CargarView
from app.ui.hallazgo_view import HallazgoView
from app.ui.launcher_view import LauncherView
from app.ui.resumen_view import ResumenView
from app.ui.sidebar import (
    INICIO, Sidebar, ruta_cargar, ruta_hallazgo, ruta_resumen,
)


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Certificación de Accesos · Pacífico Seguros")
        self.resize(1440, 900)
        self.setMinimumSize(1180, 720)

        self._cargar_views: dict[str, CargarView] = {}
        self._hallazgo_views: dict[str, HallazgoView] = {}
        self._resumen_views: dict[str, ResumenView] = {}

        central = QWidget()
        central.setObjectName("Canvas")
        raiz = QHBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        self.sidebar = Sidebar()
        self.sidebar.ir_inicio.connect(self.abrir_inicio)
        self.sidebar.ir_hallazgo.connect(self.abrir_hallazgo)
        self.sidebar.ir_cargar.connect(self.abrir_cargar)
        self.sidebar.ir_resumen.connect(self.abrir_resumen)
        raiz.addWidget(self.sidebar)

        contenido = QWidget()
        contenido.setObjectName("Canvas")
        columna = QVBoxLayout(contenido)
        columna.setContentsMargins(0, 0, 0, 0)
        columna.setSpacing(0)

        self.stack = QStackedWidget()
        self.stack.setObjectName("Canvas")

        self.launcher = LauncherView()
        self.launcher.ir_cargar.connect(self.abrir_cargar)
        self.launcher.ir_generar.connect(self.abrir_hallazgo)
        self.stack.addWidget(self.launcher)

        columna.addWidget(self.stack, 1)
        raiz.addWidget(contenido, 1)

        self.setCentralWidget(central)
        self.abrir_inicio()

    # ── Rutas ─────────────────────────────────────────────────────────────

    def abrir_inicio(self) -> None:
        self.launcher.refrescar()
        self.stack.setCurrentWidget(self.launcher)
        self.sidebar.marcar(INICIO)

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
        self.sidebar.marcar(ruta_cargar(hallazgo_id))

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
        self.sidebar.marcar(ruta_hallazgo(hallazgo_id))

    def abrir_resumen(self, hallazgo_id: str) -> None:
        vista = self._resumen_views.get(hallazgo_id)
        if vista is None:
            vista = ResumenView(get_hallazgo(hallazgo_id))
            vista.ir_hallazgo.connect(self.abrir_hallazgo)
            self._resumen_views[hallazgo_id] = vista
            self.stack.addWidget(vista)

        self.stack.setCurrentWidget(vista)
        self.sidebar.marcar(ruta_resumen(hallazgo_id))

    def _al_cambiar_carga(self, hallazgo_id: str, cargadas: int, total: int) -> None:
        self.launcher.refrescar()
        for hid, vista in self._hallazgo_views.items():
            if hid != hallazgo_id:
                vista.refrescar()
