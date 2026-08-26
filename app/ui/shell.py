from __future__ import annotations

from PySide6.QtCore import QTimer
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from app.catalog.hallazgos import HALLAZGOS_BY_ID, get as get_hallazgo
from app.ui.cargar_view import CargarView
from app.ui.hallazgo_view import HallazgoView
from app.ui.launcher_view import LauncherView
from app.ui.resumen_view import ResumenView
from app.ui import preferencias
from app.ui.update_badge import BadgeActualizacion
from app.ui.paleta import PaletaComandos
from app.ui.topbar import (
    INICIO, PieDatos, TopBar, ruta_cargar, ruta_hallazgo, ruta_resumen,
)


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Certificación")
        self.resize(1440, 900)
        self.setMinimumSize(900, 600)

        guardada = preferencias.leer_geometria()
        if guardada is not None:
            self.restoreGeometry(guardada)

        self._cargar_views: dict[str, CargarView] = {}
        self._hallazgo_views: dict[str, HallazgoView] = {}
        self._resumen_views: dict[str, ResumenView] = {}

        central = QWidget()
        central.setObjectName("Canvas")
        raiz = QVBoxLayout(central)
        raiz.setContentsMargins(0, 0, 0, 0)
        raiz.setSpacing(0)

        self.topbar = TopBar()
        self.topbar.ir_inicio.connect(self.abrir_inicio)
        self.topbar.ir_hallazgo.connect(self.abrir_hallazgo)
        self.topbar.ir_cargar.connect(self.abrir_cargar)
        self.topbar.ir_resumen.connect(self.abrir_resumen)
        self.topbar.abrir_busqueda.connect(self.abrir_paleta)
        raiz.addWidget(self.topbar)

        self.badge_update = BadgeActualizacion(self.topbar)
        self.topbar.montar_badge(self.badge_update)

        self.stack = QStackedWidget()
        self.stack.setObjectName("Canvas")

        self.launcher = LauncherView()
        self.launcher.ir_cargar.connect(self.abrir_cargar)
        self.launcher.ir_generar.connect(self.abrir_hallazgo)
        self.stack.addWidget(self.launcher)

        raiz.addWidget(self.stack, 1)
        raiz.addWidget(PieDatos())

        self.setCentralWidget(central)

        self.paleta = PaletaComandos(self)
        self.paleta.navegar.connect(self._ir_a)
        atajo = QShortcut(QKeySequence("Ctrl+K"), self)
        atajo.activated.connect(self.abrir_paleta)

        self._restaurar_vista()

        QTimer.singleShot(3000, self.badge_update.buscar)

    def abrir_paleta(self) -> None:
        self.paleta.abrir()

    def _ir_a(self, entrada) -> None:
        if entrada.vista == "cargar":
            self.abrir_cargar(entrada.hallazgo_id, foco=entrada.fuente_id)
        elif entrada.vista == "hallazgo":
            self.abrir_hallazgo(entrada.hallazgo_id)
        elif entrada.vista == "resumen":
            self.abrir_resumen(entrada.hallazgo_id)


    def _restaurar_vista(self) -> None:
        ruta = preferencias.leer_ultima_vista()
        vista, _, hallazgo_id = ruta.partition(":")

        if hallazgo_id and hallazgo_id in HALLAZGOS_BY_ID:
            accion = {
                "cargar": self.abrir_cargar,
                "hallazgo": self.abrir_hallazgo,
                "resumen": self.abrir_resumen,
            }.get(vista)
            if accion is not None:
                accion(hallazgo_id)
                return

        self.abrir_inicio()

    def closeEvent(self, evento) -> None:
        preferencias.guardar_geometria(self.saveGeometry())
        super().closeEvent(evento)

    def abrir_inicio(self) -> None:
        self.launcher.refrescar()
        self.stack.setCurrentWidget(self.launcher)
        self.topbar.marcar(INICIO)
        preferencias.guardar_ultima_vista(INICIO)

    def abrir_cargar(self, hallazgo_id: str, foco: str | None = None) -> None:
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
        self.topbar.marcar(ruta_cargar(hallazgo_id))
        preferencias.guardar_ultima_vista(ruta_cargar(hallazgo_id))

        if foco:
            vista.enfocar_fuente(foco)

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
        self.topbar.marcar(ruta_hallazgo(hallazgo_id))
        preferencias.guardar_ultima_vista(ruta_hallazgo(hallazgo_id))

    def abrir_resumen(self, hallazgo_id: str) -> None:
        vista = self._resumen_views.get(hallazgo_id)
        if vista is None:
            vista = ResumenView(get_hallazgo(hallazgo_id))
            vista.ir_hallazgo.connect(self.abrir_hallazgo)
            self._resumen_views[hallazgo_id] = vista
            self.stack.addWidget(vista)

        self.stack.setCurrentWidget(vista)
        self.topbar.marcar(ruta_resumen(hallazgo_id))
        preferencias.guardar_ultima_vista(ruta_resumen(hallazgo_id))

    def _al_cambiar_carga(self, hallazgo_id: str, cargadas: int, total: int) -> None:
        self.launcher.refrescar()
        for hid, vista in self._hallazgo_views.items():
            if hid != hallazgo_id:
                vista.refrescar()
