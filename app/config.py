from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv


def _congelado() -> bool:
    """True cuando la app corre desde el .exe de PyInstaller."""
    return getattr(sys, "frozen", False)


def raiz_datos() -> Path:
    """Carpeta donde vive el .exe (o la raíz del proyecto en desarrollo).

    Aquí se busca el .env. Con --onefile NO sirve el cwd: si el usuario abre
    el .exe desde otra carpeta o desde un acceso directo, load_dotenv() no
    encontraría el archivo.
    """
    if _congelado():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def raiz_recursos() -> Path:
    """Carpeta de los recursos empaquetados (iconos, fuentes).

    Con --onefile PyInstaller los extrae a un temporal (sys._MEIPASS); en
    desarrollo es la raíz del proyecto.
    """
    interno = getattr(sys, "_MEIPASS", None)
    if interno:
        return Path(interno)
    return Path(__file__).resolve().parent.parent


def recurso(*partes: str) -> Path:
    """Ruta a un recurso empaquetado, p. ej. recurso("app", "ui", "assets", "logo.ico")."""
    return raiz_recursos().joinpath(*partes)


def ruta_icono() -> Path:
    return recurso("app", "ui", "assets", "logo.ico")


def carpeta_fuentes() -> Path:
    return recurso("app", "ui", "fonts")


load_dotenv(raiz_datos() / ".env")

APP_NAME = "CertificacionPPS"
APP_AUTHOR = "Pacifico"

EXTENSION_DATOS = ".csv"

CSV_SEP = ";"
CSV_ENCODING = "utf-8"
CSV_QUOTECHAR = '"'
CSV_TERMINADOR = "\n"

# Extensiones de versiones anteriores de la app. Solo se usan para limpiar
# residuos al eliminar un archivo cargado (ver storage/files._residuos_de).
EXTENSIONES_LEGADAS = (".parquet",)


def data_path() -> Path:
    raw = os.getenv("DATA_PATH")
    if not raw:
        donde = "junto al ejecutable" if _congelado() else "en la raíz del proyecto"
        raise RuntimeError(
            "DATA_PATH no está definido.\n\n"
            f"Crea un archivo llamado .env {donde}, es decir en:\n"
            f"{raiz_datos()}\n\n"
            "con esta única línea dentro:\n"
            "DATA_PATH=C:\\ruta\\a\\la\\carpeta\\de\\datos"
        )
    return Path(raw)


def nombre_base(file_name: str) -> str:
    nombre = str(file_name)
    conocidas = (EXTENSION_DATOS, *EXTENSIONES_LEGADAS)
    cambio = True
    while cambio:
        cambio = False
        for ext in conocidas:
            if nombre.lower().endswith(ext):
                nombre = nombre[: -len(ext)]
                cambio = True
    return nombre


def destino(file_name: str, subfolder: str | None = None) -> Path:
    carpeta = data_path() / subfolder if subfolder else data_path()
    return carpeta / f"{nombre_base(file_name)}{EXTENSION_DATOS}"
