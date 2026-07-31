"""
BORRADO POR ALCANCE  (slot · fuente · hallazgo · certificación)
==============================================================

Eliminar un archivo cargado nunca es solo eliminar ese archivo: hay un hallazgo
generado en caché que se calculó A PARTIR de él y que, si sobrevive, queda
mostrando resultados de datos que ya no existen. Ese es el estado inconsistente
clásico y es el que este módulo cierra: los datos de origen y sus derivados se
eliminan siempre en la misma operación.

Por qué vive aquí y no en `storage/files.py`:

    app.cache.fingerprint  ->  app.storage.files

Si `files.py` importara `app.cache.store` para invalidar la caché, el import
sería circular. `purge.py` está por encima de ambos y los orquesta: `files.py`
sigue sabiendo solo de disco, y `store.py` sigue sabiendo solo de caché.

ALCANCES
--------
  * `slot`          : un archivo.
  * `fuente`        : todos los slots de una card (AD = PPS + Vida).
  * `hallazgo`      : todas las fuentes que ese hallazgo requiere + su caché.
  * `certificación` : todos los hallazgos de la certificación + toda su caché.

Aviso que la UI DEBE mostrar: las fuentes transversales (DNI vs Usuarios, GDH,
AD, Tickets Ceses) están compartidas entre certificaciones. Eliminarlas desde
Usuarios también las quita de Base de Datos y de Perfiles, porque es el mismo
archivo en disco, no una copia. Ocultar ese efecto sería mentirle al auditor.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass

from app import config
from app.catalog.fuentes import Fuente
from app.catalog.hallazgos import Hallazgo, HALLAZGOS
from app.storage.files import eliminar_slots


@dataclass
class ResultadoBorrado:
    """Lo que realmente se eliminó. Se usa para el mensaje final al usuario."""

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
    """
    Borra el hallazgo generado en caché. Import diferido a propósito: mantiene
    `app.cache` fuera del grafo de imports de `app.storage`.
    """
    from app.cache import store

    existia = store.ruta_parquet(hallazgo).exists() or store.ruta_meta(hallazgo).exists()
    store.invalidar(hallazgo)
    return 1 if existia else 0


# ---------------------------------------------------------------------------
# Alcances
# ---------------------------------------------------------------------------

def borrar_fuente(fuente: Fuente) -> ResultadoBorrado:
    """
    Elimina los archivos de una card y desactualiza los hallazgos que la usaban.

    No se invalida la caché aquí: `app.cache.fingerprint` ya detecta por sí solo
    que la fuente desapareció y marca el hallazgo como DESACTUALIZADO. Borrar el
    resultado anterior dejaría la pantalla en blanco; marcarlo como obsoleto le
    permite al auditor seguir viéndolo con el aviso correspondiente. Ese
    comportamiento existente se respeta.
    """
    return ResultadoBorrado(archivos=eliminar_slots(fuente.slots))


def borrar_hallazgo(hallazgo: Hallazgo) -> ResultadoBorrado:
    """Elimina TODAS las fuentes que alimentan un hallazgo y su caché."""
    slots = [slot for fuente in hallazgo.fuentes for slot in fuente.slots]
    return ResultadoBorrado(
        archivos=eliminar_slots(slots),
        hallazgos_cache=_invalidar(hallazgo),
    )


def hallazgos_de(cert_id: str) -> list[Hallazgo]:
    return [h for h in HALLAZGOS if h.cert_id == cert_id]


def borrar_certificacion(cert_id: str) -> ResultadoBorrado:
    """
    Elimina todo lo correspondiente a una certificación completa: los archivos
    de origen de todos sus hallazgos y toda su carpeta de caché.

    La carpeta de caché se borra entera (`<CACHE_DIR>/<cert_id>`) en lugar de
    hallazgo por hallazgo. Así también desaparecen los restos de hallazgos que
    ya no están en el catálogo pero cuyo Parquet quedó del release anterior.
    """
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
        generados = len(list(carpeta.glob("*.parquet")))
        shutil.rmtree(carpeta, ignore_errors=True)

    return ResultadoBorrado(archivos=archivos, hallazgos_cache=generados)


def fuentes_compartidas(hallazgo: Hallazgo) -> list[str]:
    """
    Fuentes del hallazgo que TAMBIÉN usa otro hallazgo del catálogo.

    La UI las lista en el diálogo de confirmación: son las que van a
    desaparecer de pantallas donde el auditor no está parado en este momento.
    """
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
