from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from app import config


def _equivalente_parquet(ruta: str | os.PathLike) -> Path | None:
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
