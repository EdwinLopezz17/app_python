from __future__ import annotations

from PySide6.QtCore import QElapsedTimer, QSize, Qt, QTimer
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (
    QApplication, QFrame, QLabel, QProgressBar, QVBoxLayout, QWidget,
)

from app import config
from app.ui import theme

LADO_LOGO = 96
ANCHO = 420
MINIMO_MS = 700


def _logo(lado: int = LADO_LOGO) -> QPixmap:
    svg = config.recurso("app", "ui", "assets", "logo.svg")
    if svg.is_file():
        try:
            from PySide6.QtSvg import QSvgRenderer

            renderer = QSvgRenderer(str(svg))
            if renderer.isValid():
                mapa = QPixmap(QSize(lado, lado))
                mapa.fill(Qt.transparent)
                pintor = QPainter(mapa)
                pintor.setRenderHint(QPainter.Antialiasing, True)
                renderer.render(pintor)
                pintor.end()
                return mapa
        except Exception:
            pass

    ico = config.ruta_icono()
    if ico.is_file():
        return QIcon(str(ico)).pixmap(lado, lado)

    return QPixmap()


class PantallaCarga(QWidget):

    def __init__(self) -> None:
        super().__init__(
            None,
            Qt.SplashScreen | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint,
        )
        self.setObjectName("Splash")
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self._reloj = QElapsedTimer()
        self._reloj.start()

        raiz = QVBoxLayout(self)
        raiz.setContentsMargins(0, 0, 0, 0)

        tarjeta = QFrame()
        tarjeta.setObjectName("SplashCard")
        raiz.addWidget(tarjeta)

        cuerpo = QVBoxLayout(tarjeta)
        cuerpo.setContentsMargins(32, 32, 32, 26)
        cuerpo.setSpacing(14)

        marca = QLabel()
        marca.setAlignment(Qt.AlignCenter)
        mapa = _logo()
        if not mapa.isNull():
            marca.setPixmap(mapa)
        cuerpo.addWidget(marca)

        titulo = QLabel("Certificación de Accesos")
        titulo.setObjectName("SplashTitulo")
        titulo.setAlignment(Qt.AlignCenter)
        cuerpo.addWidget(titulo)

        self.estado = QLabel("Iniciando la aplicación…")
        self.estado.setObjectName("SplashEstado")
        self.estado.setAlignment(Qt.AlignCenter)
        cuerpo.addWidget(self.estado)

        barra = QProgressBar()
        barra.setObjectName("SplashBarra")
        barra.setRange(0, 0)
        barra.setTextVisible(False)
        barra.setFixedHeight(4)
        cuerpo.addWidget(barra)

        self.setFixedWidth(ANCHO)
        self.setStyleSheet(_qss())
        self.adjustSize()
        self._centrar()

    def _centrar(self) -> None:
        pantalla = QApplication.primaryScreen()
        if pantalla is None:
            return
        area = pantalla.availableGeometry()
        geo = self.frameGeometry()
        geo.moveCenter(area.center())
        self.move(geo.topLeft())

    def mensaje(self, texto: str) -> None:
        self.estado.setText(texto)
        QApplication.processEvents()

    def cerrar_con(self, ventana: QWidget, minimo_ms: int = MINIMO_MS) -> None:
        restante = max(0, minimo_ms - int(self._reloj.elapsed()))

        def _terminar() -> None:
            ventana.show()
            ventana.raise_()
            ventana.activateWindow()
            self.close()

        QTimer.singleShot(restante, _terminar)


def _qss() -> str:
    return f"""
QFrame#SplashCard {{
    background: {theme.SURFACE_CONTAINER_LOWEST};
    border: 1px solid {theme.OUTLINE_VARIANT};
    border-radius: {theme.RADIO_LG}px;
}}
QLabel#SplashTitulo {{
    color: {theme.ON_SURFACE};
    font-size: 18px;
    font-weight: 600;
}}
QLabel#SplashEstado {{
    color: {theme.ON_SURFACE_VARIANT};
    font-size: 12px;
}}
QProgressBar#SplashBarra {{
    background: {theme.SURFACE_CONTAINER};
    border: none;
    border-radius: 2px;
}}
QProgressBar#SplashBarra::chunk {{
    background: {theme.PRIMARY};
    border-radius: 2px;
}}
"""
