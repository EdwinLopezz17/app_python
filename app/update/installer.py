from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

from app.update.bitacora import anotar, ruta_log_inno

ARGUMENTOS = ["/SILENT", "/NORESTART", "/SUPPRESSMSGBOXES"]


class ErrorInstalacion(RuntimeError):
    pass


def _sin_ventana() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0


def _separado() -> int:
    return getattr(subprocess, "DETACHED_PROCESS", 0x00000008) if os.name == "nt" else 0


def _nuevo_grupo() -> int:
    return (
        getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0x00000200)
        if os.name == "nt"
        else 0
    )


def desbloquear(ruta: Path) -> None:
    zona = Path(f"{ruta}:Zone.Identifier")
    try:
        if zona.exists():
            zona.unlink()
            anotar(f"Zone.Identifier eliminado de {ruta.name}")
        else:
            anotar("El archivo no tenia Zone.Identifier.")
    except OSError as exc:
        anotar(f"No se pudo eliminar Zone.Identifier: {exc}")


def lanzar_instalador(ruta: Path, log: Path | None = None) -> None:
    if os.name != "nt":
        raise ErrorInstalacion(
            "La actualización automática solo está disponible en Windows."
        )
    if not ruta.is_file():
        raise ErrorInstalacion(f"No se encontró el instalador en {ruta}")

    desbloquear(ruta)

    log_inno = ruta_log_inno()
    pid = os.getpid()

    comando = [
        str(ruta),
        *ARGUMENTOS,
        f"/LOG={log_inno}",
        f"/PID={pid}",
    ]

    anotar(f"Setup descargado    : {ruta} ({ruta.stat().st_size} bytes)")
    anotar(f"Log de Inno         : {log_inno}")
    anotar(f"PID a esperar       : {pid}")
    anotar("Lanzando el instalador directamente (sin script intermediario).")

    try:
        proceso = subprocess.Popen(
            comando,
            close_fds=True,
            cwd=str(ruta.parent),
            creationflags=_sin_ventana() | _separado() | _nuevo_grupo(),
        )
    except OSError as exc:
        anotar(f"FALLO al lanzar el instalador: {exc}")
        raise ErrorInstalacion(f"No se pudo ejecutar el instalador: {exc}") from exc

    anotar(f"Instalador lanzado con PID {proceso.pid}. Cerrando la aplicacion.")


def ruta_ejecutable() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve()


def carpeta_instalacion() -> Path:
    return ruta_ejecutable().parent


def es_escribible(carpeta: Path) -> bool:
    prueba = carpeta / ".permiso_escritura"
    try:
        prueba.write_text("x", encoding="utf-8")
        prueba.unlink()
        return True
    except OSError:
        return False
