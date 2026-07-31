"""
Punto de entrada de la aplicación de escritorio.

Ejecutar desde la RAÍZ del proyecto (la carpeta que contiene `app/`, `logic/` y
`models/`):

    python -m app.main

También funciona `python app/main.py`: el bloque de sys.path de abajo agrega la
raíz del proyecto para que `models.*` y `logic.*` sean importables en ambos
casos.

Requisitos previos:
  * un archivo `.env` en la raíz con la línea  DATA_PATH=C:\\ruta\\a\\los\\datos
  * las dependencias de `requirements.txt` instaladas
"""

from __future__ import annotations

import sys
from pathlib import Path

# La raíz del proyecto es el padre de `app/`. Se agrega antes de cualquier
# import propio para que `models.file_names` resuelva sin importar cómo se
# lance el programa.
RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from PySide6.QtCore import Qt  # noqa: E402
from PySide6.QtWidgets import QApplication, QMessageBox  # noqa: E402

from app import config  # noqa: E402
from app.ui import theme  # noqa: E402
from app.ui.shell import VentanaPrincipal  # noqa: E402


def main() -> int:
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName("Certificación de Accesos")
    app.setOrganizationName("Pacífico Seguros")

    familia = theme.cargar_fuentes()
    app.setStyleSheet(theme.qss(familia))

    # Falla temprano y con un mensaje claro si falta la configuración, en vez de
    # abrir la ventana y reventar al primer clic.
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
