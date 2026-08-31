from __future__ import annotations

import getpass
import json
import os
import platform
import socket
import sys
import tempfile
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

from app.__version__ import __version__

_SESION = f"{datetime.now():%Y%m%d%H%M%S}-{os.getpid()}"


def carpeta_logs() -> Path:
    base = os.getenv("LOCALAPPDATA") or tempfile.gettempdir()
    destino = Path(base) / "Certificacion" / "logs"
    destino.mkdir(parents=True, exist_ok=True)
    return destino


def ruta_texto() -> Path:
    return carpeta_logs() / f"uso-{datetime.now():%Y%m%d}.log"


def ruta_jsonl() -> Path:
    return carpeta_logs() / f"uso-{datetime.now():%Y%m}.jsonl"


def identidad() -> dict[str, str]:
    try:
        usuario = getpass.getuser()
    except Exception:
        usuario = "desconocido"
    try:
        equipo = socket.gethostname()
    except Exception:
        equipo = "desconocido"
    return {"usuario": usuario, "equipo": equipo, "version": __version__}


def _linea_texto(evento: str, datos: dict[str, Any]) -> str:
    partes = []
    for clave, valor in datos.items():
        if clave in ("usuario", "equipo", "version", "sesion", "ts"):
            continue
        if valor in (None, "", []):
            continue
        if clave == "traceback":
            continue
        partes.append(f"{clave}={valor}")
    cola = "  ".join(partes)
    return f"{datetime.now():%Y-%m-%d %H:%M:%S}  {evento:<22} {cola}".rstrip()


def registrar(evento: str, **datos: Any) -> None:
    registro = {
        "ts": datetime.now().isoformat(timespec="seconds"),
        "sesion": _SESION,
        "evento": evento,
        **identidad(),
        **datos,
    }

    try:
        with ruta_jsonl().open("a", encoding="utf-8") as salida:
            salida.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
    except OSError:
        pass

    try:
        with ruta_texto().open("a", encoding="utf-8") as salida:
            salida.write(_linea_texto(evento, registro) + "\n")
            rastro = datos.get("traceback")
            if rastro:
                for linea in str(rastro).rstrip().splitlines():
                    salida.write(f"    | {linea}\n")
    except OSError:
        pass


def registrar_excepcion(evento: str, exc: BaseException, **datos: Any) -> None:
    registro = {
        "error": f"{exc.__class__.__name__}: {exc}",
        "traceback": "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        ),
    }
    registrar(evento, **registro, **datos)


def abrir_sesion() -> None:
    ident = identidad()
    registrar("=" * 30, marca="INICIO DE SESION")
    registrar(
        "app_inicio",
        usuario_so=ident["usuario"],
        windows=platform.platform(),
        pid=os.getpid(),
        ejecutable=sys.executable,
        congelado=bool(getattr(sys, "frozen", False)),
        logs=str(carpeta_logs()),
    )
    try:
        from app import config

        registrar("data_path", ruta=str(config.data_path()))
    except Exception as exc:
        registrar("data_path_error", error=str(exc))


def cerrar_sesion() -> None:
    registrar("app_cierre")
    publicar()


def publicar() -> None:
    try:
        from app import config

        destino = config.data_path() / "_logs"
        destino.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        registrar("publicar_error", error=str(exc))
        return

    ident = identidad()
    marca = f"{ident['equipo']}-{ident['usuario']}"
    copiados = 0
    for origen in sorted(carpeta_logs().glob("uso-*")):
        try:
            contenido = origen.read_bytes()
            (destino / f"{marca}-{origen.name}").write_bytes(contenido)
            copiados += 1
        except OSError:
            continue
    registrar("publicar", destino=str(destino), archivos=copiados)


def resumen_para_usuario() -> str:
    return (
        f"Bitácora de esta sesión:\n{ruta_texto()}\n\n"
        f"Copia compartida al cerrar la aplicación:\n"
        f"carpeta de datos \\ _logs"
    )
