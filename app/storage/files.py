"""
Estado de los archivos cargados.

En la versión Next esto vivía en localStorage (`upload-status.ts`) y en
IndexedDB, y podía desincronizarse de la realidad: la UI decía "cargado" y el
backend no tenía el archivo, o al revés.

Aquí NO hay estado que mantener. La única verdad es el disco: si el .parquet
existe, la fuente está cargada. Punto. Esto elimina por construcción toda una
familia de bugs, y explica por qué una fuente cargada desde el hallazgo de
Aplicaciones aparece cargada también en AD, BD y Perfiles: es el mismo archivo.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import pyarrow.parquet as pq

from app import config
from app.catalog.fuentes import Fuente, Slot


@dataclass
class EstadoSlot:
    slot: Slot
    existe: bool
    path: Path
    filas: int = 0
    columnas: int = 0
    modificado: datetime | None = None
    tamano_bytes: int = 0

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
    """
    Lee el estado de un slot sin cargar los datos.

    El conteo de filas sale de los METADATOS del Parquet, no de leer el archivo:
    es instantáneo incluso con 90.000 filas. Esa es una de las ventajas
    concretas de Parquet sobre CSV, donde habría que contar líneas.
    """
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
        # Archivo corrupto o a medio escribir: se reporta como existente pero vacío.
        pass

    return EstadoSlot(
        slot=slot,
        existe=True,
        path=path,
        filas=filas,
        columnas=columnas,
        modificado=datetime.fromtimestamp(stat.st_mtime),
        tamano_bytes=stat.st_size,
    )


def estado_fuente(fuente: Fuente) -> list[EstadoSlot]:
    return [estado_slot(s) for s in fuente.slots]


def fuente_completa(fuente: Fuente) -> bool:
    """True si TODOS los slots de la card tienen archivo (AD necesita PPS y Vida)."""
    return all(e.existe for e in estado_fuente(fuente))


def eliminar_slot(slot: Slot) -> bool:
    """
    Elimina el archivo de un slot. Devuelve True si había algo que eliminar.

    Además de la ruta canónica, barre dos residuos que pueden haber quedado de
    ejecuciones anteriores y que, si sobreviven, hacen que la card siga
    apareciendo cargada o que ocupen espacio para siempre:

      * `<nombre>.parquet.parquet`, del bug de doble extensión ya corregido en
        `config.destino`;
      * `<nombre>-XXXX.parquet.tmp`, de una escritura atómica interrumpida.
    """
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
    """Archivos huérfanos asociados al destino de un slot."""
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
    """
    Elimina un conjunto arbitrario de slots, sin repetir trabajo.

    La deduplicación por ruta NO es un detalle: una certificación completa
    referencia la misma fuente transversal (DNI, GDH, AD, Tickets) desde varios
    hallazgos. Sin deduplicar, el contador que se le muestra al usuario diría
    "12 archivos eliminados" cuando en disco solo había 7.
    """
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
    """Carga el Parquet de un slot para previsualizarlo."""
    import pandas as pd

    path = config.destino(slot.key, slot.subfolder)
    if not path.exists():
        raise FileNotFoundError(f"No hay datos cargados para {slot.display_label}")
    return pd.read_parquet(path, engine="pyarrow", columns=columnas)
