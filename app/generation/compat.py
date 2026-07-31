"""
PUENTE DE COMPATIBILIDAD  (temporal)
====================================

Los servicios de `logic/` todavía leen `.csv`:

    self.path_file = os.path.join(self.folder_path, f"{self.file_enum.value}.csv")
    df = pd.read_csv(self.path_file, sep=';', encoding='utf-8')

y la aplicación ya escribe `.parquet`. Este módulo cierra esa brecha SIN tocar
`logic/`, para que la generación de hallazgos funcione desde hoy mientras el
backend hace la migración a su ritmo.

Cómo funciona: durante la generación (y solo durante ella) se interceptan
`os.path.exists`, `os.path.isfile` y `pandas.read_csv`. Cuando `logic/` pregunta
por un `.csv` que no existe pero SÍ existe el `.parquet` equivalente, se le
responde con el Parquet. Cualquier otra ruta se comporta igual que siempre.

El parche es temporal y de alcance acotado: se activa con un `with` y se
revierte al salir, incluso si hay excepción.

CÓMO ELIMINAR ESTE ARCHIVO
--------------------------
Cuando el backend termine de migrar sus servicios a
`pd.read_parquet(...)` con extensión `.parquet`:

  1. En `app/generation/reports.py`, quitar el `with puente_parquet():` de
     `generar()`.
  2. Borrar este archivo.

Nada más depende de él.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from app import config


def _equivalente_parquet(ruta: str | os.PathLike) -> Path | None:
    """Devuelve el .parquet correspondiente a un .csv, si existe."""
    try:
        p = Path(ruta)
    except TypeError:
        return None
    if p.suffix.lower() != ".csv":
        return None
    candidato = p.with_suffix(config.EXTENSION_DATOS)
    return candidato if candidato.exists() else None


@contextmanager
def puente_parquet():
    """
    Activa la compatibilidad .csv -> .parquet mientras dure el bloque.

    Se usa alrededor de las llamadas a los reportes de `logic/`.
    """
    exists_original = os.path.exists
    isfile_original = os.path.isfile
    read_csv_original = pd.read_csv

    def exists_parcheado(ruta):
        if exists_original(ruta):
            return True
        return _equivalente_parquet(ruta) is not None

    def isfile_parcheado(ruta):
        if isfile_original(ruta):
            return True
        return _equivalente_parquet(ruta) is not None

    def read_csv_parcheado(ruta, *args, **kwargs):
        equivalente = _equivalente_parquet(ruta) if not exists_original(ruta) else None
        if equivalente is None:
            return read_csv_original(ruta, *args, **kwargs)

        # Se devuelve el Parquet con el mismo contrato que tenía el CSV:
        # todo string, sin NaN. Es exactamente lo que `logic/` espera recibir.
        df = pd.read_parquet(equivalente, engine="pyarrow")
        return df.fillna("").astype(str)

    os.path.exists = exists_parcheado
    os.path.isfile = isfile_parcheado
    pd.read_csv = read_csv_parcheado
    try:
        yield
    finally:
        os.path.exists = exists_original
        os.path.isfile = isfile_original
        pd.read_csv = read_csv_original


def logic_ya_migrado() -> bool:
    """
    True si los servicios de `logic/` ya leen Parquet directamente.

    Se usa solo para informar en `app/doctor.py`; el puente es inofensivo aunque
    la migración ya esté hecha (simplemente nunca se activa).
    """
    try:
        from logic.share.services.dni_vs_user_service import DNIUserService
    except Exception:
        return False

    import inspect

    try:
        fuente = inspect.getsource(DNIUserService)
    except (OSError, TypeError):
        return False
    return "read_parquet" in fuente
