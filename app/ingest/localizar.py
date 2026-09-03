from __future__ import annotations

from dataclasses import dataclass

from app.ingest.normalize import norm_header

MAX_FILAS = 20
MAX_COLUMNAS = 10

@dataclass(frozen=True)
class Ancla:
    fila: int = 0
    columna: int = 0
    aciertos: int = 0
    esperadas: int = 0

    @property
    def completa(self) -> bool:
        return self.esperadas > 0 and self.aciertos == self.esperadas

    @property
    def desplazada(self) -> bool:
        return self.fila > 0 or self.columna > 0

def _texto(valor: object) -> str:
    return "" if valor is None else str(valor)

def _normalizadas(fila: list, desde: int) -> set[str]:
    return {
        norm_header(c) for c in fila[desde:] if _texto(c).strip()
    }


def _ajustar_izquierda(
    fila: list, columna: int, objetivo: set[str]
) -> int:
    limite = len(fila) - 1
    while columna < limite:
        celda = _texto(fila[columna]).strip()
        if celda and norm_header(celda) in objetivo:
            break
        if not objetivo.issubset(_normalizadas(fila, columna + 1)):
            break
        columna += 1
    return columna


def localizar_cabecera(
    matriz: list[list],
    esperadas: list[str],
    max_filas: int = MAX_FILAS,
    max_columnas: int = MAX_COLUMNAS,
) -> Ancla:
    if not matriz or not esperadas:
        return Ancla(0, 0, 0, len(esperadas or []))

    objetivo = {norm_header(c) for c in esperadas}
    total = len(objetivo)

    filas = min(len(matriz), max_filas)
    ancho = max((len(f) for f in matriz[:filas]), default=0)
    columnas = min(ancho, max_columnas)

    mejor = Ancla(0, 0, 0, total)

    for columna in range(columnas):
        for indice in range(filas):
            fila = matriz[indice]
            if columna >= len(fila):
                continue
            if not _texto(fila[columna]).strip():
                continue

            presentes = _normalizadas(fila, columna)
            aciertos = len(objetivo & presentes)

            if aciertos == total:
                final = _ajustar_izquierda(fila, columna, objetivo)
                return Ancla(indice, final, aciertos, total)

            if aciertos > mejor.aciertos:
                mejor = Ancla(indice, columna, aciertos, total)

    return mejor








