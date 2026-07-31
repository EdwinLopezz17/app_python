"""
Configuración de rutas de la aplicación.

DATA_PATH  : carpeta donde se escriben los archivos cargados (.parquet). Es la
             MISMA que leen los servicios de `logic/`, y se toma del .env que ya
             usa el monolito. No se inventa ni se duplica.

CACHE_DIR  : carpeta donde se guardan los hallazgos ya generados. Va en
             %LOCALAPPDATA%, NUNCA dentro de OneDrive ni de DATA_PATH: son datos
             derivados, regenerables, y no deben sincronizarse ni mezclarse con
             los archivos de origen.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_cache_dir

load_dotenv()

APP_NAME = "CertificacionPPS"
APP_AUTHOR = "Pacifico"

EXTENSION_DATOS = ".parquet"
COMPRESION = "zstd"


def data_path() -> Path:
    """Carpeta de archivos cargados. Coincide con la que consume `logic/`."""
    raw = os.getenv("DATA_PATH")
    if not raw:
        raise RuntimeError(
            "DATA_PATH no está definido. Crea un archivo .env en la raíz del "
            "proyecto con la línea:  DATA_PATH=C:\\ruta\\a\\la\\carpeta\\de\\datos"
        )
    return Path(raw)


def cache_dir() -> Path:
    """Carpeta de hallazgos generados (caché Parquet)."""
    raw = os.getenv("CACHE_PATH")
    base = Path(raw) if raw else Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    base.mkdir(parents=True, exist_ok=True)
    return base


def destino(file_name: str, subfolder: str | None = None) -> Path:
    """Ruta absoluta del archivo de datos de una fuente."""
    carpeta = data_path() / subfolder if subfolder else data_path()
    return carpeta / f"{file_name}{EXTENSION_DATOS}"
