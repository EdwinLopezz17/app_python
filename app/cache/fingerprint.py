"""
Huella de las fuentes que alimentan un hallazgo.

Reemplaza la invalidación de SWR/IndexedDB de la versión Next, y es mejor:
en vez de un TTL o una revalidación manual, la caché sabe con certeza si sigue
siendo válida. Si alguien recargó GDH, el hallazgo de Aplicaciones que dependía
de GDH queda marcado como desactualizado automáticamente.

La huella combina, por cada archivo de origen: nombre, tamaño y fecha de
modificación. No se hashea el contenido a propósito: leer 200 MB solo para
decidir si hay que regenerar sería más caro que regenerar. Tamaño + mtime es
suficiente para detectar cualquier recarga hecha desde la propia aplicación,
que es el único camino por el que estos archivos cambian.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from app.catalog.hallazgos import Hallazgo
from app.storage.files import EstadoSlot, estado_slot


@dataclass
class Huella:
    valor: str
    faltantes: list[str]

    @property
    def completa(self) -> bool:
        return not self.faltantes


def estados_de(hallazgo: Hallazgo) -> list[EstadoSlot]:
    return [estado_slot(slot) for f in hallazgo.fuentes for slot in f.slots]


def calcular(hallazgo: Hallazgo) -> Huella:
    """Huella determinista de todas las fuentes requeridas por el hallazgo."""
    h = hashlib.sha256()
    faltantes: list[str] = []

    for estado in sorted(estados_de(hallazgo), key=lambda e: e.slot.key):
        if not estado.existe:
            faltantes.append(estado.slot.key)
            h.update(f"{estado.slot.key}|AUSENTE".encode())
            continue
        stat = estado.path.stat()
        h.update(f"{estado.slot.key}|{stat.st_size}|{int(stat.st_mtime)}".encode())

    return Huella(valor=h.hexdigest(), faltantes=faltantes)
