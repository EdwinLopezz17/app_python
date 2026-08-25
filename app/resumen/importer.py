from __future__ import annotations

from pathlib import Path

from app.catalog import hallazgo_columns as cols
from app.ingest.normalize import norm_header
from app.ingest.readers import ErrorDeLectura, leer_como_texto

EXTENSIONES = {".xlsx", ".xlsm", ".xls", ".csv"}


class ErrorDeImportacion(Exception):
    pass


def _mapa_cabeceras(modelo: str) -> dict[str, str]:
    etiquetas = cols.etiquetas(modelo)
    alias = cols.alias(modelo)
    mapa: dict[str, str] = {}
    for campo, etiqueta in etiquetas.items():
        mapa.setdefault(norm_header(etiqueta), campo)
        mapa.setdefault(norm_header(campo), campo)
        for alterna in alias.get(campo, ()):
            mapa.setdefault(norm_header(alterna), campo)
    return mapa


def leer_detalle(path: str | Path, modelo: str) -> list[dict]:
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
    if not filas:
        return []
    presentes = set(filas[0])
    return [c for c in cols.etiquetas(modelo) if c in presentes]
