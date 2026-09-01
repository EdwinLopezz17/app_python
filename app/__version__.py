from __future__ import annotations

__version__ = "1.0.14"

GITHUB_OWNER = "EdwinLopezz17"
GITHUB_REPO = "app_python"


def version_tupla(texto: str) -> tuple[int, ...]:
    limpio = str(texto).strip().lstrip("vV")
    limpio = limpio.split("-")[0].split("+")[0]
    partes = []
    for trozo in limpio.split("."):
        digitos = "".join(c for c in trozo if c.isdigit())
        partes.append(int(digitos) if digitos else 0)
    while len(partes) < 3:
        partes.append(0)
    return tuple(partes[:3])


def es_mas_nueva(remota: str, local: str = __version__) -> bool:
    return version_tupla(remota) > version_tupla(local)
