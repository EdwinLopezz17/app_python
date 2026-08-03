"""Lectura del Excel de detalle que el usuario devuelve con Responsable lleno.

Port de `import-excel.ts` / `import-excel-ad.ts`. Reutiliza el lector de
`app/ingest/readers.py` (mismo tratamiento de tipos que la carga de fuentes, así
que los identificadores no se distorsionan) y traduce las cabeceras visibles del
archivo a los nombres de campo del modelo usando `catalog/display.py` al revés.

La comparación de cabeceras pasa por `norm_header`, así que tolera tildes,
mayúsculas y espacios repetidos: da igual si el usuario reordena columnas o
reescribe «Fecha de Cese» como «FECHA DE CESE».
"""

from __future__ import annotations

from pathlib import Path

from app.catalog import display
from app.ingest.normalize import norm_header
from app.ingest.readers import ErrorDeLectura, leer_como_texto

EXTENSIONES = {".xlsx", ".xlsm", ".xls", ".csv"}


class ErrorDeImportacion(Exception):
    pass


def _mapa_cabeceras(modelo: str) -> dict[str, str]:
    """{cabecera normalizada: campo del modelo}, aceptando etiqueta o campo."""
    etiquetas = display.etiquetas(modelo)
    mapa: dict[str, str] = {}
    for campo, etiqueta in etiquetas.items():
        mapa.setdefault(norm_header(etiqueta), campo)
        mapa.setdefault(norm_header(campo), campo)
    return mapa


def leer_detalle(path: str | Path, modelo: str) -> list[dict]:
    """Devuelve las filas del Excel como dicts con los campos del modelo.

    Las columnas que no correspondan a ningún campo conocido se conservan con su
    cabecera original, por si el usuario agregó anotaciones propias.
    """
    path = Path(path)
    if path.suffix.lower() not in EXTENSIONES:
        raise ErrorDeImportacion(
            "El archivo debe ser .xlsx (el mismo que exporta la app)."
        )

    try:
        df = leer_como_texto(path)
    except ErrorDeLectura as exc:
        raise ErrorDeImportacion(str(exc)) from exc

    if df.empty:
        raise ErrorDeImportacion("No se encontraron filas de datos en el archivo.")

    mapa = _mapa_cabeceras(modelo)
    columnas = {c: mapa.get(norm_header(c), str(c)) for c in df.columns}

    filas: list[dict] = []
    for registro in df.to_dict("records"):
        filas.append({columnas[c]: v for c, v in registro.items()})
    return filas


def campos_presentes(filas: list[dict], modelo: str) -> list[str]:
    """Campos del modelo que sí venían en el archivo (para diagnóstico)."""
    if not filas:
        return []
    presentes = set(filas[0])
    return [c for c in display.etiquetas(modelo) if c in presentes]
