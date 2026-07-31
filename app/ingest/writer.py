"""
Escritura del archivo de destino y pipeline completo de "Cargar Información".

Este módulo es la frontera con `logic/`: escribe el Parquet que después leerán
los servicios del backend. El nombre del archivo sale SIEMPRE de
`models.file_names.FileName`; nunca se construye a mano.

Todas las columnas se escriben como STRING. Ese es el contrato: la app de carga
no interpreta, solo transporta fielmente lo que el auditor descargó de cada
sistema. Quien convierte a fecha/booleano es `logic/`, que ya sabe el formato de
cada campo (ver `logic/share/utils.py -> to_datetime`).

La escritura es ATÓMICA: se escribe a un archivo temporal en la misma carpeta y
recién al terminar se reemplaza el definitivo. Si la app muere a mitad de una
carga de 200 MB, el archivo anterior queda intacto en lugar de quedar truncado.
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from app import config
from app.catalog.fuentes import Slot
from app.ingest.merge import consolidar
from app.ingest.readers import leer_cabeceras
from app.ingest.validate import ResultadoValidacion, formato_permitido, validar_columnas


class ErrorDeCarga(Exception):
    """La carga no se pudo completar. El mensaje es apto para mostrar en pantalla."""


@dataclass
class ResultadoCarga:
    slot: Slot
    destino: Path
    total_filas: int
    archivos: int
    validacion: ResultadoValidacion


def escribir_parquet(df: pd.DataFrame, destino: Path) -> None:
    """Escribe el DataFrame como Parquet de forma atómica."""
    destino.parent.mkdir(parents=True, exist_ok=True)

    # Todo como string, sin índice: es lo que espera leer `logic/`.
    df = df.astype(str)

    fd, tmp_name = tempfile.mkstemp(
        suffix=".parquet.tmp", prefix=destino.stem + "-", dir=destino.parent
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        df.to_parquet(tmp, engine="pyarrow", compression=config.COMPRESION, index=False)
        os.replace(tmp, destino)  # atómico en el mismo volumen
    except Exception:
        tmp.unlink(missing_ok=True)
        raise


def validar_archivos(slot: Slot, paths: list[str | Path]) -> ResultadoValidacion:
    """
    Valida formato y cabeceras ANTES de leer los archivos completos.

    Con varios archivos, todos deben cumplir; se devuelve el primer fallo, que es
    el que se le muestra al usuario.
    """
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

    return peor  # type: ignore[return-value]


def cargar(slot: Slot, paths: list[str | Path]) -> ResultadoCarga:
    """
    Pipeline completo: validar -> leer -> consolidar -> escribir Parquet.

    Es una función pura respecto de la UI: no sabe nada de Qt y se puede probar
    con pytest sin abrir una ventana.
    """
    validacion = validar_archivos(slot, paths)
    if not validacion.ok:
        raise ErrorDeCarga(validacion.mensaje())

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
