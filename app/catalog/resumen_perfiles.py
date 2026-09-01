from __future__ import annotations

from app.resumen.engine import (
    BloquePoblacion,
    ConfigPoblacion,
    ConfigResumen,
    Filtro,
    Metrica,
)

COLUMNAS_ACCION = ("Acción Correctiva", "Comentario")

SOCIEDADES = ("PACIFICO CIA SEG Y REASEG", "Pacifico SA EPS")

CODIGOS_SOCIEDAD = {
    "PACIFICO CIA SEG Y REASEG": "CIA SEG",
    "Pacifico SA EPS": "SA EPS",
}

METRICAS_REPORTE = (
    Metrica(id="roles", label="Roles", campo="rol_gdh", modo="distinto"),
    Metrica(id="usuarios", label="Usuarios", campo="dni"),
)

METRICAS_PROVEEDOR = (
    Metrica(id="dni", label="Cuenta de dni", campo="dni"),
)

HALLAZGO_ROL = (Filtro(campo="validacion_rol", op="no_vacio"),)

HALLAZGO_PROVEEDOR = (
    Filtro(campo="username_pps", op="contiene", valor="no existe en ad"),
    Filtro(campo="username_vida", op="contiene", valor="no existe en ad"),
)

POBLACION_ACTIVOS_GDH = ConfigPoblacion(
    campo_bloque="tipo_rol",
    campo_columna="sociedad",
    columnas=SOCIEDADES,
    codigos_columna=CODIGOS_SOCIEDAD,
    bloques=(
        BloquePoblacion(
            titulo="PLANILLA",
            valor="Planilla",
            metricas=METRICAS_REPORTE,
            hallazgo=HALLAZGO_ROL,
            etiqueta_total="Reporte GDH",
        ),
        BloquePoblacion(
            titulo="FFVV",
            valor="FFVV",
            metricas=METRICAS_REPORTE,
            hallazgo=HALLAZGO_ROL,
            etiqueta_total="Reporte GDH",
        ),
        BloquePoblacion(
            titulo="PROVEEDORES",
            valor="Proveedor",
            metricas=METRICAS_PROVEEDOR,
            hallazgo=HALLAZGO_PROVEEDOR,
            etiqueta_total="Cuenta de dni",
            etiqueta_hallazgo="No existen en AD",
            etiqueta_porcentaje="% No existen en AD",
        ),
    ),
)

CONFIGS: dict[str, ConfigResumen] = {
    "activos-gdh": ConfigResumen(
        hallazgo_id="activos-gdh",
        modelo="GDHRows",
        escenarios=(),
        archivo="resumen-activos-gdh.xlsx",
        titulo="ACTIVOS GDH",
        poblacion=POBLACION_ACTIVOS_GDH,
        columnas_accion=COLUMNAS_ACCION,
    ),
}
