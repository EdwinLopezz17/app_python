from __future__ import annotations

import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from app import config
from app.catalog.fuentes import Fuente, Slot
from app.ingest.merge import COLUMNA_ORIGEN

VERSION_SIDECAR = 1

_MEMORIA: dict[Path, tuple[int, int, "Medida"]] = {}


@dataclass
class Medida:
    filas: int = 0
    columnas: int = 0
    archivos: list[str] = field(default_factory=list)


@dataclass
class EstadoSlot:
    slot: Slot
    existe: bool
    path: Path
    filas: int = 0
    columnas: int = 0
    modificado: datetime | None = None
    tamano_bytes: int = 0
    archivos: list[str] = field(default_factory=list)

    @property
    def total_archivos(self) -> int:
        return len(self.archivos)

    @property
    def modificado_texto(self) -> str:
        return self.modificado.strftime("%d/%m/%Y %H:%M") if self.modificado else "—"

    @property
    def tamano_texto(self) -> str:
        if not self.tamano_bytes:
            return "—"
        unidades = ["B", "KB", "MB", "GB"]
        valor = float(self.tamano_bytes)
        for unidad in unidades:
            if valor < 1024 or unidad == unidades[-1]:
                return f"{valor:.0f} {unidad}" if unidad == "B" else f"{valor:.1f} {unidad}"
            valor /= 1024
        return f"{valor:.1f} GB"


def _ruta_sidecar(path: Path) -> Path:
    carpeta = config.cache_dir() / "slots"
    carpeta.mkdir(parents=True, exist_ok=True)
    firma = str(path).replace("\\", "/")
    seguro = "".join(c if c.isalnum() or c in "-_." else "_" for c in firma)[-120:]
    return carpeta / f"{seguro}.json"


def _leer_sidecar(path: Path, mtime: int, tamano: int) -> Medida | None:
    destino = _ruta_sidecar(path)
    if not destino.exists():
        return None
    try:
        datos = json.loads(destino.read_text(encoding="utf-8"))
    except Exception:
        return None
    if datos.get("version") != VERSION_SIDECAR:
        return None
    if int(datos.get("mtime", -1)) != mtime or int(datos.get("tamano", -1)) != tamano:
        return None
    return Medida(
        filas=int(datos.get("filas", 0)),
        columnas=int(datos.get("columnas", 0)),
        archivos=list(datos.get("archivos", [])),
    )


