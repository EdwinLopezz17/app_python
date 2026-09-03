from __future__ import annotations

import re

SERVIDOR = "el servidor de actualizaciones"

_URL = re.compile(r"https?://[^\s<>\"')\]]+", re.IGNORECASE)
_DOMINIO = re.compile(
    r"\b(?:[A-Za-z0-9-]+\.)+(?:com|net|org|io|dev|co|app|cloud)\b(?:/[^\s]*)?",
    re.IGNORECASE,
)
_MARCAS = re.compile(
    r"\b(github(?:usercontent)?|EdwinLopezz17|app_python|git)\b",
    re.IGNORECASE,
)
_ENLACE_MD = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
_ESPACIOS = re.compile(r"[ \t]{2,}")


def sin_origen(texto: str) -> str:
    if not texto:
        return ""
    limpio = _URL.sub(SERVIDOR, str(texto))
    limpio = _DOMINIO.sub(SERVIDOR, limpio)
    limpio = _MARCAS.sub("el servidor", limpio)
    limpio = _ESPACIOS.sub(" ", limpio)
    return limpio.strip()


def limpiar_notas(texto: str) -> str:
    if not texto:
        return ""

    sin_enlaces = _ENLACE_MD.sub(r"\1", str(texto))

    lineas = []
    for linea in sin_enlaces.splitlines():
        if _URL.search(linea) or _MARCAS.search(linea):
            continue
        if linea.strip().lower().startswith(("full changelog", "compare", "commits")):
            continue
        lineas.append(linea.rstrip())

    while lineas and not lineas[0].strip():
        lineas.pop(0)
    while lineas and not lineas[-1].strip():
        lineas.pop()

    return "\n".join(lineas).strip()
