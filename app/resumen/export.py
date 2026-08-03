"""Excel de resumen: hoja «Escenarios» + una hoja de detalle por escenario.

Port de `export-resumen-ad.ts` y `export-resumen-excel.ts`. El front usa
exceljs; aquí se usa xlsxwriter, que es lo que ya emplea `app/exports/excel.py`.
Los colores de cabecera salen de `catalog/colors.py`, así que la hoja de detalle
se ve igual que la tabla de la app y que el Excel del front.

Dos formatos de hoja «Escenarios», según la config del hallazgo:

  · Sin `campo_grupo` (Active Directory): una fila por escenario, con
    hipervínculo a su hoja de detalle solo si tiene hallazgos.
  · Con `campo_grupo` (Aplicaciones): una fila por aplicación y un bloque de
    columnas por escenario, más la fila TOTAL.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Sequence

import xlsxwriter

from app.catalog import colors, display
from app.catalog.resumen_usuarios import ConfigResumen
from app.resumen import engine
from app.resumen.engine import Escenario

GRIS_BORDE = "#bdc8d0"
FONDO_TOTAL = "#eaedff"
AZUL_ENLACE = "#0563c1"
ANCHO_MIN, ANCHO_MAX = 12, 45


def con_sello(nombre: str, momento: datetime | None = None) -> str:
    """`resumen.xlsx` → `resumen_20260803_170500.xlsx` (igual que withTimestamp)."""
    momento = momento or datetime.now()
    sello = momento.strftime("%Y%m%d_%H%M%S")
    punto = nombre.rfind(".")
    if punto <= 0:
        return f"{nombre}_{sello}"
    return f"{nombre[:punto]}_{sello}{nombre[punto:]}"


def nombre_sugerido(config: ConfigResumen) -> str:
    return con_sello(config.archivo)


# ── Formatos ───────────────────────────────────────────────────────────────


class _Formatos:
    def __init__(self, libro: xlsxwriter.Workbook) -> None:
        self.libro = libro
        self._cabeceras: dict[str, object] = {}

        self.celda = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "valign": "top",
            "font_name": "Inter", "font_size": 10,
        })
        self.resumen = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE,
            "valign": "vcenter", "align": "center", "text_wrap": True,
            "font_name": "Inter", "font_size": 10,
        })
        self.resumen_izq = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE,
            "valign": "vcenter", "align": "left", "text_wrap": True,
            "font_name": "Inter", "font_size": 10,
        })
        self.total = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "bold": True,
            "bg_color": FONDO_TOTAL, "font_color": "#131b2e",
            "valign": "vcenter", "align": "center",
            "font_name": "Inter", "font_size": 10,
        })
        self.total_izq = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "bold": True,
            "bg_color": FONDO_TOTAL, "font_color": "#131b2e",
            "valign": "vcenter", "align": "left",
            "font_name": "Inter", "font_size": 10,
        })
        self.enlace = libro.add_format({
            "border": 1, "border_color": GRIS_BORDE, "bold": True,
            "font_color": AZUL_ENLACE, "underline": 1,
            "valign": "vcenter", "align": "center",
            "font_name": "Inter", "font_size": 10,
        })
        self.volver = libro.add_format({
            "bold": True, "font_color": AZUL_ENLACE, "underline": 1,
            "valign": "vcenter", "align": "center",
            "font_name": "Inter", "font_size": 10,
        })

    def cabecera(self, relleno: str, texto: str = "#ffffff"):
        clave = f"{relleno}|{texto}"
        if clave not in self._cabeceras:
            self._cabeceras[clave] = self.libro.add_format({
                "bold": True, "font_color": texto, "bg_color": relleno,
                "border": 1, "border_color": "#ffffff",
                "align": "center", "valign": "vcenter", "text_wrap": True,
                "font_name": "Inter", "font_size": 10,
            })
        return self._cabeceras[clave]

    def cabecera_campo(self, modelo: str, campo: str):
        grupo = colors.grupo(modelo, campo)
        return self.cabecera(grupo.fill, grupo.text)


# ── Hoja de detalle ────────────────────────────────────────────────────────


def _texto(valor) -> str:
    if valor is None:
        return ""
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor)


def _hoja_detalle(
    libro: xlsxwriter.Workbook, fmt: _Formatos, config: ConfigResumen,
    escenario: Escenario, filas: Sequence[dict],
) -> None:
    hoja = libro.add_worksheet(escenario.code)
    etiquetas = display.etiquetas(config.modelo)
    campos = list(escenario.columnas)

    # Fila 1: vuelta a la hoja resumen (igual que en el front).
    hoja.merge_range(0, 1, 0, 2, "", fmt.volver)
    hoja.write_url(0, 1, "internal:'Escenarios'!A1", fmt.volver, "VOLVER A ESCENARIOS")

    # Fila 3 (índice 2): cabeceras coloreadas por grupo de origen.
    for col, campo in enumerate(campos):
        hoja.write(2, col, etiquetas.get(campo, campo), fmt.cabecera_campo(config.modelo, campo))
    hoja.set_row(2, 28)

    for indice, fila in enumerate(filas):
        for col, campo in enumerate(campos):
            hoja.write(3 + indice, col, _texto(fila.get(campo)), fmt.celda)

    for col, campo in enumerate(campos):
        titulo = etiquetas.get(campo, campo)
        ancho = max(len(titulo) + 4, ANCHO_MIN)
        muestra = [len(_texto(f.get(campo))) for f in filas[:200]]
        if muestra:
            ancho = max(ancho, min(max(muestra) + 2, ANCHO_MAX))
        hoja.set_column(col, col, ancho)

    hoja.freeze_panes(3, 0)
    if campos:
        hoja.autofilter(2, 0, max(2 + len(filas), 3), len(campos) - 1)


# ── Hoja «Escenarios» — formato por escenario (Active Directory) ───────────


def _hoja_por_escenario(
    libro: xlsxwriter.Workbook, fmt: _Formatos, config: ConfigResumen,
    filas: Sequence[dict],
) -> list[tuple[Escenario, list[dict]]]:
    hoja = libro.add_worksheet("Escenarios")
    hoja.set_column(0, 0, 46)
    hoja.set_column(1, 3, 18)
    hoja.set_column(4, 4, 14)
    hoja.set_column(5, 5, 38)

    titulo = fmt.cabecera(colors.PRIMARY)
    hoja.merge_range(1, 1, 1, 4, config.titulo, titulo)
    hoja.merge_range(2, 1, 2, 4, "VIDA-PPS", fmt.cabecera(colors.INVERSE_SURFACE))

    cabeceras = [
        ("Escenarios de monitoreo", colors.PRIMARY),
        ("N° Hallazgos", colors.OUTLINE),
        ("Hallazgos GDH", colors.OUTLINE),
        ("Hallazgos ACCESOS", colors.OUTLINE),
        ("Hallazgos", colors.INVERSE_SURFACE),
        ("Comentario", colors.OUTLINE),
    ]
    for col, (texto, relleno) in enumerate(cabeceras):
        hoja.write(3, col, texto, fmt.cabecera(relleno))
    hoja.set_row(3, 30)

    detalles: list[tuple[Escenario, list[dict]]] = []
    fila_excel = 4
    for escenario in config.escenarios:
        alcance = engine.filas_de_escenario(filas, escenario)
        total = len(alcance)

        hoja.write(fila_excel, 0, escenario.title, fmt.resumen_izq)
        hoja.write_number(fila_excel, 1, total, fmt.resumen)
        hoja.write_number(
            fila_excel, 2,
            engine.contar_por_responsable(alcance, "GDH", escenario.campo_responsable),
            fmt.resumen,
        )
        hoja.write_number(
            fila_excel, 3,
            engine.contar_por_responsable(alcance, "ACCESOS", escenario.campo_responsable),
            fmt.resumen,
        )

        # Si no hay hallazgos no se genera hoja ni hipervínculo.
        if total:
            hoja.write_url(
                fila_excel, 4, f"internal:'{escenario.code}'!A1",
                fmt.enlace, escenario.code,
            )
            detalles.append((escenario, alcance))
        else:
            hoja.write(fila_excel, 4, escenario.code, fmt.resumen)

        hoja.write(fila_excel, 5, "", fmt.resumen)
        fila_excel += 1

    hoja.freeze_panes(4, 0)
    return detalles


# ── Hoja «Escenarios» — formato por grupo (Aplicaciones) ───────────────────


def _hoja_por_grupo(
    libro: xlsxwriter.Workbook, fmt: _Formatos, config: ConfigResumen,
    filas: Sequence[dict],
) -> list[tuple[Escenario, list[dict]]]:
    hoja = libro.add_worksheet("Escenarios")
    escenarios = list(config.escenarios)
    resumen = engine.por_grupo(filas, escenarios, config.campo_grupo or "")

    ancho_bloque = 3
    primera = 1                      # columna B
    total_cols = len(escenarios) * ancho_bloque

    hoja.set_column(primera, primera, 26)
    hoja.set_column(primera + 1, primera + total_cols, 16)
    hoja.set_column(primera + total_cols + 1, primera + total_cols + 1, 32)

    rellenos = [colors.PRIMARY, colors.SECONDARY, colors.TERTIARY,
                colors.INVERSE_SURFACE, colors.OUTLINE]

    # Fila 3: título general sobre todos los bloques.
    hoja.merge_range(
        2, primera + 1, 2, primera + total_cols, config.titulo,
        fmt.cabecera(colors.INVERSE_SURFACE),
    )
    hoja.set_row(2, 24)

    # Filas 4 y 5: título del escenario y enlace a su hoja.
    for indice, escenario in enumerate(escenarios):
        relleno = rellenos[indice % len(rellenos)]
        ini = primera + 1 + indice * ancho_bloque
        fin = ini + ancho_bloque - 1
        hoja.merge_range(3, ini, 3, fin, escenario.title, fmt.cabecera(relleno))
        hoja.merge_range(4, ini, 4, fin, "", fmt.cabecera(relleno))
        hoja.write_url(
            4, ini, f"internal:'{escenario.code}'!A1",
            fmt.cabecera(relleno), escenario.code,
        )
    hoja.set_row(3, 32)

    # Fila 6: cabeceras de columna.
    hoja.write(5, primera, config.etiqueta_grupo or "Grupo",
               fmt.cabecera(colors.INVERSE_SURFACE))
    subcabeceras = ["N° Hallazgos", "Hallazgos GDH", "Hallazgos ACCESOS"]
    for indice, escenario in enumerate(escenarios):
        relleno = rellenos[indice % len(rellenos)]
        for desplazamiento, texto in enumerate(subcabeceras):
            columna = primera + 1 + indice * ancho_bloque + desplazamiento
            hoja.write(5, columna, texto, fmt.cabecera(relleno))
    hoja.write(5, primera + total_cols + 1, "COMENTARIO", fmt.cabecera(colors.OUTLINE))
    hoja.set_row(5, 28)

    def escribir(fila_excel: int, fila: engine.FilaGrupo, es_total: bool) -> None:
        formato = fmt.total if es_total else fmt.resumen
        hoja.write(fila_excel, primera, fila.grupo,
                   fmt.total_izq if es_total else fmt.resumen_izq)
        for indice, escenario in enumerate(escenarios):
            base = primera + 1 + indice * ancho_bloque
            hoja.write_number(fila_excel, base, fila.total(escenario.code), formato)
            hoja.write_number(fila_excel, base + 1, fila.gdh(escenario.code), formato)
            hoja.write_number(fila_excel, base + 2, fila.accesos(escenario.code), formato)
        hoja.write(fila_excel, primera + total_cols + 1, "", formato)

    fila_excel = 6
    for fila in resumen.filas:
        escribir(fila_excel, fila, False)
        fila_excel += 1
    escribir(fila_excel, resumen.total, True)

    hoja.freeze_panes(6, primera + 1)

    return [(e, engine.filas_de_escenario(filas, e)) for e in escenarios]


# ── Punto de entrada ───────────────────────────────────────────────────────


def exportar(config: ConfigResumen, filas: Sequence[dict], destino: str | Path) -> Path:
    """Genera el Excel de resumen del hallazgo y devuelve la ruta escrita."""
    destino = Path(destino)
    destino.parent.mkdir(parents=True, exist_ok=True)

    libro = xlsxwriter.Workbook(str(destino), {"default_date_format": "dd/mm/yyyy"})
    try:
        fmt = _Formatos(libro)
        if config.campo_grupo:
            detalles = _hoja_por_grupo(libro, fmt, config, filas)
        else:
            detalles = _hoja_por_escenario(libro, fmt, config, filas)

        for escenario, alcance in detalles:
            _hoja_detalle(libro, fmt, config, escenario, alcance)
    finally:
        libro.close()

    return destino
