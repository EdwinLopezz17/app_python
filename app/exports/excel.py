from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

from app.catalog import colors, display

GRIS_BORDE = "#BDC8D0"
ANCHO_MIN, ANCHO_MAX = 12, 45


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
    """Exporta el detalle del hallazgo.

    `columnas_extra` son campos que no vienen en el DataFrame y se agregan
    VACÍOS al final para que el usuario los llene en Excel (Responsable y
    Comentario) y devuelva el archivo en «Generar Resumen».
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    df = df.copy()
    for extra in columnas_extra:
        if extra not in df.columns:
            df[extra] = ""

    if modelo:
        etiquetas = display.etiquetas(modelo)
        columnas = [c for c in etiquetas if c in df.columns]
        columnas += [c for c in df.columns if c not in etiquetas]
        salida = df[columnas].rename(columns=etiquetas)
    else:
        columnas = list(df.columns)
        salida = df

    # Nombre de campo original por posición: la cabecera visible ya está
    # renombrada, pero el grupo de color se resuelve por el campo del modelo.
    campos_origen = [str(c) for c in columnas]

    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        salida.to_excel(writer, sheet_name=hoja, index=False, startrow=1, header=False)
        libro = writer.book
        hoja_xl = writer.sheets[hoja]

        fmt_celda = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "valign": "top",
            "font_name": "Inter", "font_size": 10,
        })

        # Un formato por grupo de color; se reutiliza entre columnas del mismo
        # origen. Mismos hex que la tabla y que el front (lib/theme.ts).
        cache_formatos: dict[str, object] = {}

        def formato_cabecera(campo: str):
            grupo = colors.grupo(modelo, campo)
            if grupo.id not in cache_formatos:
                cache_formatos[grupo.id] = libro.add_format({
                    "bold": True, "font_color": grupo.text, "bg_color": grupo.fill,
                    "border": 1, "border_color": grupo.fill,
                    "align": "left", "valign": "vcenter", "text_wrap": True,
                    "font_name": "Inter", "font_size": 10,
                })
            return cache_formatos[grupo.id]

        for idx, nombre in enumerate(salida.columns):
            hoja_xl.write(0, idx, str(nombre), formato_cabecera(campos_origen[idx]))
            ancho = max(len(str(nombre)) + 4, ANCHO_MIN)
            if len(salida) and idx < len(salida.columns):
                muestra = salida.iloc[: min(200, len(salida)), idx].astype(str)
                largo = int(muestra.str.len().max() or 0)
                ancho = max(ancho, min(largo + 2, ANCHO_MAX))
            hoja_xl.set_column(idx, idx, ancho, fmt_celda)

        hoja_xl.freeze_panes(1, 0)
        if len(salida.columns):
            hoja_xl.autofilter(0, 0, max(len(salida), 1), len(salida.columns) - 1)
        hoja_xl.set_row(0, 32)

    return destino
