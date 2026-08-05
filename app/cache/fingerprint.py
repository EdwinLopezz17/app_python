from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

from app.catalog.hallazgos import Hallazgo
from app.storage.files import EstadoSlot, estado_slot


@dataclass
class Huella:
    valor: str
    #: Solo fuentes OBLIGATORIAS que faltan: son las que bloquean la generación.
    faltantes: list[str]
    #: Fuentes opcionales que faltan. No bloquean nada; se informan en la UI.
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

    # La huella sigue incluyendo TODAS las fuentes: si mañana se carga una
    # aplicación opcional que hoy falta, la caché queda desactualizada y se
    # ofrece regenerar. Lo que cambia es solo qué se considera bloqueante.
    for estado in sorted(estados_de(hallazgo), key=lambda e: e.slot.key):
        if not estado.existe:
            if estado.slot.key in obligatorias:
                faltantes.append(estado.slot.key)
            else:
                opcionales_faltantes.append(estado.slot.key)
            h.update(f"{estado.slot.key}|AUSENTE".encode())
            continue
        stat = estado.path.stat()
        h.update(f"{estado.slot.key}|{stat.st_size}|{int(stat.st_mtime)}".encode())

    return Huella(
        valor=h.hexdigest(),
        faltantes=faltantes,
        opcionales_faltantes=opcionales_faltantes,
    )
