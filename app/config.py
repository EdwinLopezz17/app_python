from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

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
        raise RuntimeError(
            "DATA_PATH no está definido. Crea un archivo .env en la raíz del "
            "proyecto con la línea:  DATA_PATH=C:\\ruta\\a\\la\\carpeta\\de\\datos"
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
