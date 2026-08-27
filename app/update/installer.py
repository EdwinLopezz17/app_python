from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ARGUMENTOS = [
    "/SILENT",
    "/NORESTART",
    "/SUPPRESSMSGBOXES",
    "/CLOSEAPPLICATIONS",
    "/RESTARTAPPLICATIONS",
]


class ErrorInstalacion(RuntimeError):
    pass


def _sin_ventana() -> int:
    if os.name != "nt":
        return 0
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)


def _separado() -> int:
    if os.name != "nt":
        return 0
    return getattr(subprocess, "DETACHED_PROCESS", 0x00000008)


def lanzar_instalador(ruta: Path, log: Path | None = None) -> None:
    if os.name != "nt":
        raise ErrorInstalacion("La actualización automática solo está disponible en Windows.")

    if not ruta.is_file():
        raise ErrorInstalacion(f"No se encontró el instalador en {ruta}")

    pid = os.getpid()
    args = " ".join(ARGUMENTOS)
    if log is not None:
        args += f' /LOG="{log}"'

    ps = (
        f"Wait-Process -Id {pid} -Timeout 60 -ErrorAction SilentlyContinue; "
        f"Start-Sleep -Seconds 2; "
        f"Start-Process -FilePath '{ruta}' -ArgumentList '{args}'"
    )

    try:
        subprocess.Popen(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-Command", ps],
            close_fds=True,
            creationflags=_sin_ventana() | _separado(),
        )
    except OSError as exc:
        raise ErrorInstalacion(f"No se pudo ejecutar el instalador: {exc}") from exc

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
