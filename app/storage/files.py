from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

from app import config
from app.catalog.fuentes import Fuente, Slot

# ---------------------------------------------------------------------------
# Verificación de archivos cargados.
#
# La verificación NO lee los archivos: comprobar que el CSV existe en disco
# (path.stat()) es suficiente para decir "cargado". Las filas/columnas que se
# muestran en las cards vienen del propio proceso de carga: el writer ya
# conoce esos números al escribir el CSV y los registra aquí en memoria
# (registrar_medida). Si la app se reinicia, el archivo sigue mostrándose
# como cargado ("En disco") aunque ya no se conozcan sus filas.
# ---------------------------------------------------------------------------

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


def registrar_medida(path: Path, filas: int, columnas: int, archivos: list[str]) -> None:
    """El writer llama esto al terminar de escribir el CSV consolidado."""
    try:
        stat = path.stat()
    except OSError:
        return
    medida = Medida(filas=filas, columnas=columnas, archivos=list(archivos))
    _MEMORIA[path] = (int(stat.st_mtime), stat.st_size, medida)


def olvidar(path: Path) -> None:
    _MEMORIA.pop(path, None)


def _medida_conocida(path: Path, mtime: int, tamano: int) -> Medida:
    guardada = _MEMORIA.get(path)
    if guardada and guardada[0] == mtime and guardada[1] == tamano:
        return guardada[2]
    return Medida()


def estado_slot(slot: Slot) -> EstadoSlot:
    path = config.destino(slot.key, slot.subfolder)
    try:
        stat = path.stat()
    except OSError:
        return EstadoSlot(slot=slot, existe=False, path=path)

    medida = _medida_conocida(path, int(stat.st_mtime), stat.st_size)

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


def _leer_csv(path: Path, columnas: list[str] | None = None) -> pd.DataFrame:
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
