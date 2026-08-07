from __future__ import annotations

from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from app.catalog.hallazgos import HALLAZGOS_BY_ID, get as get_hallazgo
from app.ui.cargar_view import CargarView
from app.ui.hallazgo_view import HallazgoView
from app.ui.launcher_view import LauncherView
from app.ui.resumen_view import ResumenView
from app.ui import preferencias
from app.ui.topbar import (
    INICIO, PieDatos, TopBar, ruta_cargar, ruta_hallazgo, ruta_resumen,
)


class VentanaPrincipal(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Certificación de Accesos · Pacífico Seguros")
        self.resize(1440, 900)
        # La app se usa mucho a media pantalla en monitores Full HD (~960 px).
        # Con el piso anterior (1180) nunca se llegaba a los anchos angostos.
        self.setMinimumSize(900, 600)

        # La geometría guardada manda sobre el `resize` por defecto. Si la
        # pantalla cambió (portátil que se desacopla del monitor) Qt la
        # descarta sola y se queda con el tamaño de arriba.
        guardada = preferencias.leer_geometria()
        if guardada is not None:
            self.restoreGeometry(guardada)

        self._cargar_views: dict[str, CargarView] = {}
        self._hallazgo_views: dict[str, HallazgoView] = {}
        self._resumen_views: dict[str, ResumenView] = {}

        # Tres franjas apiladas, como el AppShell de la referencia: barra de
        # navegación, contenido (cada vista trae su propia cabecera de migas y
        # título) y un pie discreto con la ruta de datos.
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
        raiz.addWidget(self.topbar)

        self.stack = QStackedWidget()
        self.stack.setObjectName("Canvas")

        self.launcher = LauncherView()
        self.launcher.ir_cargar.connect(self.abrir_cargar)
        self.launcher.ir_generar.connect(self.abrir_hallazgo)
        self.stack.addWidget(self.launcher)

        raiz.addWidget(self.stack, 1)
        raiz.addWidget(PieDatos())

        self.setCentralWidget(central)
        self._restaurar_vista()



    def _restaurar_vista(self) -> None:
        """Reabre la vista en la que se cerró la app la última vez.

        La ruta se guarda como "cargar:<id>" / "hallazgo:<id>" / "resumen:<id>".
        Si el hallazgo ya no existe en el catálogo (renombrado, retirado) se
        cae a la pantalla de inicio en silencio.
        """
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
        self.topbar.marcar(ruta_cargar(hallazgo_id))
        preferencias.guardar_ultima_vista(ruta_cargar(hallazgo_id))

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
