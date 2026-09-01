from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

from app.catalog import formatos, hallazgo_columns as cols
from app.exports import resumen_activos_gdh as motor
from app.exports.excel import FORMATO_FECHA, GRIS_BORDE, a_fecha

MODELO = "GDHRows"
HOJA_DATOS = "ACTIVOS GDH"
HOJA_RESUMEN = "RESUMEN"

COLUMNAS_ACCION = ("Acción Correctiva", "Comentario")

FUENTE = "Calibri"

AZUL_OSCURO = "#283044"
AZUL_PRIMARIO = "#006386"
AZUL_CLARO = "#e2e7ff"
AMBAR = "#ffe6cc"
GRIS_SUAVE = "#f2f3ff"
NARANJA = "#bc5800"

COL_INICIO = 1
FILA_INICIO = 1


def nombre_sugerido() -> str:
    marca = datetime.now().strftime("%Y%m%d-%H%M")
    return f"activos-gdh-{marca}.xlsx"


def _formatos(libro):
    base = {"font_name": FUENTE, "font_size": 10, "border": 1, "border_color": GRIS_BORDE}
    return {
        "titulo": libro.add_format({
            **base, "bold": True, "bg_color": AZUL_OSCURO, "font_color": "#ffffff",
            "align": "left", "valign": "vcenter", "font_size": 11,
        }),
        "cabecera": libro.add_format({
            **base, "bold": True, "bg_color": AZUL_PRIMARIO, "font_color": "#ffffff",
            "align": "center", "valign": "vcenter",
        }),
        "subcabecera": libro.add_format({
            **base, "bold": True, "bg_color": AZUL_CLARO, "font_color": "#131b2e",
            "align": "center", "valign": "vcenter",
        }),
        "enlace": libro.add_format({
            **base, "bold": True, "bg_color": AZUL_CLARO, "font_color": AZUL_PRIMARIO,
            "align": "center", "valign": "vcenter", "underline": 1,
        }),
        "etiqueta": libro.add_format({**base, "bold": True, "align": "left"}),
        "numero": libro.add_format({**base, "align": "center", "num_format": "#,##0"}),
        "etiqueta_hallazgo": libro.add_format({
            **base, "bold": True, "bg_color": AMBAR, "align": "left",
        }),
        "numero_hallazgo": libro.add_format({
            **base, "bg_color": AMBAR, "align": "center", "num_format": "#,##0",
        }),
        "etiqueta_pct": libro.add_format({
            **base, "bold": True, "bg_color": GRIS_SUAVE, "align": "left",
        }),
        "pct": libro.add_format({
            **base, "bold": True, "bg_color": GRIS_SUAVE, "align": "center",
            "num_format": "0.00%",
        }),
        "celda": libro.add_format({**base, "valign": "top"}),
        "fecha": libro.add_format({**base, "valign": "top", "num_format": FORMATO_FECHA}),
    }


def _formato_cabecera_campo(libro, cache: dict, campo: str, extra: bool):
    clave = "EXTRA" if extra else cols.grupo(MODELO, campo).id
    if clave not in cache:
        if extra:
            relleno, texto = NARANJA, "#ffffff"
        else:
            grupo = cols.grupo(MODELO, campo)
            relleno, texto = grupo.fill, grupo.text
        cache[clave] = libro.add_format({
            "bold": True, "font_color": texto, "bg_color": relleno,
            "border": 1, "border_color": relleno,
            "align": "left", "valign": "vcenter", "text_wrap": True,
            "font_name": FUENTE, "font_size": 10,
        })
    return cache[clave]


