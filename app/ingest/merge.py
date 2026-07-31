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
