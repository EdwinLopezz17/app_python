from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from app import config

_MAGIC_PARQUET = b"PAR1"

_ENCODINGS_FALLBACK = ("utf-8-sig", "cp1252", "latin-1")


def _es_parquet(path: Path) -> bool:
    try:
        with open(path, "rb") as fh:
            return fh.read(4) == _MAGIC_PARQUET
    except OSError:
        return False


def _leer_csv(path: Path, columns=None, **kwargs) -> pd.DataFrame:
    base = dict(
        sep=config.CSV_SEP,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        low_memory=False,
    )
    if columns:
        base["usecols"] = list(columns)

    errores: list[Exception] = []
    for encoding in (config.CSV_ENCODING, *_ENCODINGS_FALLBACK):
        try:
            df = pd.read_csv(path, encoding=encoding, **base)
            return df.fillna("")
        except UnicodeDecodeError as exc:
            errores.append(exc)
            continue
    raise errores[-1]


@contextmanager
def puente_csv():
    read_parquet_original = pd.read_parquet

    def read_parquet_parcheado(ruta, *args, **kwargs):
        try:
            path = Path(ruta)
        except TypeError:
            return read_parquet_original(ruta, *args, **kwargs)

        if path.exists() and not _es_parquet(path):
            return _leer_csv(path, columns=kwargs.get("columns"))

        if not path.exists():
            gemelo = path.with_suffix(config.EXTENSION_DATOS)
            if gemelo.exists():
                return _leer_csv(gemelo, columns=kwargs.get("columns"))

        return read_parquet_original(ruta, *args, **kwargs)

    pd.read_parquet = read_parquet_parcheado
    try:
        yield
    finally:
        pd.read_parquet = read_parquet_original


def logic_lee_csv() -> bool:
    import inspect

    modulos = [
        ("logic.share.services.ad_service", "ADService"),
        ("logic.share.services.gdh_service", "GDHUserService"),
        ("logic.share.services.dni_vs_user_service", "DNIUserService"),
        ("logic.share.services.entraid_service", "EntraUserService"),
        ("logic.share.services.tickets_report", "TicketInfoService"),
        ("logic.share.services.mr_service", "MatrizRolesService"),
    ]

    for modulo, clase in modulos:
        try:
            mod = __import__(modulo, fromlist=[clase])
            fuente = inspect.getsource(getattr(mod, clase))
        except Exception:
            return False
        if "read_parquet" in fuente:
            return False
    return True


def servicios_con_parquet() -> list[str]:
    import inspect

    pendientes: list[str] = []
    modulos = [
        ("logic.share.services.ad_service", "ADService"),
        ("logic.share.services.gdh_service", "GDHUserService"),
        ("logic.share.services.dni_vs_user_service", "DNIUserService"),
        ("logic.share.services.entraid_service", "EntraUserService"),
        ("logic.share.services.tickets_report", "TicketInfoService"),
        ("logic.share.services.mr_service", "MatrizRolesService"),
    ]
    for modulo, clase in modulos:
        try:
            mod = __import__(modulo, fromlist=[clase])
            if "read_parquet" in inspect.getsource(getattr(mod, clase)):
                pendientes.append(clase)
        except Exception:
            continue
    return pendientes
