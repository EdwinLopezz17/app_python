from __future__ import annotations

import importlib
import inspect
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from app.generation.compat import puente_csv

PAQUETES = ("logic",)

SUFIJOS = ("Service", "Services")


def _modulos_de_servicio() -> list[str]:
    nombres: list[str] = []
    for nombre_paquete in PAQUETES:
        try:
            paquete = importlib.import_module(nombre_paquete)
        except Exception:
            continue
        for raiz in paquete.__path__:
            base = Path(raiz)
            for archivo in sorted(base.rglob("*.py")):
                if archivo.name == "__init__.py":
                    continue
                relativo = archivo.relative_to(base).with_suffix("")
                partes = relativo.parts
                if "services" not in partes and not archivo.stem.endswith(
                    ("_service", "_services")
                ):
                    continue
                nombres.append(".".join((nombre_paquete, *partes)))
    return nombres


def _clases_de_servicio() -> list[type]:
    encontradas: dict[str, type] = {}
    for nombre_modulo in _modulos_de_servicio():
        try:
            modulo = importlib.import_module(nombre_modulo)
        except Exception:
            continue
        for nombre, obj in vars(modulo).items():
            if not inspect.isclass(obj):
                continue
            if obj.__module__ != modulo.__name__:
                continue
            if not nombre.endswith(SUFIJOS):
                continue
            encontradas.setdefault(f"{obj.__module__}.{nombre}", obj)
    return list(encontradas.values())


def _clave(args, kwargs) -> tuple:
    try:
        return (args, tuple(sorted(kwargs.items())))
    except TypeError:
        return None


@contextmanager
def _servicios_memoizados():
    instancias: dict[tuple, dict] = {}
    originales: list[tuple[type, object]] = []

    for cls in _clases_de_servicio():
        init_original = cls.__init__
        originales.append((cls, init_original))

        def envolver(cls=cls, init_original=init_original):
            def __init__(self, *args, **kwargs):
                clave = _clave(args, kwargs)
                if clave is None:
                    init_original(self, *args, **kwargs)
                    return
                guardado = instancias.get((cls, clave))
                if guardado is not None:
                    self.__dict__.update(guardado)
                    return
                init_original(self, *args, **kwargs)
                instancias[(cls, clave)] = dict(self.__dict__)
            return __init__

        cls.__init__ = envolver()

    try:
        yield instancias
    finally:
        for cls, init_original in originales:
            cls.__init__ = init_original


@contextmanager
def _lecturas_cacheadas():
    cache: dict[tuple, pd.DataFrame] = {}
    read_csv_original = pd.read_csv

    def firma(ruta, kwargs):
        try:
            path = Path(ruta)
            stat = path.stat()
        except (TypeError, OSError, ValueError):
            return None
        if kwargs.get("chunksize") or kwargs.get("iterator") or kwargs.get("nrows"):
            return None
        usecols = kwargs.get("usecols")
        if usecols is not None:
            try:
                usecols = tuple(usecols)
            except TypeError:
                return None
        return (
            str(path), stat.st_size, int(stat.st_mtime),
            kwargs.get("sep"), kwargs.get("encoding"), kwargs.get("dtype") is str,
            usecols,
        )

    def read_csv_cacheado(ruta, *args, **kwargs):
        if args:
            return read_csv_original(ruta, *args, **kwargs)
        clave = firma(ruta, kwargs)
        if clave is None:
            return read_csv_original(ruta, **kwargs)
        guardado = cache.get(clave)
        if guardado is None:
            guardado = read_csv_original(ruta, **kwargs)
            cache[clave] = guardado
        return guardado.copy()

    pd.read_csv = read_csv_cacheado
    try:
        yield cache
    finally:
        pd.read_csv = read_csv_original


@contextmanager
def sesion_generacion():
    with puente_csv():
        with _lecturas_cacheadas():
            with _servicios_memoizados():
                yield