def _escribir_sidecar(path: Path, mtime: int, tamano: int, medida: Medida) -> None:
    try:
        _ruta_sidecar(path).write_text(
            json.dumps(
                {
                    "version": VERSION_SIDECAR,
                    "origen": str(path),
                    "mtime": mtime,
                    "tamano": tamano,
                    "filas": medida.filas,
                    "columnas": medida.columnas,
                    "archivos": medida.archivos,
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
    except Exception:
        pass


def _borrar_sidecar(path: Path) -> None:
    try:
        _ruta_sidecar(path).unlink(missing_ok=True)
    except Exception:
        pass


def _cabecera(path: Path) -> list[str]:
    try:
        vacia = pd.read_csv(
            path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING,
            dtype=str, nrows=0,
        )
    except Exception:
        return []
    return [str(c) for c in vacia.columns]


def _medir(path: Path, con_origen: bool) -> Medida:
    columnas = _cabecera(path)
    if not columnas:
        return Medida()

    usar_origen = con_origen and COLUMNA_ORIGEN in columnas
    usar = [COLUMNA_ORIGEN] if usar_origen else [0]
    filas = 0
    vistos: dict[str, None] = {}
    try:
        lector = pd.read_csv(
            path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING,
            dtype=str, keep_default_na=False, na_filter=False,
            usecols=usar, chunksize=200_000,
        )
        for bloque in lector:
            filas += len(bloque)
            if usar_origen:
                for valor in bloque[COLUMNA_ORIGEN].unique():
                    nombre = str(valor or "").strip()
                    if nombre:
                        vistos.setdefault(nombre, None)
    except Exception:
        return Medida(columnas=len(columnas))

    return Medida(filas=filas, columnas=len(columnas), archivos=list(vistos))


def medida_de(path: Path, con_origen: bool) -> Medida:
    try:
        stat = path.stat()
    except OSError:
        return Medida()

    mtime = int(stat.st_mtime)
    tamano = stat.st_size

    guardada = _MEMORIA.get(path)
    if guardada and guardada[0] == mtime and guardada[1] == tamano:
        return guardada[2]

    desde_disco = _leer_sidecar(path, mtime, tamano)
    if desde_disco is not None:
        _MEMORIA[path] = (mtime, tamano, desde_disco)
        return desde_disco

    medida = _medir(path, con_origen)
    _MEMORIA[path] = (mtime, tamano, medida)
    _escribir_sidecar(path, mtime, tamano, medida)
    return medida


def registrar_medida(path: Path, filas: int, columnas: int, archivos: list[str]) -> None:
    try:
        stat = path.stat()
    except OSError:
        return
    mtime = int(stat.st_mtime)
    medida = Medida(filas=filas, columnas=columnas, archivos=list(archivos))
    _MEMORIA[path] = (mtime, stat.st_size, medida)
    _escribir_sidecar(path, mtime, stat.st_size, medida)


def olvidar(path: Path) -> None:
    _MEMORIA.pop(path, None)
    _borrar_sidecar(path)


def limpiar_memoria() -> None:
    _MEMORIA.clear()


def estado_slot(slot: Slot) -> EstadoSlot:
    path = config.destino(slot.key, slot.subfolder)
    try:
        stat = path.stat()
    except OSError:
        return EstadoSlot(slot=slot, existe=False, path=path)

    medida = medida_de(path, slot.origin_file)

    return EstadoSlot(
        slot=slot,
        existe=True,
        path=path,
        filas=medida.filas,
        columnas=medida.columnas,
        modificado=datetime.fromtimestamp(stat.st_mtime),
        tamano_bytes=stat.st_size,
        archivos=medida.archivos,
    )


def _leer_csv(path: Path, columnas: list[str] | int | None = None) -> pd.DataFrame:
    return pd.read_csv(
        path,
        sep=config.CSV_SEP,
        encoding=config.CSV_ENCODING,
        dtype=str,
        keep_default_na=False,
        na_filter=False,
        usecols=columnas,
        low_memory=False,
    )


def archivos_origen(slot: Slot, path: Path | None = None) -> list[str]:
    if not slot.origin_file:
        return []
    path = path or config.destino(slot.key, slot.subfolder)
    if not path.exists():
        return []
    return medida_de(path, True).archivos


def estado_fuente(fuente: Fuente) -> list[EstadoSlot]:
    return [estado_slot(s) for s in fuente.slots]


def fuente_completa(fuente: Fuente) -> bool:
    return all(e.existe for e in estado_fuente(fuente))


def eliminar_slot(slot: Slot) -> bool:
    path = config.destino(slot.key, slot.subfolder)
    borrado = False

    if path.exists():
        path.unlink()
        borrado = True

    for residuo in _residuos_de(path):
        residuo.unlink(missing_ok=True)
        borrado = True

    olvidar(path)
    return borrado


def _residuos_de(path: Path) -> list[Path]:
    carpeta = path.parent
    if not carpeta.exists():
        return []
    candidatos = [carpeta / f"{path.name}{config.EXTENSION_DATOS}"]
    for ext in config.EXTENSIONES_LEGADAS:
        candidatos.append(path.with_suffix(ext))
        candidatos.append(carpeta / f"{path.name}{ext}")

    encontrados = [c for c in candidatos if c != path and c.exists()]
    encontrados += sorted(carpeta.glob(f"{path.stem}-*.csv.tmp"))
    encontrados += sorted(carpeta.glob(f"{path.stem}-*.parquet.tmp"))
    return encontrados


def eliminar_fuente(fuente: Fuente) -> int:
    return sum(1 for s in fuente.slots if eliminar_slot(s))


def eliminar_slots(slots: Iterable[Slot]) -> int:
    vistos: set[Path] = set()
    eliminados = 0
    for slot in slots:
        path = config.destino(slot.key, slot.subfolder)
        if path in vistos:
            continue
        vistos.add(path)
        if eliminar_slot(slot):
            eliminados += 1
    return eliminados


def leer_datos(slot: Slot, columnas: list[str] | None = None):
    path = config.destino(slot.key, slot.subfolder)
    if not path.exists():
        raise FileNotFoundError(f"No hay datos cargados para {slot.display_label}")
    return _leer_csv(path, columnas)
