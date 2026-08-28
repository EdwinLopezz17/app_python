from __future__ import annotations

import getpass
import os
import platform
import shutil
import socket
import sys
import tempfile
from datetime import datetime
from pathlib import Path

def carpeta_logs() -> Path:
    base = os.getenv("LOCALAPPDATA") or tempfile.gettempdir()
    destino = Path(base) / "Certificacion" / "logs"
    destino.mkdir(parents=True, exist_ok=True)
    return destino

def ruta_log() -> Path:
    return carpeta_logs() / f"update-{datetime.now():%Y%m%d}.log"

def ruta_log_inno() -> Path:
    return carpeta_logs() / f"inno-{datetime.now():%Y%m%d-%H%M%S}.log"

def anotar(mensaje: str) -> None:
    try:
        with ruta_log().open("a", encoding="utf-8") as salida:
            salida.write(f"{datetime.now():%Y-%m-%d %H:%M:%S}  {mensaje}\n")
    except OSError:
        pass


def abrir_sesion(version_local: str, version_remota: str) -> None:
    from app.update.installer import carpeta_instalacion, es_escribible

    carpeta = carpeta_instalacion()
    anotar("=" * 70)
    anotar(f"INICIO ACTUALIZACION  {version_local} -> {version_remota}")
    anotar(f"Usuario           : {getpass.getuser()}")
    anotar(f"Equipo            : {socket.gethostname()}")
    anotar(f"Windows           : {platform.platform()}")
    anotar(f"PID               : {os.getpid()}")
    anotar(f"Ejecutable        : {sys.executable}")
    anotar(f"Carpeta instalada : {carpeta}")
    anotar(f"Escribible        : {es_escribible(carpeta)}")
    anotar(f"TEMP              : {tempfile.gettempdir()}")


def cerrar_sesion(exito: bool, detalle: str = "") -> None:
    anotar(f"RESULTADO: {'OK' if exito else 'FALLO'}  {detalle}".rstrip())
    if not exito:
        copiar_a_datos()


def copiar_a_datos() -> None:
    try:
        from app.ingest import config

        destino = config.data_path() / "_logs"
        destino.mkdir(parents=True, exist_ok=True)
        marca = f"{getpass.getuser()}-{socket.gethostname()}-{datetime.now():%Y%m%d-%H%M%S}"
        for origen in sorted(carpeta_logs().glob("*.log")):
            shutil.copy2(origen, destino / f"{marca}-{origen.name}")
        anotar(f"Logs copiados a {destino}")
    except Exception as exc:
        anotar(f"No se pudieron copiar los logs a DATA_PATH: {exc}")


