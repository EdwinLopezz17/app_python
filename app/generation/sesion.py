from __future__ import annotations

import hashlib
import importlib
import inspect
import threading
from contextlib import contextmanager
from pathlib import Path

import pandas as pd

from app import config
from app.generation.compat import puente_csv

PAQUETES = ("logic",)

SUFIJOS = ("Service", "Services")

# ---------------------------------------------------------------------------
# Sesión caliente persistente
#
# Antes, cada llamada a sesion_generacion() creaba desde cero la memoización
# de servicios y el cache de lecturas, y los descartaba al salir: cada clic en
# «Generar» reconstruía TODOS los servicios de logic/ (MR, GDH, AD, Entra,
# las ~20 aplicaciones, etc.), lo que costaba varios minutos por hallazgo.
#
# Ahora ambos caches viven a nivel de módulo y sobreviven entre generaciones,
# igual que los servicios calientes del backend FastAPI. Se invalidan solos
# cuando cambia cualquier archivo fuente en DATA_PATH (huella por
# nombre|tamaño|mtime, el mismo criterio que app/cache/fingerprint.py).
# ---------------------------------------------------------------------------

_LOCK = threading.RLock()

_CALIENTE: dict = {
    "huella": None,
    "instancias": {},   # (clase, args) -> __dict__ del servicio ya cargado
    "lecturas": {},     # firma de archivo -> DataFrame leído
}

_PRECALENTANDO = False


def _huella_datos() -> str:
    """Huella de todos los CSV bajo DATA_PATH (recursivo, incluye subfolders)."""
    h = hashlib.sha256()
    try:
        carpeta = config.data_path()
    except RuntimeError:
        return ""

    try:
        archivos = sorted(carpeta.rglob(f"*{config.EXTENSION_DATOS}"))
    except OSError:
        return ""

    for archivo in archivos:
        try:
            stat = archivo.stat()
        except OSError:
            continue
        h.update(
            f"{archivo.relative_to(carpeta)}|{stat.st_size}|{int(stat.st_mtime)}"
            .encode("utf-8", errors="replace")
        )
    return h.hexdigest()


def _invalidar_si_cambio() -> None:
    """Si algún archivo fuente cambió, descarta la sesión caliente completa."""
    actual = _huella_datos()
    if _CALIENTE["huella"] != actual:
        _CALIENTE["instancias"].clear()
        _CALIENTE["lecturas"].clear()
        _CALIENTE["huella"] = actual


def _modulos_de_servicio() -> list[str]:
    nombres: list[str] = []
    for nombre_paquete in PAQUETES:
        try:
            paquete = importlib.import_module(nombre_paquete)
        except Exception:
            continue
        for raiz in paquete.__path__:
            base = Path(raiz)
            for archivo in sorted(base.rglob("*.py")):
                if archivo.name == "__init__.py":
                    continue
                relativo = archivo.relative_to(base).with_suffix("")
                partes = relativo.parts
                if "services" not in partes and not archivo.stem.endswith(
                    ("_service", "_services")
                ):
                    continue
                nombres.append(".".join((nombre_paquete, *partes)))
    return nombres


def _clases_de_servicio() -> list[type]:
    encontradas: dict[str, type] = {}
    for nombre_modulo in _modulos_de_servicio():
        try:
            modulo = importlib.import_module(nombre_modulo)
        except Exception:
            continue
        for nombre, obj in vars(modulo).items():
            if not inspect.isclass(obj):
                continue
            if obj.__module__ != modulo.__name__:
                continue
            if not nombre.endswith(SUFIJOS):
                continue
            encontradas.setdefault(f"{obj.__module__}.{nombre}", obj)
    return list(encontradas.values())


def _clave(args, kwargs) -> tuple:
    try:
        return (args, tuple(sorted(kwargs.items())))
    except TypeError:
        return None


