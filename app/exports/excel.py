"""
Exportación de un hallazgo a .xlsx.

Usa EXACTAMENTE las mismas etiquetas que la tabla en pantalla
(`app/catalog/display.py`). Ese es el punto: el auditor ve "Fecha Último Login"
en la aplicación y encuentra "Fecha Último Login" en el Excel. Es imposible que
se desalineen porque salen del mismo diccionario.

El estilo sigue el design system Corporate Minimalist: cabecera en el azul
corporativo, fila congelada, autofiltro y anchos calculados.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from app.catalog import display

AZUL_PRIMARIO = "#006386"
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
) -> Path:
    """
    Escribe el DataFrame como .xlsx con las cabeceras visibles del modelo.

    Si `modelo` es None (hallazgo aún sin dataclass asociado), se exportan los
    nombres de columna tal cual vienen.
    """
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    if modelo:
        etiquetas = display.etiquetas(modelo)
        # Solo las columnas que realmente están en el DataFrame, en orden de catálogo.
        columnas = [c for c in etiquetas if c in df.columns]
        # Y al final, cualquier columna inesperada, para no perder información.
        columnas += [c for c in df.columns if c not in etiquetas]
        salida = df[columnas].rename(columns=etiquetas)
    else:
        salida = df

    with pd.ExcelWriter(destino, engine="xlsxwriter") as writer:
        salida.to_excel(writer, sheet_name=hoja, index=False, startrow=1, header=False)
        libro = writer.book
        hoja_xl = writer.sheets[hoja]

        fmt_cabecera = libro.add_format({
            "bold": True, "font_color": "#FFFFFF", "bg_color": AZUL_PRIMARIO,
            "border": 1, "border_color": AZUL_PRIMARIO,
            "align": "left", "valign": "vcenter", "text_wrap": True,
            "font_name": "Inter", "font_size": 10,
        })
        fmt_celda = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "valign": "top",
            "font_name": "Inter", "font_size": 10,
        })

        for idx, nombre in enumerate(salida.columns):
            hoja_xl.write(0, idx, str(nombre), fmt_cabecera)
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
