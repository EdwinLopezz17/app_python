from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from app import config
from app.catalog.hallazgos import Hallazgo
from app.storage.files import EstadoSlot, estado_slot


@dataclass
class Huella:
    valor: str
    faltantes: list[str]
    opcionales_faltantes: list[str] = field(default_factory=list)

    @property
    def completa(self) -> bool:
        return not self.faltantes


def estados_de(hallazgo: Hallazgo) -> list[EstadoSlot]:
    return [estado_slot(slot) for f in hallazgo.fuentes for slot in f.slots]


def calcular(hallazgo: Hallazgo) -> Huella:
    h = hashlib.sha256()
    faltantes: list[str] = []
    opcionales_faltantes: list[str] = []

    obligatorias = {s.key for s in hallazgo.slots_requeridos}

    vistos: set[str] = set()
    slots = [s for f in hallazgo.fuentes for s in f.slots]
    for slot in sorted(slots, key=lambda s: s.key):
        if slot.key in vistos:
            continue
        vistos.add(slot.key)

        path = config.destino(slot.key, slot.subfolder)
        try:
            stat = path.stat()
        except OSError:
            if slot.key in obligatorias:
                faltantes.append(slot.key)
            else:
                opcionales_faltantes.append(slot.key)
            h.update(f"{slot.key}|AUSENTE".encode())
            continue

        h.update(f"{slot.key}|{stat.st_size}|{int(stat.st_mtime)}".encode())

    return Huella(
        valor=h.hexdigest(),
        faltantes=faltantes,
        opcionales_faltantes=opcionales_faltantes,
    )
