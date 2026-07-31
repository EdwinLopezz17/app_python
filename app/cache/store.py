"""
CACHÉ DE HALLAZGOS GENERADOS
============================

Reemplazo de IndexedDB. Cada hallazgo generado se guarda como un Parquet con un
sidecar .json de metadatos:

    <CACHE_DIR>/<cert_id>/<hallazgo_id>.parquet
    <CACHE_DIR>/<cert_id>/<hallazgo_id>.meta.json

Por qué Parquet y no CSV ni SQLite:
  * conserva los tipos (bool sigue siendo bool, datetime sigue siendo datetime),
    que es justo donde se pierden los datos al pasar por CSV;
  * comprime ~10x, así que un hallazgo de 90.000 filas ocupa pocos MB;
  * permite leer solo las columnas que la tabla va a mostrar, sin tocar el resto.

El nombre del archivo está estandarizado: es siempre el `id` del hallazgo, en
minúsculas y con guiones. No se generan nombres con fecha ni con contador.

Al abrir un hallazgo, `cargar()` compara la huella actual de las fuentes contra
la guardada y devuelve un estado explícito: VIGENTE, DESACTUALIZADA o AUSENTE.
La UI decide qué hacer con eso; este módulo no toma esa decisión.
"""

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


def guardar(hallazgo: Hallazgo, df: pd.DataFrame) -> Metadatos:
    """Persiste un hallazgo recién generado junto con la huella de sus fuentes."""
    huella = fingerprint.calcular(hallazgo)

    df.to_parquet(
        ruta_parquet(hallazgo), engine="pyarrow",
        compression=config.COMPRESION, index=False,
    )

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
    """Estado de la caché sin cargar los datos. Barato: solo lee el .json."""
    meta = leer_meta(hallazgo)
    if meta is None or not ruta_parquet(hallazgo).exists():
        return EstadoCache.AUSENTE
    if meta.version != VERSION_CACHE:
        return EstadoCache.DESACTUALIZADA
    actual = fingerprint.calcular(hallazgo)
    return EstadoCache.VIGENTE if actual.valor == meta.huella else EstadoCache.DESACTUALIZADA


def cargar(hallazgo: Hallazgo, columnas: list[str] | None = None) -> ResultadoCache:
    """
    Devuelve el hallazgo cacheado y su estado.

    Si está DESACTUALIZADA igual se devuelven los datos: es preferible mostrar el
    resultado anterior con un aviso visible a dejar la pantalla en blanco
    mientras el auditor decide si regenera.
    """
    st = estado(hallazgo)
    if st is EstadoCache.AUSENTE:
        return ResultadoCache(estado=st)

    df = pd.read_parquet(ruta_parquet(hallazgo), engine="pyarrow", columns=columnas)
    return ResultadoCache(estado=st, df=df, meta=leer_meta(hallazgo))


def invalidar(hallazgo: Hallazgo) -> None:
    ruta_parquet(hallazgo).unlink(missing_ok=True)
    ruta_meta(hallazgo).unlink(missing_ok=True)