def _preparar(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    df = df.copy()
    for campo in list(df.columns):
        fmt = formatos.formato(MODELO, str(campo))
        if fmt is not None:
            df[campo] = df[campo].map(lambda v, f=fmt: formatos.texto(v, f))

    columnas = cols.ordenar(MODELO, [str(c) for c in df.columns])
    return df[columnas], columnas


def _escribir_tabla(hoja, df: pd.DataFrame, campos: list[str], fmts, libro,
                    cache: dict, extras: Sequence[str] = ()) -> None:
    etiquetas = cols.etiquetas(MODELO)
    todos = list(campos) + list(extras)

    for idx, campo in enumerate(todos):
        es_extra = campo in extras
        cabecera = campo if es_extra else etiquetas.get(campo, campo)
        hoja.write(0, idx, cabecera, _formato_cabecera_campo(libro, cache, campo, es_extra))
        ancho = 24 if es_extra else cols.ancho(MODELO, campo) / 7
        hoja.set_column(idx, idx, round(ancho, 1))

    for fila_idx, (_, fila) in enumerate(df.iterrows(), start=1):
        for col_idx, campo in enumerate(todos):
            if campo in extras:
                hoja.write(fila_idx, col_idx, "", fmts["celda"])
                continue
            valor = fila[campo]
            if cols.es_fecha(MODELO, campo):
                convertido = a_fecha(valor)
                if convertido == "":
                    hoja.write(fila_idx, col_idx, "", fmts["fecha"])
                else:
                    hoja.write_datetime(fila_idx, col_idx, convertido, fmts["fecha"])
            else:
                texto = "" if valor is None or valor != valor else str(valor)
                hoja.write(fila_idx, col_idx, texto, fmts["celda"])

    hoja.freeze_panes(1, 0)
    if len(df) > 0:
        hoja.autofilter(0, 0, len(df), len(todos) - 1)


def _escribir_bloque_reporte(hoja, fila, bloque, fmts, hojas_detalle) -> int:
    c = COL_INICIO
    hoja.merge_range(fila, c, fila, c + 4, bloque.titulo, fmts["titulo"])
    fila += 1

    hoja.merge_range(fila, c + 1, fila, c + 4, "Reporte GDH", fmts["cabecera"])
    fila += 1

    for i, dato in enumerate(bloque.sociedades):
        ini = c + 1 + i * 2
        nombre = motor.nombre_hoja(
            motor.TIPO_PLANILLA if bloque.titulo == "PLANILLA" else motor.TIPO_FFVV,
            dato.sociedad,
        )
        if nombre in hojas_detalle:
            hoja.merge_range(fila, ini, fila, ini + 1, "", fmts["enlace"])
            hoja.write_url(
                fila, ini, f"internal:'{nombre}'!A1", fmts["enlace"], dato.sociedad
            )
        else:
            hoja.merge_range(fila, ini, fila, ini + 1, dato.sociedad, fmts["subcabecera"])
    fila += 1

    hoja.write(fila, c, "", fmts["subcabecera"])
    for i in range(len(bloque.sociedades)):
        ini = c + 1 + i * 2
        hoja.write(fila, ini, "Roles", fmts["subcabecera"])
        hoja.write(fila, ini + 1, "Usuarios", fmts["subcabecera"])
    fila += 1

    hoja.write(fila, c, "Reporte GDH", fmts["etiqueta"])
    for i, dato in enumerate(bloque.sociedades):
        ini = c + 1 + i * 2
        hoja.write_number(fila, ini, dato.reporte.roles, fmts["numero"])
        hoja.write_number(fila, ini + 1, dato.reporte.usuarios, fmts["numero"])
    fila += 1

    hoja.write(fila, c, "# Hallazgos inicial", fmts["etiqueta_hallazgo"])
    for i, dato in enumerate(bloque.sociedades):
        ini = c + 1 + i * 2
        hoja.write_number(fila, ini, dato.hallazgos.roles, fmts["numero_hallazgo"])
        hoja.write_number(fila, ini + 1, dato.hallazgos.usuarios, fmts["numero_hallazgo"])
    fila += 1

    hoja.write(fila, c, "% Hallazgos inicial", fmts["etiqueta_pct"])
    for i, dato in enumerate(bloque.sociedades):
        ini = c + 1 + i * 2
        hoja.write_number(fila, ini, dato.pct_roles, fmts["pct"])
        hoja.write_number(fila, ini + 1, dato.pct_usuarios, fmts["pct"])
    fila += 2

    return fila


def _escribir_bloque_proveedores(hoja, fila, proveedores, fmts, hojas_detalle) -> int:
    c = COL_INICIO
    hoja.merge_range(fila, c, fila, c + 2, "PROVEEDORES", fmts["titulo"])
    fila += 1

    hoja.write(fila, c, "", fmts["subcabecera"])
    for i, dato in enumerate(proveedores):
        nombre = motor.nombre_hoja(motor.TIPO_PROVEEDOR, dato.sociedad)
        if nombre in hojas_detalle:
            hoja.write_url(
                fila, c + 1 + i, f"internal:'{nombre}'!A1", fmts["enlace"], dato.sociedad
            )
        else:
            hoja.write(fila, c + 1 + i, dato.sociedad, fmts["subcabecera"])
    fila += 1

    hoja.write(fila, c, "Cuenta de dni", fmts["etiqueta"])
    for i, dato in enumerate(proveedores):
        hoja.write_number(fila, c + 1 + i, dato.cuenta_dni, fmts["numero"])
    fila += 1

    hoja.write(fila, c, "No existen en AD", fmts["etiqueta_hallazgo"])
    for i, dato in enumerate(proveedores):
        hoja.write_number(fila, c + 1 + i, dato.no_existen_ad, fmts["numero_hallazgo"])
    fila += 1

    hoja.write(fila, c, "% No existen en AD", fmts["etiqueta_pct"])
    for i, dato in enumerate(proveedores):
        hoja.write_number(fila, c + 1 + i, dato.pct, fmts["pct"])
    fila += 2

    return fila


def exportar(df: pd.DataFrame, destino: str | Path) -> Path:
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    salida, campos = _preparar(df)
    filas = motor.desde_dataframe(salida)
    resumen = motor.calcular(filas)
    escenarios = motor.escenarios_con_hallazgos(filas)
    hojas_detalle = {motor.nombre_hoja(t, s) for t, s, _ in escenarios}

    import xlsxwriter

    libro = xlsxwriter.Workbook(str(destino), {"remove_timezone": True})
    fmts = _formatos(libro)
    cache: dict = {}

    hoja_datos = libro.add_worksheet(HOJA_DATOS)
    _escribir_tabla(hoja_datos, salida, campos, fmts, libro, cache)

    hoja_resumen = libro.add_worksheet(HOJA_RESUMEN)
    hoja_resumen.hide_gridlines(2)
    hoja_resumen.set_column(0, 0, 3)
    hoja_resumen.set_column(COL_INICIO, COL_INICIO, 24)
    hoja_resumen.set_column(COL_INICIO + 1, COL_INICIO + 4, 18)

    fila = FILA_INICIO
    for bloque in resumen.reporte_gdh:
        fila = _escribir_bloque_reporte(hoja_resumen, fila, bloque, fmts, hojas_detalle)
    _escribir_bloque_proveedores(
        hoja_resumen, fila, resumen.proveedores, fmts, hojas_detalle
    )

    for tipo_rol, sociedad, hallazgos in escenarios:
        hoja = libro.add_worksheet(motor.nombre_hoja(tipo_rol, sociedad))
        detalle = pd.DataFrame(hallazgos)[campos]
        _escribir_tabla(hoja, detalle, campos, fmts, libro, cache, COLUMNAS_ACCION)

    libro.close()
    return destino
