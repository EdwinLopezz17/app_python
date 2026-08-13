from __future__ import annotations

from dataclasses import dataclass

from app.catalog.fuentes import Fuente
from app.catalog.hallazgos import Hallazgo, HALLAZGOS
from app.generation import reports
from app.storage.files import eliminar_slots


@dataclass
class ResultadoBorrado:
    archivos: int = 0

    @property
    def hubo_algo(self) -> bool:
        return bool(self.archivos)

    def mensaje(self) -> str:
        if not self.hubo_algo:
            return "No había nada que eliminar."
        plural = "archivo(s) de origen" if self.archivos != 1 else "archivo de origen"
        return f"Se eliminó: {self.archivos} {plural}."


def borrar_fuente(fuente: Fuente) -> ResultadoBorrado:
    return ResultadoBorrado(archivos=eliminar_slots(fuente.slots))


def borrar_hallazgo(hallazgo: Hallazgo) -> ResultadoBorrado:
    slots = [slot for fuente in hallazgo.fuentes for slot in fuente.slots]
    reports.olvidar(hallazgo.id)
    return ResultadoBorrado(archivos=eliminar_slots(slots))


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
    for hallazgo in hallazgos:
        reports.olvidar(hallazgo.id)

    return ResultadoBorrado(archivos=eliminar_slots(slots))


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
