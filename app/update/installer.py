from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

from app.update.bitacora import anotar, ruta_log_inno

ARGUMENTOS = ["/SILENT", "/NORESTART", "/SUPPRESSMSGBOXES"]

PLANTILLA = r"""@echo off
setlocal
set PID={pid}
set N=0

:esperar
tasklist /FI "PID eq %PID%" 2>nul | find "%PID%" >nul
if errorlevel 1 goto instalar
set /a N+=1
if %N% GEQ 90 goto rendirse
timeout /t 1 /nobreak >nul
goto esperar

:rendirse
echo [cmd] La aplicacion no cerro en 90 segundos. >> "{log}"
goto fin

:instalar
timeout /t 3 /nobreak >nul
echo [cmd] Lanzando instalador: {setup} >> "{log}"
start "" /wait "{setup}" {args} /LOG="{innolog}"
set CODIGO=%ERRORLEVEL%
echo [cmd] Codigo de salida de Inno: %CODIGO% >> "{log}"
if not "%CODIGO%"=="0" goto fin
echo [cmd] Relanzando aplicacion. >> "{log}"
start "" "{exe}"

:fin
del "%~f0"
"""


class ErrorInstalacion(RuntimeError):
    pass


def _sin_ventana() -> int:
    return getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000) if os.name == "nt" else 0


def _separado() -> int:
    return getattr(subprocess, "DETACHED_PROCESS", 0x00000008) if os.name == "nt" else 0


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
        raise ErrorInstalacion("La actualización automática solo está disponible en Windows.")
    if not ruta.is_file():
        raise ErrorInstalacion(f"No se encontró el instalador en {ruta}")

    desbloquear(ruta)

    from app.update.bitacora import ruta_log

    script = Path(tempfile.gettempdir()) / f"cert_update_{os.getpid()}.cmd"
    contenido = PLANTILLA.format(
        pid=os.getpid(),
        setup=ruta,
        args=" ".join(ARGUMENTOS),
        log=ruta_log(),
        innolog=ruta_log_inno(),
        exe=ruta_ejecutable(),
    )
    script.write_text(contenido, encoding="cp1252")

    anotar(f"Script intermediario: {script}")
    anotar(f"Setup descargado    : {ruta} ({ruta.stat().st_size} bytes)")
    anotar(f"Log de Inno         : {ruta_log_inno()}")
    anotar("Lanzando cmd.exe y cerrando la aplicacion.")

    try:
        subprocess.Popen(
            ["cmd.exe", "/c", str(script)],
            close_fds=True,
            creationflags=_sin_ventana() | _separado(),
        )
    except OSError as exc:
        anotar(f"FALLO al lanzar cmd.exe: {exc}")
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