from __future__ import annotations

import hashlib
import os
import tempfile
from pathlib import Path
from typing import Callable

from app.update.checker import Actualizacion, ErrorRed, abrir

BLOQUE = 256 * 1024


class ErrorIntegridad(RuntimeError):
    pass


def carpeta_descargas() -> Path:
    base = os.getenv("LOCALAPPDATA") or tempfile.gettempdir()
    destino = Path(base) / "Certificacion" / "update"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def _nombre_archivo(info: Actualizacion) -> str:
    cola = info.url.rsplit("/", 1)[-1]
    if cola.lower().endswith(".exe"):
        return cola
    return f"Certificacion-Setup-{info.version.lstrip('vV')}.exe"


def descargar(
    info: Actualizacion,
    progreso: Callable[[int, int], None] | None = None,
    cancelado: Callable[[], bool] | None = None,
) -> Path:
    destino = carpeta_descargas() / _nombre_archivo(info)
    parcial = destino.with_suffix(destino.suffix + ".part")

    if parcial.exists():
        parcial.unlink()

    resumen = hashlib.sha256()
    leido = 0

    try:
        with abrir(info.url, timeout=60) as respuesta:
            total = int(respuesta.headers.get("Content-Length") or info.tamano or 0)
            with parcial.open("wb") as salida:
                while True:
                    if cancelado is not None and cancelado():
                        raise ErrorRed("Descarga cancelada por el usuario.")
                    trozo = respuesta.read(BLOQUE)
                    if not trozo:
                        break
                    salida.write(trozo)
                    resumen.update(trozo)
                    leido += len(trozo)
                    if progreso is not None:
                        progreso(leido, total)
    except ErrorRed:
        parcial.unlink(missing_ok=True)
        raise
    except Exception as exc:
        parcial.unlink(missing_ok=True)
        raise ErrorRed(f"Falló la descarga: {exc}") from exc

    if info.sha256:
        obtenido = resumen.hexdigest().lower()
        if obtenido != info.sha256.lower():
            parcial.unlink(missing_ok=True)
            raise ErrorIntegridad(
                "El archivo descargado no coincide con la firma publicada.\n\n"
                f"Esperado: {info.sha256.lower()}\n"
                f"Obtenido: {obtenido}\n\n"
                "La actualización fue cancelada por seguridad."
            )

    if destino.exists():
        destino.unlink()
    parcial.replace(destino)
    return destino


def limpiar_descargas(conservar: Path | None = None) -> None:
    carpeta = carpeta_descargas()
    for archivo in carpeta.glob("*"):
        if conservar is not None and archivo == conservar:
            continue
        try:
            archivo.unlink()
        except OSError:
            pass
