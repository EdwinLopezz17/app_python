from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app.ingest.normalize import norm_header
from app.ingest.readers import BASES, leer_como_texto

COLUMNA_ORIGEN = "ORIGIN_FILE"

@dataclass
class ResultadoConsolidacion:
    df: pd.DataFrame
    total_filas: int
    archivos: int

def _agrupar(df: pd.DataFrame) -> dict[str, list[str]]:
    bases = df.attrs.get(BASES, {})
    grupos: dict[str, list[str]] = {}
    for real in df.columns:
        clave = norm_header(bases.get(real, real))
        grupos.setdefault(clave, []).append(real)
    return grupos

def _repeticiones(brutos: list[pd.DataFrame], columnas: list[str]) -> dict[str, int]:
    maximos: dict[str, int] = {}
    for df in brutos:
        grupos = _agrupar(df)
        for canonica in columnas:
            clave = norm_header(canonica)
            actual = len(grupos.get(clave, []))
            if actual > maximos.get(clave, 0):
                maximos[clave] = actual
    return maximos

def _reordenar(
    df: pd.DataFrame, columnas: list[str], repeticiones: dict[str, int]
) -> pd.DataFrame:
    grupos = _agrupar(df)

    salida = pd.DataFrame(index=df.index)
    duplicadas: list[tuple[str, object]] = []

    for canonica in columnas:
        clave = norm_header(canonica)
        reales = grupos.get(clave, [])
        total = max(repeticiones.get(clave, 0), 1)

        if total == 1:
            salida[canonica] = df[reales[0]] if reales else ""
            continue

        salida[f"{canonica}1"] = df[reales[0]] if reales else ""
        for orden in range(2, total + 1):
            real = reales[orden - 1] if len(reales) >= orden else None
            duplicadas.append(
                (f"{canonica}{orden}", df[real] if real is not None else "")
            )
    for nombre, serie in duplicadas:
        salida[nombre] = serie

    return salida

def consolidar(
    paths: list[str | Path],
    columnas: list[str],
    origin_file: bool = False,
) -> ResultadoConsolidacion:
    if not paths:
        raise ValueError("No se proporcionaron rutas de archivos para consolidar.")

    rutas = [Path(p) for p in paths]
    brutos = [leer_como_texto(path, columnas) for path in rutas]
    repeticiones = _repeticiones(brutos, columnas)

    partes: list[pd.DataFrame] = []
    for path, bruto in zip(rutas, brutos):
        parte = _reordenar(bruto, columnas, repeticiones)
        if origin_file:
            parte[COLUMNA_ORIGEN] = path.name
        partes.append(parte)

    df = partes[0] if len(partes) == 1 else pd.concat(partes, ignore_index=True)
    df = df.reset_index(drop=True)

    return ResultadoConsolidacion(df=df, total_filas=len(df), archivos=len(partes))

