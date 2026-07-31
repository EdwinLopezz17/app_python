"""
Consolidación de uno o varios archivos de origen a un único DataFrame.

Port de `src/features/usuarios/cargar/merge-fuente.ts`, con un cambio de
propósito importante: en la versión Next esto servía para EMPAQUETAR un .xlsx y
subirlo por HTTP. Aquí ya no hay red — se consolida para escribir directamente
el Parquet de destino.

Qué hace:
  * reordena cada fila a las columnas canónicas declaradas en el catálogo,
    haciendo match por cabecera NORMALIZADA (tolerante a tildes y mayúsculas);
  * descarta las columnas que no están en el catálogo;
  * rellena con "" las que falten (no debería quedar ninguna: la validación ya
    corrió antes, pero es una red de seguridad);
  * opcionalmente agrega ORIGIN_FILE como última columna, con el nombre del
    archivo de origen de cada fila (lo requieren DB Vida y DB Generales, cuyos
    servicios en `logic/` leen esa columna).
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.ingest.normalize import norm_header
from app.ingest.readers import leer_como_texto

COLUMNA_ORIGEN = "ORIGIN_FILE"


@dataclass
class ResultadoConsolidacion:
    df: pd.DataFrame
    total_filas: int
    archivos: int


def _reordenar(df: pd.DataFrame, columnas: list[str]) -> pd.DataFrame:
    """Proyecta el DataFrame sobre las columnas canónicas, por nombre normalizado."""
    lut: dict[str, str] = {}
    for real in df.columns:
        lut.setdefault(norm_header(real), real)

    salida = pd.DataFrame(index=df.index)
    for canonica in columnas:
        real = lut.get(norm_header(canonica))
        salida[canonica] = df[real] if real is not None else ""
    return salida


def consolidar(
    paths: list[str | Path],
    columnas: list[str],
    origin_file: bool = False,
) -> ResultadoConsolidacion:
    """
    Lee N archivos con la misma estructura y devuelve un único DataFrame
    normalizado a `columnas`.
    """
    if not paths:
        raise ValueError("No se recibió ningún archivo para consolidar")

    partes: list[pd.DataFrame] = []
    for path in paths:
        path = Path(path)
        bruto = leer_como_texto(path)
        parte = _reordenar(bruto, columnas)
        if origin_file:
            parte[COLUMNA_ORIGEN] = path.name
        partes.append(parte)

    df = partes[0] if len(partes) == 1 else pd.concat(partes, ignore_index=True)
    df = df.reset_index(drop=True)

    return ResultadoConsolidacion(df=df, total_filas=len(df), archivos=len(partes))
