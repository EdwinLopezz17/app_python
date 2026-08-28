from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import csv

import pandas as pd

from app.ingest import config
from app.catalog.fuentes import Slot
from app.ingest.merge import consolidar
from app.ingest.normalize import limpiar_celda
from app.ingest.readers import leer_cabeceras, texto_celda
from app.ingest.validate import ResultadoValidacion, formato_permitido, validar_columnas
from app.storage import files


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


def a_texto(df: pd.DataFrame) -> pd.DataFrame:
    salida = pd.DataFrame(index=df.index)
    for nombre in df.columns:
        salida[str(nombre)] = df[nombre].map(texto_celda).map(limpiar_celda)
    return salida


def escribir_csv(df: pd.DataFrame, destino: Path) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)

    texto = a_texto(df)

    fd, tmp_name = tempfile.mkstemp(
        suffix=".csv.tmp", prefix=destino.stem + "-", dir=destino.parent
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        texto.to_csv(
            tmp,
            sep=config.CSV_SEP,
            index=False,
            encoding=config.CSV_ENCODING,
            lineterminator=config.CSV_TERMINADOR,
            quotechar=config.CSV_QUOTECHAR,
            quoting=csv.QUOTE_MINIMAL,
            na_rep="",
        )
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
    escribir_csv(consolidado.df, destino)

    nombres = (
        list(dict.fromkeys(Path(p).name for p in paths)) if slot.origin_file else []
    )
    files.registrar_medida(
        destino,
        filas=consolidado.total_filas,
        columnas=len(consolidado.df.columns),
        archivos=nombres,
    )

    return ResultadoCarga(
        slot=slot,
        destino=destino,
        total_filas=consolidado.total_filas,
        archivos=consolidado.archivos,
        validacion=validacion,
    )
