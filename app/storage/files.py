from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

import pandas as pd

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
    filas, columnas = _dimensiones(path)

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


def _leer_csv(path: Path, columnas: list[str] | int | None = None) -> pd.DataFrame:
    """Lectura estándar del formato que escribe la app: `;`, UTF-8, todo texto."""
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


def _dimensiones(path: Path) -> tuple[int, int]:
    """Filas y columnas sin cargar el archivo completo en memoria."""
    try:
        cabecera = pd.read_csv(
            path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING,
            dtype=str, nrows=0,
        )
    except Exception:
        return 0, 0

    columnas = len(cabecera.columns)
    if not columnas:
        return 0, 0

    filas = 0
    try:
        lector = pd.read_csv(
            path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING,
            dtype=str, keep_default_na=False, na_filter=False,
            usecols=[0], chunksize=200_000,
        )
        for bloque in lector:
            filas += len(bloque)
    except Exception:
        filas = 0

    return filas, columnas


def archivos_origen(slot: Slot, path: Path | None = None) -> list[str]:
    if not slot.origin_file:
        return []

    path = path or config.destino(slot.key, slot.subfolder)
    if not path.exists():
        return []

    vistos: dict[str, None] = {}
    try:
        lector = pd.read_csv(
            path, sep=config.CSV_SEP, encoding=config.CSV_ENCODING,
            dtype=str, keep_default_na=False, na_filter=False,
            usecols=[COLUMNA_ORIGEN], chunksize=200_000,
        )
        for bloque in lector:
            for valor in bloque[COLUMNA_ORIGEN]:
                nombre = str(valor or "").strip()
                if nombre:
                    vistos.setdefault(nombre, None)
    except Exception:
        return []

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
    candidatos = [carpeta / f"{path.name}{config.EXTENSION_DATOS}"]
    # Restos de la etapa Parquet: usuarios_x.parquet y usuarios_x.csv.parquet
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
