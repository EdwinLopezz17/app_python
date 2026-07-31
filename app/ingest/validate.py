"""
Validación de columnas de un archivo de origen.

Port de `validateColumns` del frontend. Criterio idéntico: el archivo es válido
cuando NO falta ninguna columna esperada. Las columnas de más solo se informan;
no bloquean, porque los reportes de origen suelen traer campos extra que a los
servicios de `logic/` simplemente no les interesan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.catalog.fuentes import FORMATOS_ACEPTADOS
from app.ingest.normalize import norm_header


@dataclass
class ResultadoValidacion:
    ok: bool
    faltantes: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)

    def mensaje(self) -> str:
        if self.ok and not self.extra:
            return "Columnas correctas"
        if self.ok:
            return f"Correcto · {len(self.extra)} columna(s) adicional(es)"
        n = len(self.faltantes)
        detalle = ", ".join(self.faltantes[:3])
        if n > 3:
            detalle += f" y {n - 3} más"
        return f"Faltan {n} columna(s): {detalle}"


def formato_permitido(nombre_archivo: str) -> bool:
    return Path(nombre_archivo).suffix.lower() in FORMATOS_ACEPTADOS


def validar_columnas(esperadas: list[str], encontradas: list[str]) -> ResultadoValidacion:
    """Compara ambos conjuntos ya normalizados. Preserva el nombre original al reportar."""
    set_encontradas = {norm_header(c) for c in encontradas}
    set_esperadas = {norm_header(c) for c in esperadas}

    faltantes = [c for c in esperadas if norm_header(c) not in set_encontradas]
    extra = [c for c in encontradas if norm_header(c) not in set_esperadas]

    return ResultadoValidacion(ok=not faltantes, faltantes=faltantes, extra=extra)
