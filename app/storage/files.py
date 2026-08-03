from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

from app import config
from app.catalog.fuentes import Fuente, Slot
from app.ingest.merge import COLUMNA_ORIGEN


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


def estado_slot(slot: Slot) -> EstadoSlot:
    path = config.destino(slot.key, slot.subfolder)
    if not path.exists():
        return EstadoSlot(slot=slot, existe=False, path=path)

    stat = path.stat()
    filas = columnas = 0
    try:
        meta = pq.read_metadata(path)
        filas = meta.num_rows
        columnas = meta.num_columns
    except Exception:
        pass

    return EstadoSlot(
        slot=slot,
        existe=True,
        path=path,
        filas=filas,
        columnas=columnas,
        modificado=datetime.fromtimestamp(stat.st_mtime),
        tamano_bytes=stat.st_size,
        archivos=archivos_origen(slot, path),
    )


def archivos_origen(slot: Slot, path: Path | None = None) -> list[str]:
    """Nombres de los archivos que se consolidaron en el parquet del slot.

    Solo aplica a los slots con `origin_file=True` (DB Vida y DB Generales),
    que guardan la columna ORIGIN_FILE al unificar varios archivos. Se lee
    únicamente esa columna, así que el costo es mínimo aunque el parquet sea
    grande.
    """
    if not slot.origin_file:
        return []

    path = path or config.destino(slot.key, slot.subfolder)
    if not path.exists():
        return []

    try:
        tabla = pq.read_table(path, columns=[COLUMNA_ORIGEN])
    except Exception:
        return []

    vistos: dict[str, None] = {}
    for valor in tabla.column(COLUMNA_ORIGEN).to_pylist():
        nombre = str(valor or "").strip()
        if nombre:
            vistos.setdefault(nombre, None)
    return list(vistos)


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

    return borrado


def _residuos_de(path: Path) -> list[Path]:
    carpeta = path.parent
    if not carpeta.exists():
        return []
    doble = carpeta / f"{path.name}{config.EXTENSION_DATOS}"
    encontrados = [doble] if doble.exists() else []
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
    import pandas as pd

    path = config.destino(slot.key, slot.subfolder)
    if not path.exists():
        raise FileNotFoundError(f"No hay datos cargados para {slot.display_label}")
    return pd.read_parquet(path, engine="pyarrow", columns=columnas)
