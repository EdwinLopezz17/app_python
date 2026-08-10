from __future__ import annotations

import csv
import json
import os
import tempfile
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path

import pandas as pd

from app import config
from app.cache import fingerprint
from app.catalog.hallazgos import Hallazgo
from app.generation import sanitize

VERSION_CACHE = 2


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
    dtypes: dict[str, str] = field(default_factory=dict)

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


def ruta_datos(hallazgo: Hallazgo) -> Path:
    return _carpeta(hallazgo) / f"{hallazgo.id}{config.EXTENSION_DATOS}"


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

def _volcar_csv(datos: pd.DataFrame, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        suffix=".csv.tmp", prefix=destino.stem + "-", dir=destino.parent
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        datos.to_csv(
            tmp,
            sep=config.CSV_SEP,
            index=False,
            encoding=config.CSV_ENCODING,
            lineterminator=config.CSV_TERMINADOR,
            quotechar=config.CSV_QUOTECHAR,
            quoting=csv.QUOTE_MINIMAL,
            na_rep="",
            date_format="%Y-%m-%d %H:%M:%S",
        )
        os.replace(tmp, destino)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def _escribir_csv(df: pd.DataFrame, destino: Path) -> pd.DataFrame:
    try:
        datos = sanitize.normalizar(df)
        _volcar_csv(datos, destino)
    except Exception:
        datos = sanitize.forzar_texto(df)
        _volcar_csv(datos, destino)
    return datos


def _mapa_dtypes(df: pd.DataFrame) -> dict[str, str]:
    if df is None or df.empty:
        return {}
    return {str(c): str(df[c].dtype) for c in df.columns}


def _restaurar_dtypes(df: pd.DataFrame, dtypes: dict[str, str]) -> pd.DataFrame:
    if df is None or df.empty or not dtypes:
        return df

    for col in df.columns:
        tipo = str(dtypes.get(str(col), ""))
        if not tipo:
            continue
        try:
            if tipo == "bool":
                df[col] = df[col].map(
                    {"True": True, "False": False, "true": True, "false": False}
                ).fillna(False).astype(bool)
            elif tipo.startswith("datetime64"):
                df[col] = pd.to_datetime(df[col], errors="coerce")
            elif tipo.startswith(("int", "uint", "float")):
                df[col] = pd.to_numeric(df[col], errors="coerce")
        except Exception:
            continue
    return df


def guardar(hallazgo: Hallazgo, df: pd.DataFrame) -> Metadatos:
    huella = fingerprint.calcular(hallazgo)

    escrito = _escribir_csv(df, ruta_datos(hallazgo))

    meta = Metadatos(
        hallazgo_id=hallazgo.id,
        modelo=hallazgo.modelo,
        huella=huella.valor,
        filas=len(df),
        generado_en=datetime.now().isoformat(timespec="seconds"),
        fuentes=[s.key for f in hallazgo.fuentes for s in f.slots],
        dtypes=_mapa_dtypes(escrito),
    )
    ruta_meta(hallazgo).write_text(
        json.dumps(asdict(meta), ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return meta


def estado(hallazgo: Hallazgo) -> EstadoCache:
    meta = leer_meta(hallazgo)
    if meta is None or not ruta_datos(hallazgo).exists():
        return EstadoCache.AUSENTE
    if meta.version != VERSION_CACHE:
        return EstadoCache.DESACTUALIZADA
    actual = fingerprint.calcular(hallazgo)
    return EstadoCache.VIGENTE if actual.valor == meta.huella else EstadoCache.DESACTUALIZADA


def cargar(hallazgo: Hallazgo, columnas: list[str] | None = None) -> ResultadoCache:
    st = estado(hallazgo)
    if st is EstadoCache.AUSENTE:
        return ResultadoCache(estado=st)

    meta = leer_meta(hallazgo)
    df = pd.read_csv(
        ruta_datos(hallazgo),
        sep=config.CSV_SEP,
        encoding=config.CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        usecols=columnas,
        low_memory=False,
    )
    df = _restaurar_dtypes(df, meta.dtypes if meta else {})
    return ResultadoCache(estado=st, df=df, meta=meta)


def invalidar(hallazgo: Hallazgo) -> None:
    ruta_datos(hallazgo).unlink(missing_ok=True)
    ruta_meta(hallazgo).unlink(missing_ok=True)
    for ext in config.EXTENSIONES_LEGADAS:
        (_carpeta(hallazgo) / f"{hallazgo.id}{ext}").unlink(missing_ok=True)
