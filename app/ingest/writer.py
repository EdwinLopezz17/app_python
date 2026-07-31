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
import pyarrow as pa
import pyarrow.parquet as pq

from app import config
from app.catalog.fuentes import Slot
from app.ingest.merge import consolidar
from app.ingest.readers import leer_cabeceras, texto_celda
from app.ingest.validate import ResultadoValidacion, formato_permitido, validar_columnas


class ErrorDeCarga(Exception):
    """
    La carga no se pudo completar. El mensaje es apto para mostrar en pantalla.

    Cuando el fallo es por columnas faltantes, `faltantes` las lleva para que la
    interfaz pueda listarlas en la card en lugar de mostrar solo un texto
    genérico.
    """

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
    """
    Convierte el DataFrame a una tabla Arrow donde TODAS las columnas son
    `string`, con el esquema declarado de forma explícita.

    Por qué no basta con `df.astype(str)` antes de `to_parquet`:

      * `astype(str)` sobre una columna float escribe "123.0" — es exactamente el
        bug que aparecía en los códigos y DNIs.
      * `astype(str)` sobre nulos escribe los literales "nan", "None" y "NaT"
        dentro del Parquet. `logic/` los recibe como texto y no como vacío, así
        que un `if not valor` deja de funcionar.
      * Sin esquema explícito, pyarrow infiere el tipo de cada columna. Una
        columna que quedó totalmente vacía se infiere como `null` y no como
        `string`, y al leerla luego rompe cualquier `.str`.

    Declarar el esquema es la garantía de que el archivo en disco tiene el
    contrato prometido, no una aproximación.
    """
    columnas: list[pa.Array] = []
    for nombre in df.columns:
        serie = df[nombre]
        # `texto_celda` es la misma función que usa el lector: una sola regla de
        # conversión en toda la aplicación, no dos que puedan divergir.
        limpia = serie.map(texto_celda)
        columnas.append(pa.array(limpia.tolist(), type=pa.string()))

    esquema = pa.schema([pa.field(str(c), pa.string()) for c in df.columns])
    return pa.Table.from_arrays(columnas, schema=esquema)


def escribir_parquet(df: pd.DataFrame, destino: Path) -> None:
    """Escribe el DataFrame como Parquet de forma atómica, todo en string."""
    destino.parent.mkdir(parents=True, exist_ok=True)

    tabla = a_tabla_string(df)

    fd, tmp_name = tempfile.mkstemp(
        suffix=".parquet.tmp", prefix=destino.stem + "-", dir=destino.parent
    )
    os.close(fd)
    tmp = Path(tmp_name)
    try:
        pq.write_table(tabla, tmp, compression=config.COMPRESION)
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
