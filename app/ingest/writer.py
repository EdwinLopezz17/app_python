from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app import config
from app.catalog.fuentes import Slot
from app.ingest.merge import consolidar
from app.ingest.readers import leer_cabeceras, texto_celda
from app.ingest.validate import ResultadoValidacion, formato_permitido, validar_columnas


class ErrorDeCarga(Exception):

    def __init__(self, mensaje: str, faltantes: list[str] | None = None) -> None:
        super().__init__(mensaje)
        self.faltantes = faltantes or []


@dataclass
class ResultadoCarga:
    slot: Slot
    destino: Path
    total_filas: int
    archivos: int
    validacion: ResultadoValidacion


def a_tabla_string(df: pd.DataFrame) -> pa.Table:
    columnas: list[pa.Array] = []
    for nombre in df.columns:
        serie = df[nombre]
        limpia = serie.map(texto_celda)
        columnas.append(pa.array(limpia.tolist(), type=pa.string()))

    esquema = pa.schema([pa.field(str(c), pa.string()) for c in df.columns])
    return pa.Table.from_arrays(columnas, schema=esquema)


def escribir_parquet(df: pd.DataFrame, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)

    tabla = a_tabla_string(df)

    fd, tmp_name = tempfile.mkstemp(
        suffix=".parquet.tmp", prefix=destino.stem + "-", dir=destino.parent
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        pq.write_table(tabla, tmp, compression=config.COMPRESION)
        os.replace(tmp, destino)
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def validar_archivos(slot: Slot, paths: list[str | Path]) -> ResultadoValidacion:
    if not paths:
        raise ErrorDeCarga("No se seleccionó ningún archivo.")

    if not slot.multiple and len(paths) > 1:
        raise ErrorDeCarga(
            f"'{slot.display_label}' admite un solo archivo, se seleccionaron {len(paths)}."
        )

    peor: ResultadoValidacion | None = None
    for path in paths:
        path = Path(path)
        if not formato_permitido(path.name):
            raise ErrorDeCarga(
                f"Formato no permitido: {path.name}. "
                f"Se aceptan {', '.join(sorted({'.csv', '.xls', '.xlsx'}))}."
            )
        resultado = validar_columnas(slot.columns, leer_cabeceras(path))
        if not resultado.ok:
            return resultado
        if peor is None or len(resultado.extra) > len(peor.extra):
            peor = resultado

    return peor


def cargar(slot: Slot, paths: list[str | Path]) -> ResultadoCarga:
    validacion = validar_archivos(slot, paths)
    if not validacion.ok:
        raise ErrorDeCarga(validacion.mensaje(), faltantes=validacion.faltantes)

    consolidado = consolidar(paths, slot.columns, origin_file=slot.origin_file)
    if consolidado.total_filas == 0:
        raise ErrorDeCarga("El archivo no contiene filas de datos.")

    destino = config.destino(slot.key, slot.subfolder)
    escribir_parquet(consolidado.df, destino)

    return ResultadoCarga(
        slot=slot,
        destino=destino,
        total_filas=consolidado.total_filas,
        archivos=consolidado.archivos,
        validacion=validacion,
    )
