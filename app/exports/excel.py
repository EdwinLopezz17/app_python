from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

from app.catalog import formatos, hallazgo_columns as cols

GRIS_BORDE = "#BDC8D0"
ANCHO_MIN, ANCHO_MAX = 10, 45

# Formato con el que se escriben las celdas de fecha en Excel.
# Si se quiere hora, cambiar a "dd/mm/yyyy hh:mm".
FORMATO_FECHA = "dd/mm/yyyy"

# Fechas ISO (YYYY-MM-DD...). Se detectan aparte porque con dayfirst=True
# pandas invierte este formato.
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}")

# Valores que las fuentes usan como "sin fecha" y que no deben quedar
# escritos como texto en la columna.
_SIN_FECHA = {"", "-", "--", "N/A", "NA", "NAT", "NAN", "NONE", "NULL", "NUNCA"}


def nombre_sugerido(hallazgo_id: str) -> str:
    marca = datetime.now().strftime("%Y%m%d-%H%M")
    return f"hallazgo-{hallazgo_id}-{marca}.xlsx"


def _sin_zona(valor: datetime) -> datetime:
    # xlsxwriter no acepta datetimes con tzinfo.
    return valor.replace(tzinfo=None) if valor.tzinfo is not None else valor


def a_fecha(valor: Any) -> Any:
    if valor is None or valor is pd.NaT:
        return ""
    if isinstance(valor, pd.Timestamp):
        return "" if pd.isna(valor) else _sin_zona(valor.to_pydatetime())
    if isinstance(valor, datetime):
        return _sin_zona(valor)
    if isinstance(valor, date):
        return datetime(valor.year, valor.month, valor.day)

    try:
        if valor != valor:  # NaN / NaT
            return ""
    except (TypeError, ValueError):
        pass

    texto = str(valor).strip()
    if texto.upper() in _SIN_FECHA:
        return ""

    try:
        ts = pd.to_datetime(
            texto,
            errors="coerce",
            dayfirst=not bool(_ISO.match(texto)),
            format="mixed",
        )
    except Exception:
        return valor

    if ts is None or pd.isna(ts):
        return valor
    return _sin_zona(ts.to_pydatetime())


def exportar(
    df: pd.DataFrame,
    destino: str | Path,
    modelo: str | None = None,
    hoja: str = "Hallazgos",
    columnas_extra: Sequence[str] = (),
) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    for extra in columnas_extra:
        if extra not in df.columns:
            df[extra] = ""

    for campo in list(df.columns):
        fmt = formatos.formato(modelo, str(campo))
        if fmt is not None:
            df[campo] = df[campo].map(lambda v, f=fmt: formatos.texto(v, f))

    if modelo:
        columnas = cols.ordenar(modelo, [str(c) for c in df.columns])
        salida = df[columnas].rename(columns=cols.etiquetas(modelo))
    else:
        columnas = [str(c) for c in df.columns]
        salida = df.copy()

    campos_origen = [str(c) for c in columnas]

    idx_fechas: set[int] = set()
    for idx, campo in enumerate(campos_origen):
        if not cols.es_fecha(modelo, campo):
            continue
        idx_fechas.add(idx)
        salida.isetitem(idx, salida.iloc[:, idx].map(a_fecha))

    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        salida.to_excel(writer, sheet_name=hoja, index=False, startrow=1, header=False)
        libro = writer.book
        hoja_xl = writer.sheets[hoja]

        base_celda = {
            "border": 1, "border_color": GRIS_BORDE, "valign": "top",
            "font_name": "Inter", "font_size": 10,
        }
        fmt_celda = libro.add_format(base_celda)
        fmt_fecha = libro.add_format({**base_celda, "num_format": FORMATO_FECHA})

        cache_formatos: dict[str, object] = {}

        def formato_cabecera(campo: str):
            grupo = cols.grupo(modelo, campo)
            if grupo.id not in cache_formatos:
                cache_formatos[grupo.id] = libro.add_format({
                    "bold": True, "font_color": grupo.text, "bg_color": grupo.fill,
                    "border": 1, "border_color": grupo.fill,
                    "align": "left", "valign": "vcenter", "text_wrap": True,
                    "font_name": "Inter", "font_size": 10,
                })
            return cache_formatos[grupo.id]

        for idx, nombre in enumerate(salida.columns):
            campo = campos_origen[idx]
            hoja_xl.write(0, idx, str(nombre), formato_cabecera(campo))
            ancho = cols.definicion(modelo, campo).ancho_excel
            if len(salida):
                muestra = salida.iloc[: min(200, len(salida)), idx]
                largo = max((len(str(v)) for v in muestra), default=0)
                ancho = max(ancho, min(largo + 2, ANCHO_MAX))
            hoja_xl.set_column(
                idx, idx, max(ancho, ANCHO_MIN),
                fmt_fecha if idx in idx_fechas else fmt_celda,
            )

        for idx in sorted(idx_fechas):
            for fila, valor in enumerate(salida.iloc[:, idx], start=1):
                if isinstance(valor, datetime):
                    hoja_xl.write_datetime(fila, idx, valor, fmt_fecha)
                elif valor == "":
                    hoja_xl.write_blank(fila, idx, None, fmt_fecha)
                else:
                    hoja_xl.write_string(fila, idx, str(valor), fmt_fecha)

        hoja_xl.freeze_panes(1, 0)
        if len(salida.columns):
            hoja_xl.autofilter(0, 0, max(len(salida), 1), len(salida.columns) - 1)
        hoja_xl.set_row(0, 32)

    return destino
