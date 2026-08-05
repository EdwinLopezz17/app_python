from __future__ import annotations

import shutil
from dataclasses import dataclass

from app import config
from app.catalog.fuentes import Fuente
from app.catalog.hallazgos import Hallazgo, HALLAZGOS
from app.storage.files import eliminar_slots


@dataclass
class ResultadoBorrado:
    archivos: int = 0
    hallazgos_cache: int = 0

    @property
    def hubo_algo(self) -> bool:
        return bool(self.archivos or self.hallazgos_cache)

    def mensaje(self) -> str:
        if not self.hubo_algo:
            return "No había nada que eliminar."
        partes = []
        if self.archivos:
            partes.append(
                f"{self.archivos} archivo(s) de origen"
                if self.archivos != 1 else "1 archivo de origen"
            )
        if self.hallazgos_cache:
            partes.append(f"{self.hallazgos_cache} hallazgo(s) generado(s)")
        return "Se eliminó: " + " y ".join(partes) + "."


def _invalidar(hallazgo: Hallazgo) -> int:
    from app.cache import store

    existia = store.ruta_datos(hallazgo).exists() or store.ruta_meta(hallazgo).exists()
    store.invalidar(hallazgo)
    return 1 if existia else 0


def borrar_fuente(fuente: Fuente) -> ResultadoBorrado:
    return ResultadoBorrado(archivos=eliminar_slots(fuente.slots))


def borrar_hallazgo(hallazgo: Hallazgo) -> ResultadoBorrado:
    slots = [slot for fuente in hallazgo.fuentes for slot in fuente.slots]
    return ResultadoBorrado(
        archivos=eliminar_slots(slots),
        hallazgos_cache=_invalidar(hallazgo),
    )


def hallazgos_de(cert_id: str) -> list[Hallazgo]:
    return [h for h in HALLAZGOS if h.cert_id == cert_id]


def borrar_certificacion(cert_id: str) -> ResultadoBorrado:
    hallazgos = hallazgos_de(cert_id)
    if not hallazgos:
        raise KeyError(f"Certificación no registrada: {cert_id!r}")

    slots = [
        slot
        for hallazgo in hallazgos
        for fuente in hallazgo.fuentes
        for slot in fuente.slots
    ]
    archivos = eliminar_slots(slots)

    carpeta = config.cache_dir() / cert_id
    generados = 0
    if carpeta.exists():
        generados = len(list(carpeta.glob(f"*{config.EXTENSION_DATOS}")))
        shutil.rmtree(carpeta, ignore_errors=True)

    return ResultadoBorrado(archivos=archivos, hallazgos_cache=generados)


def fuentes_compartidas(hallazgo: Hallazgo) -> list[str]:
    propios = set(hallazgo.fuente_ids)
    ajenos = {
        fid
        for otro in HALLAZGOS
        if otro.id != hallazgo.id
        for fid in otro.fuente_ids
    }
    return [
        get_label(fid) for fid in hallazgo.fuente_ids if fid in propios & ajenos
    ]


def get_label(fuente_id: str) -> str:
    from app.catalog.fuentes import get

    return get(fuente_id).label
