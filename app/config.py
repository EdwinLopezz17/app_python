from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv
from platformdirs import user_cache_dir

load_dotenv()

APP_NAME = "CertificacionPPS"
APP_AUTHOR = "Pacifico"

#: Formato de persistencia de los datos cargados manualmente.
#: Se migró de Parquet a CSV para que `logic/` lea exactamente el mismo archivo
#: que escribe `app/` (los servicios usan `DATA_PATH / FileName.value`, y esos
#: valores terminan en `.csv`).
EXTENSION_DATOS = ".csv"

#: Contrato de lectura de `logic/`: `pd.read_csv(path, sep=";", encoding="utf-8")`.
#: El separador y la codificación NO son configurables por eso mismo.
CSV_SEP = ";"
CSV_ENCODING = "utf-8"          # sin BOM: un BOM rompería la 1ra cabecera en logic/
CSV_QUOTECHAR = '"'
CSV_TERMINADOR = "\n"

#: Extensiones que pudieron quedar de la etapa Parquet y que se limpian al borrar.
EXTENSIONES_LEGADAS = (".parquet",)


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
    """Quita la extensión de datos (y las legadas) del nombre lógico del slot.

    `slot.key` viene de `FileName` y ya trae `.csv`; sin esta limpieza el
    destino terminaría siendo `usuarios_crm.csv.csv`.
    """
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
