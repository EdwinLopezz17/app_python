"""
Verificador de entorno y contratos.

    python -m app.doctor

Comprueba, sin abrir ventana:
  * que las dependencias estén instaladas,
  * que DATA_PATH exista y sea escribible,
  * que las etiquetas de `app/catalog/display.py` sigan alineadas con los
    dataclasses de `models/reports/` (si el backend agrega una columna a un
    reporte, esto lo detecta),
  * que todo `file_name` del catálogo exista en `models.file_names.FileName`,
  * el estado de carga de cada hallazgo.

Ejecutarlo es lo primero que conviene hacer cuando algo no funciona en una
máquina nueva.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

OK, MAL, AVISO = "  [OK]   ", "  [FALLA]", "  [AVISO]"


def _dependencias() -> bool:
    print("Dependencias")
    todo_bien = True
    for modulo, etiqueta in [
        ("PySide6", "PySide6"), ("pyarrow", "pyarrow"), ("pandas", "pandas"),
        ("platformdirs", "platformdirs"), ("xlsxwriter", "XlsxWriter"),
        ("dotenv", "python-dotenv"),
    ]:
        try:
            mod = __import__(modulo)
            version = getattr(mod, "__version__", "?")
            print(f"{OK} {etiqueta} {version}")
        except ImportError:
            print(f"{MAL} {etiqueta} no instalado")
            todo_bien = False
    return todo_bien


def _rutas() -> bool:
    from app import config

    print("\nRutas")
    try:
        datos = config.data_path()
    except RuntimeError as exc:
        print(f"{MAL} {exc}")
        return False

    print(f"{OK} DATA_PATH  = {datos}")
    if not datos.exists():
        print(f"{AVISO} la carpeta no existe todavía; se creará al iniciar")
    elif not datos.is_dir():
        print(f"{MAL} DATA_PATH no es una carpeta")
        return False

    cache = config.cache_dir()
    print(f"{OK} CACHE_PATH = {cache}")
    if "OneDrive" in str(cache):
        print(f"{AVISO} la caché está dentro de OneDrive; conviene moverla "
              f"fuera para evitar sincronización de archivos binarios grandes")
    return True


def _contratos() -> bool:
    from models.file_names import FileName

    from app.catalog import display, fuentes, hallazgos

    print("\nContrato con models/")
    todo_bien = True

    validos = {f.value for f in FileName}
    for fuente in fuentes.FUENTES.values():
        for slot in fuente.slots:
            if slot.key not in validos:
                print(f"{MAL} '{slot.key}' ({fuente.label}) no existe en FileName")
                todo_bien = False
    if todo_bien:
        print(f"{OK} {len(fuentes.FUENTES)} fuentes, todos los file_name existen en FileName")

    for modelo, resultado in display.check_modelos().items():
        if resultado["faltan"] or resultado["sobran"]:
            todo_bien = False
            if resultado["faltan"]:
                print(f"{MAL} {modelo}: sin etiqueta -> {resultado['faltan']}")
            if resultado["sobran"]:
                print(f"{MAL} {modelo}: etiqueta sobrante -> {resultado['sobran']}")
        else:
            print(f"{OK} {modelo}: etiquetas alineadas con models/reports/")

    for hallazgo in hallazgos.HALLAZGOS:
        for fid in hallazgo.fuente_ids:
            if fid not in fuentes.FUENTES:
                print(f"{MAL} hallazgo '{hallazgo.id}' referencia fuente inexistente '{fid}'")
                todo_bien = False

    return todo_bien


def _estado() -> None:
    from app.cache import store
    from app.catalog import hallazgos
    from app.storage.files import estado_slot

    print("\nEstado de carga")
    for hallazgo in hallazgos.HALLAZGOS:
        slots = [s for f in hallazgo.fuentes for s in f.slots]
        cargados = sum(1 for s in slots if estado_slot(s).existe)
        cache = store.estado(hallazgo).value
        marca = OK if cargados == len(slots) else AVISO
        print(f"{marca} {hallazgo.label:24s} {cargados:2d}/{len(slots):2d} archivos "
              f"· caché: {cache}")


def main() -> int:
    print("=" * 66)
    print("  Verificación de entorno · Certificación de Accesos")
    print("=" * 66 + "\n")

    bien = _dependencias()
    if not bien:
        print("\nFaltan dependencias. Instala con:")
        print("  pip install -r requirements.txt")
        return 1

    bien &= _rutas()
    if bien:
        bien &= _contratos()
        _estado()

    print("\n" + "=" * 66)
    print("  Todo correcto." if bien else "  Hay problemas que resolver (ver [FALLA] arriba).")
    print("=" * 66)
    return 0 if bien else 1


if __name__ == "__main__":
    raise SystemExit(main())