@contextmanager
def _servicios_memoizados(instancias: dict | None = None):
    if instancias is None:
        instancias = {}
    originales: list[tuple[type, object]] = []

    for cls in _clases_de_servicio():
        init_original = cls.__init__
        originales.append((cls, init_original))

        def envolver(cls=cls, init_original=init_original):
            def __init__(self, *args, **kwargs):
                clave = _clave(args, kwargs)
                if clave is None:
                    init_original(self, *args, **kwargs)
                    return
                guardado = instancias.get((cls, clave))
                if guardado is not None:
                    self.__dict__.update(guardado)
                    return
                init_original(self, *args, **kwargs)
                instancias[(cls, clave)] = dict(self.__dict__)
            return __init__

        cls.__init__ = envolver()

    try:
        yield instancias
    finally:
        for cls, init_original in originales:
            cls.__init__ = init_original


@contextmanager
def _lecturas_cacheadas(cache: dict | None = None):
    if cache is None:
        cache = {}
    read_csv_original = pd.read_csv

    def firma(ruta, kwargs):
        try:
            path = Path(ruta)
            stat = path.stat()
        except (TypeError, OSError, ValueError):
            return None
        if kwargs.get("chunksize") or kwargs.get("iterator") or kwargs.get("nrows"):
            return None
        usecols = kwargs.get("usecols")
        if usecols is not None:
            try:
                usecols = tuple(usecols)
            except TypeError:
                return None
        return (
            str(path), stat.st_size, int(stat.st_mtime),
            kwargs.get("sep"), kwargs.get("encoding"), kwargs.get("dtype") is str,
            usecols,
        )

    def read_csv_cacheado(ruta, *args, **kwargs):
        if args:
            return read_csv_original(ruta, *args, **kwargs)
        clave = firma(ruta, kwargs)
        if clave is None:
            return read_csv_original(ruta, **kwargs)
        guardado = cache.get(clave)
        if guardado is None:
            guardado = read_csv_original(ruta, **kwargs)
            cache[clave] = guardado
        return guardado.copy()

    pd.read_csv = read_csv_cacheado
    try:
        yield cache
    finally:
        pd.read_csv = read_csv_original


@contextmanager
def sesion_generacion():
    with _LOCK:
        _invalidar_si_cambio()
        with puente_csv():
            with _lecturas_cacheadas(_CALIENTE["lecturas"]):
                with _servicios_memoizados(_CALIENTE["instancias"]):
                    yield


# ---------------------------------------------------------------------------
# Precalentamiento en segundo plano
#
# Carga los servicios compartidos (los que usan casi todos los hallazgos)
# apenas la vista está lista para generar, de modo que el primer clic en
# «Generar» encuentre la mayor parte del trabajo ya hecho. Los servicios de
# aplicaciones quedan calientes tras la primera generación que los use.
# ---------------------------------------------------------------------------

_SERVICIOS_COMPARTIDOS = (
    ("logic.share.services.dni_vs_user_service", "DNIUserService"),
    ("logic.share.services.gdh_service", "GDHUserService"),
    ("logic.share.services.ad_service", "ADService"),
    ("logic.share.services.entraid_service", "EntraUserService"),
    ("logic.share.services.tickets_report", "TicketInfoService"),
    ("logic.share.services.mr_service", "MatrizRolesService"),
)


def solicitar_precalentamiento() -> bool:
    """Devuelve True (y reserva el turno) solo si hace falta precalentar.

    Se llama desde el hilo de UI, así que no toma _LOCK: lee estado bajo el
    GIL. Una carrera en el peor caso lanza un precalentamiento redundante,
    que la memoización convierte en no-op.
    """
    global _PRECALENTANDO
    if _PRECALENTANDO:
        return False
    if _CALIENTE["instancias"] and _CALIENTE["huella"] == _huella_datos():
        return False
    _PRECALENTANDO = True
    return True


def precalentar() -> int:
    """Instancia los servicios compartidos dentro de la sesión caliente.

    Pensado para correr en una Tarea de fondo. Devuelve cuántos servicios
    quedaron cargados. Nunca propaga excepciones: si una fuente falta, el
    servicio correspondiente simplemente no se calienta y la generación
    real reportará el problema como siempre.
    """
    global _PRECALENTANDO
    try:
        with sesion_generacion():
            cargados = 0
            for nombre_modulo, nombre_clase in _SERVICIOS_COMPARTIDOS:
                try:
                    modulo = importlib.import_module(nombre_modulo)
                    getattr(modulo, nombre_clase)()
                    cargados += 1
                except Exception:
                    continue
            return cargados
    finally:
        _PRECALENTANDO = False
