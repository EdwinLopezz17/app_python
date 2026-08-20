"""
diagnostico_resumen.py — Diagnóstico del conteo del Resumen (AD y demás).

NO modifica nada. Solo lee el Excel de detalle que cargas en la vista Resumen
y te dice POR QUÉ un escenario está saliendo en 0.

USO
---
Colócalo en la RAÍZ del proyecto (al lado de app/, logic/, models/) y corre:

    python diagnostico_resumen.py "C:\\ruta\\hallazgo-active-directory-....xlsx"

Opcional, si el archivo no es de AD:

    python diagnostico_resumen.py archivo.xlsx --hallazgo aplicaciones
    python diagnostico_resumen.py archivo.xlsx --hallazgo bd-vida

Hallazgos válidos: los de app/catalog/resumenes.py (active-directory,
aplicaciones, bd-vida, bd-generales, ...).

QUÉ REVISA
----------
1. Cabeceras del archivo que NO mapean a ningún campo del modelo.
2. Campos que los escenarios necesitan y que NO llegaron a las filas
   (esta es la causa típica del "cuenta 0 en silencio").
3. Para cada flag: cuántas filas traen valor y cuántas cuentan como marca
   según engine.cumple_marca() — que es exactamente lo que usa el resumen.
4. El conteo final por escenario, igual que lo calcula la app.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.catalog import hallazgo_columns as cols  # noqa: E402
from app.catalog import resumenes  # noqa: E402
from app.ingest.normalize import norm_header  # noqa: E402
from app.ingest.readers import ErrorDeLectura, leer_como_texto  # noqa: E402
from app.resumen import engine  # noqa: E402
from app.resumen.importer import _mapa_cabeceras  # noqa: E402


LINEA = "=" * 78
SUB = "-" * 78


def _campos_usados(config) -> dict[str, list[str]]:
    """campo -> escenarios que lo usan (flags y campos de filtro)."""
    usados: dict[str, list[str]] = {}
    for esc in config.escenarios:
        if esc.flag:
            usados.setdefault(esc.flag, []).append(esc.code)
        for filtro in esc.filtros:
            usados.setdefault(filtro.campo, []).append(esc.code)
    return usados


def diagnosticar(ruta: Path, hallazgo_id: str) -> int:
    config = resumenes.CONFIGS.get(hallazgo_id)
    if config is None:
        print(f"[ERROR] Hallazgo desconocido: {hallazgo_id!r}")
        print("Disponibles:", ", ".join(sorted(resumenes.CONFIGS)))
        return 2

    modelo = config.modelo

    print(LINEA)
    print(f"ARCHIVO  : {ruta}")
    print(f"HALLAZGO : {hallazgo_id}   MODELO: {modelo}")
    print(LINEA)

    try:
        df = leer_como_texto(ruta)
    except ErrorDeLectura as exc:
        print(f"[ERROR] No se pudo leer: {exc}")
        return 2

    if df.empty:
        print("[ERROR] El archivo no tiene filas de datos.")
        return 2

    mapa = _mapa_cabeceras(modelo)
    cabeceras = [str(c) for c in df.columns]

    # ---- 1. Cabeceras que no mapean --------------------------------------
    print("\n1) CABECERAS DEL ARCHIVO QUE NO MAPEAN A NINGÚN CAMPO")
    print(SUB)
    huerfanas = [h for h in cabeceras if norm_header(h) not in mapa]
    if huerfanas:
        for h in huerfanas:
            print(f"   [ignorada] {h!r}")
        print(f"\n   -> {len(huerfanas)} de {len(cabeceras)} columnas se están perdiendo.")
    else:
        print("   OK: todas las cabeceras mapearon.")

    # ---- 2. Campos que los escenarios necesitan ---------------------------
    columnas_mapeadas = {mapa[norm_header(h)] for h in cabeceras if norm_header(h) in mapa}
    usados = _campos_usados(config)
    etiquetas = cols.etiquetas(modelo)

    print("\n2) CAMPOS QUE LOS ESCENARIOS NECESITAN")
    print(SUB)
    faltantes: list[str] = []
    for campo, codes in usados.items():
        if campo in columnas_mapeadas:
            print(f"   OK      {campo:<28} (esperada: {etiquetas.get(campo, campo)!r})")
        else:
            faltantes.append(campo)
            print(f"   FALTA   {campo:<28} -> {', '.join(codes)}  "
                  f"[la app espera la cabecera {etiquetas.get(campo, campo)!r}]")

    if faltantes:
        print("\n   >>> ESTOS ESCENARIOS VAN A CONTAR 0 SÍ O SÍ.")
        print("   >>> El campo no existe en las filas; fila.get(campo) es None")
        print("   >>> y cumple_marca(None) es False. Falla en silencio.")
        print("   >>> Compara con la lista de 'cabeceras ignoradas' de arriba:")
        print("   >>> casi siempre es la misma columna con otro nombre.")

    # ---- 3. Valores reales de cada flag -----------------------------------
    columnas_rel = {c: mapa.get(norm_header(c), str(c)) for c in df.columns}
    filas = [{columnas_rel[c]: v for c, v in reg.items()}
             for reg in df.to_dict("records")]

    print(f"\n3) VALORES REALES POR CAMPO ({len(filas)} filas)")
    print(SUB)
    for campo in usados:
        if campo not in columnas_mapeadas:
            continue
        valores = [f.get(campo) for f in filas]
        conteo = Counter(str(v).strip() for v in valores)
        no_vacios = sum(1 for v in valores if str(v).strip() != "")
        como_marca = sum(1 for v in valores if engine.cumple_marca(v, "marca"))
        como_pos = sum(1 for v in valores if engine.cumple_marca(v, "positivo"))
        print(f"   {campo}")
        print(f"      con valor: {no_vacios:<6} modo 'marca': {como_marca:<6} "
              f"modo 'positivo': {como_pos}")
        top = conteo.most_common(5)
        muestra = ", ".join(f"{v!r}x{n}" for v, n in top)
        print(f"      valores  : {muestra}")
        if no_vacios and como_marca == 0:
            print("      >>> Hay valores pero NINGUNO cuenta como marca.")
            print("      >>> Revisa que sean 'X'/'SI'/'TRUE'/'1'.")

    # ---- 4. Conteo final --------------------------------------------------
    print("\n4) CONTEO POR ESCENARIO (idéntico al de la app)")
    print(SUB)
    resumen = engine.por_escenario(filas, config.escenarios)
    print(f"   {'CODE':<18}{'TOTAL':>8}{'GDH':>8}{'ACCESOS':>10}   TÍTULO")
    for f in resumen.filas:
        marca = "  <-- EN CERO" if f.total == 0 else ""
        print(f"   {f.code:<18}{f.total:>8}{f.gdh:>8}{f.accesos:>10}   "
              f"{f.title[:40]}{marca}")
    print(f"\n   filas leídas   : {resumen.total_registros}")
    print(f"   total hallazgos: {resumen.total_hallazgos}")

    # ---- 5. Veredicto -----------------------------------------------------
    print("\n5) VEREDICTO")
    print(SUB)
    ceros = [f.code for f in resumen.filas if f.total == 0]
    if not ceros:
        print("   Todos los escenarios cuentan. El resumen está bien.")
    elif faltantes:
        print("   CAUSA: mapeo de cabeceras (punto 2).")
        print("   El archivo trae las columnas con otro nombre del que espera")
        print("   la app. Solución: agregar alias en")
        print("   app/catalog/hallazgo_columns.ALIAS_IMPORTACION para el modelo")
        print(f"   {modelo!r}, o reexportar el detalle desde esta misma app.")
    else:
        print("   CAUSA: los flags SÍ llegan pero vienen vacíos en el origen.")
        print("   El conteo del resumen está correcto; el problema está en la")
        print("   generación del hallazgo (logic/), no en app/.")
        print(f"   Escenarios en cero: {', '.join(ceros)}")

    print(LINEA)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnóstico del resumen de hallazgos.")
    parser.add_argument("archivo", help="Excel/CSV de detalle que cargas en Resumen")
    parser.add_argument("--hallazgo", default="active-directory",
                        help="ID del hallazgo (default: active-directory)")
    args = parser.parse_args()

    ruta = Path(args.archivo)
    if not ruta.exists():
        print(f"[ERROR] No existe: {ruta}")
        return 2
    return diagnosticar(ruta, args.hallazgo)


if __name__ == "__main__":
    raise SystemExit(main())
