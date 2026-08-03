from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd

from app import config
from app.cache import fingerprint
from app.catalog.hallazgos import Hallazgo
from app.generation import sanitize

VERSION_CACHE = 1


class EstadoCache(str, Enum):
    AUSENTE = "ausente"
    VIGENTE = "vigente"
    DESACTUALIZADA = "desactualizada"


@dataclass
class Metadatos:
    hallazgo_id: str
    modelo: str | None
    huella: str
    filas: int
    generado_en: str
    version: int = VERSION_CACHE
    fuentes: list[str] = field(default_factory=list)

    @property
    def generado_texto(self) -> str:
        try:
            return datetime.fromisoformat(self.generado_en).strftime("%d/%m/%Y %H:%M")
        except ValueError:
            return self.generado_en


@dataclass
class ResultadoCache:
    estado: EstadoCache
    df: pd.DataFrame | None = None
    meta: Metadatos | None = None


def _carpeta(hallazgo: Hallazgo) -> Path:
    carpeta = config.cache_dir() / hallazgo.cert_id
    carpeta.mkdir(parents=True, exist_ok=True)
    return carpeta


def ruta_parquet(hallazgo: Hallazgo) -> Path:
    return _carpeta(hallazgo) / f"{hallazgo.id}.parquet"


def ruta_meta(hallazgo: Hallazgo) -> Path:
    return _carpeta(hallazgo) / f"{hallazgo.id}.meta.json"


def leer_meta(hallazgo: Hallazgo) -> Metadatos | None:
    path = ruta_meta(hallazgo)
    if not path.exists():
        return None
    try:
        datos = json.loads(path.read_text(encoding="utf-8"))
        return Metadatos(**datos)
    except Exception:
        return None

def _escribir_parquet(df: pd.DataFrame, destino: Path) -> None:
    """Escribe el parquet homogeneizando columnas de tipos mezclados."""
    def _volcar(datos: pd.DataFrame) -> None:
        datos.to_parquet(
            destino, engine="pyarrow",
            compression=config.COMPRESION, index=False,
        )

    try:
        _volcar(sanitize.normalizar(df))
    except Exception:
        _volcar(sanitize.forzar_texto(df))

def guardar(hallazgo: Hallazgo, df: pd.DataFrame) -> Metadatos:
    huella = fingerprint.calcular(hallazgo)

    _escribir_parquet(df, ruta_parquet(hallazgo))

    meta = Metadatos(
        hallazgo_id=hallazgo.id,
        modelo=hallazgo.modelo,
        huella=huella.valor,
        filas=len(df),
        generado_en=datetime.now().isoformat(timespec="seconds"),
        fuentes=[s.key for f in hallazgo.fuentes for s in f.slots],
    )
    ruta_meta(hallazgo).write_text(
        json.dumps(asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def estado(hallazgo: Hallazgo) -> EstadoCache:
    meta = leer_meta(hallazgo)
    if meta is None or not ruta_parquet(hallazgo).exists():
        return EstadoCache.AUSENTE
    if meta.version != VERSION_CACHE:
        return EstadoCache.DESACTUALIZADA
    actual = fingerprint.calcular(hallazgo)
    return EstadoCache.VIGENTE if actual.valor == meta.huella else EstadoCache.DESACTUALIZADA


def cargar(hallazgo: Hallazgo, columnas: list[str] | None = None) -> ResultadoCache:
    st = estado(hallazgo)
    if st is EstadoCache.AUSENTE:
        return ResultadoCache(estado=st)

    df = pd.read_parquet(ruta_parquet(hallazgo), engine="pyarrow", columns=columnas)
    return ResultadoCache(estado=st, df=df, meta=leer_meta(hallazgo))


def invalidar(hallazgo: Hallazgo) -> None:
    ruta_parquet(hallazgo).unlink(missing_ok=True)
    ruta_meta(hallazgo).unlink(missing_ok=True)
