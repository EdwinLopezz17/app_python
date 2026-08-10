from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

from app.catalog import formatos, hallazgo_columns as cols

GRIS_BORDE = "#BDC8D0"
ANCHO_MIN, ANCHO_MAX = 10, 45


def nombre_sugerido(hallazgo_id: str) -> str:
    marca = datetime.now().strftime("%Y%m%d-%H%M")
    return f"hallazgo-{hallazgo_id}-{marca}.xlsx"


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
        salida = df


    campos_origen = [str(c) for c in columnas]

    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        salida.to_excel(writer, sheet_name=hoja, index=False, startrow=1, header=False)
        libro = writer.book
        hoja_xl = writer.sheets[hoja]

        fmt_celda = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "valign": "top",
            "font_name": "Inter", "font_size": 10,
        })


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
                muestra = salida.iloc[: min(200, len(salida)), idx].astype(str)
                largo = int(muestra.str.len().max() or 0)
                ancho = max(ancho, min(largo + 2, ANCHO_MAX))
            hoja_xl.set_column(idx, idx, max(ancho, ANCHO_MIN), fmt_celda)

        hoja_xl.freeze_panes(1, 0)
        if len(salida.columns):
            hoja_xl.autofilter(0, 0, max(len(salida), 1), len(salida.columns) - 1)
        hoja_xl.set_row(0, 32)

    return destino
