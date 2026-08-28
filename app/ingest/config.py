from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

def _congelado() -> bool:
    return getattr(sys, "frozen", False)


def raiz_datos() -> Path:
    if _congelado():
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


def raiz_recursos() -> Path:
    interno = getattr(sys, "_MEIPASS", None)
    if interno:
        return Path(interno)
    return Path(__file__).resolve().parent.parent


def recurso(*partes: str) -> Path:
    return raiz_recursos().joinpath(*partes)


def ruta_icono() -> Path:
    return recurso("app", "ui", "assets", "logo.ico")


def carpeta_fuentes() -> Path:
    return recurso("app", "ui", "fonts")


load_dotenv(raiz_datos() / ".env")

APP_NAME = "Certificacion"
APP_AUTHOR = "Automatizadores"

EXTENSION_DATOS = ".csv"

CSV_SEP = ";"
CSV_ENCODING = "utf-8"
CSV_QUOTECHAR = '"'
CSV_TERMINADOR = "\n"

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
