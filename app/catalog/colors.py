from __future__ import annotations

from dataclasses import dataclass


SURFACE_CONTAINER_HIGH = "#e2e7ff"
ON_SURFACE = "#131b2e"
INVERSE_SURFACE = "#283044"
OUTLINE = "#6e7880"
PRIMARY = "#006386"
SECONDARY = "#006d38"
TERTIARY = "#964400"
ERROR = "#ba1a1a"


@dataclass(frozen=True)
class GrupoColor:
    id: str
    label: str
    fill: str
    text: str


GRUPOS: dict[str, GrupoColor] = {
    "C1": GrupoColor("C1", "Aplicación", PRIMARY, "#ffffff"),
    "C2": GrupoColor("C2", "DNI vs Usuario", SECONDARY, "#ffffff"),
    "C3": GrupoColor("C3", "AD PPS", TERTIARY, "#ffffff"),
    "C4": GrupoColor("C4", "AD VIDA", INVERSE_SURFACE, "#ffffff"),
    "C5": GrupoColor("C5", "GDH", OUTLINE, "#ffffff"),
    "C6": GrupoColor("C6", "Ticket Cese", ERROR, "#ffffff"),
    "C7": GrupoColor("C7", "Estado Entra ID", ON_SURFACE, "#ffffff"),
    "C8": GrupoColor("C8", "Escenarios", "#bc5800", "#ffffff"),
    "C9": GrupoColor("C9", "Rol Final", "#8a5a00", "#ffffff"),
    "C10": GrupoColor("C10", "Matriz de Roles", "#3f6212", "#ffffff"),
    "C11": GrupoColor("C11", "Rol Ticket", "#7a1fa2", "#ffffff"),
}

GRUPO_POR_DEFECTO = "C1"


def grupos_disponibles() -> list[GrupoColor]:
    return list(GRUPOS.values())
