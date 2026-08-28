from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QMessageBox

from app import config
from app.ui import theme
from app.ui.shell import VentanaPrincipal


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Certificación")
    app.setOrganizationName("Automatización")

    icono = config.ruta_icono()
    if icono.is_file():
        app.setWindowIcon(QIcon(str(icono)))

    familia = theme.cargar_fuentes()
    app.setStyleSheet(theme.qss(familia))

    try:
        ruta = config.data_path()
        ruta.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        QMessageBox.critical(None, "Configuración incompleta", str(exc))
        return 1

    ventana = VentanaPrincipal()
    ventana.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
