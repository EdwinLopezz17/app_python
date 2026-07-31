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
    raw = os.getenv("DATA_PATH")
    if not raw:
        raise RuntimeError(
            "DATA_PATH no está definido. Crea un archivo .env en la raíz del "
            "proyecto con la línea:  DATA_PATH=C:\\ruta\\a\\la\\carpeta\\de\\datos"
        )
    return Path(raw)


def cache_dir() -> Path:
    raw = os.getenv("CACHE_PATH")
    base = Path(raw) if raw else Path(user_cache_dir(APP_NAME, APP_AUTHOR))
    base.mkdir(parents=True, exist_ok=True)
    return base


def nombre_base(file_name: str) -> str:
    nombre = str(file_name)
    while nombre.lower().endswith(EXTENSION_DATOS):
        nombre = nombre[: -len(EXTENSION_DATOS)]
    return nombre


def destino(file_name: str, subfolder: str | None = None) -> Path:
    carpeta = data_path() / subfolder if subfolder else data_path()
    return carpeta / f"{nombre_base(file_name)}{EXTENSION_DATOS}"
