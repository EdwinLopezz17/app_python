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
