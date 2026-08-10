"""Índice de búsqueda global, réplica de `lib/search-index.ts`.

Aplana, para TODAS las certificaciones:

1. Las hojas navegables del árbol (Cargar Información / Ver Hallazgos /
   Generar Resumen de cada hallazgo).
2. Cada fuente de «Cargar Información», y sus slots con etiqueta propia
   (p. ej. «AD PPS»), como destino a esa pantalla con la card enfocada.

Cada entrada se muestra como una ruta de migas —
«Certificación Usuarios › Certificar › Active Directory › Ver Hallazgos» —
y al elegirla navega a su destino.

El índice se construye una sola vez: el catálogo es estático.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.catalog import resumenes
from app.catalog.hallazgos import certificaciones


@dataclass(frozen=True)
class Entrada:
    #: Ruta completa de migas, incluida la certificación al inicio.
    ruta: list[str]
    #: "cargar" | "hallazgo" | "resumen".
    vista: str
    hallazgo_id: str
    #: Fuente a enfocar al llegar, solo para entradas de tipo fuente.
    fuente_id: str | None = None
    #: Texto normalizado sobre el que se hace el match.
    claves: str = ""

    @property
    def hoja(self) -> str:
        return self.ruta[-1]

    @property
    def cola(self) -> list[str]:
        return self.ruta[:-1]


def normalizar(texto: str) -> str:
    """Minúsculas y sin acentos, para que «active» encuentre «Áctive»."""
    plano = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in plano if unicodedata.category(c) != "Mn")


def _cert_display(label: str) -> str:
    """«Certificación de Usuarios» → «Certificación Usuarios»."""
    return re.sub(r"^Certificación de\s+", "Certificación ", label, flags=re.I)


def _construir() -> list[Entrada]:
    entradas: list[Entrada] = []

    for cert in certificaciones():
        cert_label = _cert_display(cert.label)

        for hallazgo in cert.hallazgos:
            # 1) Hojas del árbol de navegación.
            hojas = [
                ("Cargar Información", "cargar"),
                ("Ver Hallazgos", "hallazgo"),
            ]
            if resumenes.disponible(hallazgo.id):
                hojas.append(("Generar Resumen", "resumen"))

            for etiqueta, vista in hojas:
                ruta = [cert_label, "Certificar", hallazgo.label, etiqueta]
                entradas.append(
                    Entrada(
                        ruta=ruta,
                        vista=vista,
                        hallazgo_id=hallazgo.id,
                        claves=normalizar(" ".join(ruta + [hallazgo.id])),
                    )
                )

            # 2) Fuentes de «Cargar Información», con la card enfocada.
            base = [cert_label, "Cargar Información", hallazgo.label]
            for fuente in hallazgo.fuentes:
                etiquetas = [s.label for s in fuente.slots if s.label]
                comunes = [fuente.label, fuente.id, fuente.group]
                comunes += [s.key for s in fuente.slots]
                comunes += etiquetas

                if len(etiquetas) > 1:
                    # Card con varios slots etiquetados (AD PPS / AD Vida):
                    # una entrada por slot, para poder buscar «AD Vida».
                    for indice, slot in enumerate(fuente.slots):
                        hoja = slot.label or f"Archivo {indice + 1}"
                        ruta = base + [fuente.label, hoja]
                        entradas.append(
                            Entrada(
                                ruta=ruta,
                                vista="cargar",
                                hallazgo_id=hallazgo.id,
                                fuente_id=fuente.id,
                                claves=normalizar(
                                    " ".join(ruta + comunes + [slot.key])
                                ),
                            )
                        )
                else:
                    ruta = base + [fuente.label]
                    entradas.append(
                        Entrada(
                            ruta=ruta,
                            vista="cargar",
                            hallazgo_id=hallazgo.id,
                            fuente_id=fuente.id,
                            claves=normalizar(" ".join(ruta + comunes)),
                        )
                    )

    return entradas


_INDICE: list[Entrada] = []


def indice() -> list[Entrada]:
    """Índice perezoso: se construye en la primera búsqueda, no al importar."""
    global _INDICE
    if not _INDICE:
        _INDICE = _construir()
    return _INDICE


def buscar(consulta: str, limite: int = 12) -> list[Entrada]:
    """Entradas que contienen TODOS los tokens, por relevancia.

    Puntúa como la referencia: menor es mejor. Cuanto antes aparezca el token
    en el texto, mejor; y que la HOJA empiece por el token pesa mucho más que
    encontrarlo en cualquier parte de la ruta, para que escribir «entra»
    devuelva la fuente Entra ID antes que las diez rutas que la contienen.
    """
    tokens = [t for t in normalizar(consulta).split() if t]
    if not tokens:
        return []

    puntuadas: list[tuple[int, int, Entrada]] = []

    for orden, entrada in enumerate(indice()):
        hoja = normalizar(entrada.hoja)
        puntos = 0
        todos = True

        for token in tokens:
            posicion = entrada.claves.find(token)
            if posicion == -1:
                todos = False
                break
            puntos += posicion
            if hoja.startswith(token):
                puntos -= 50
            elif token in hoja:
                puntos -= 15

        if todos:
            # `orden` desempata de forma estable: sin él, entradas con la misma
            # puntuación bailaban de sitio entre pulsaciones de tecla.
            puntuadas.append((puntos, orden, entrada))

    puntuadas.sort(key=lambda p: (p[0], p[1]))
    return [entrada for _, _, entrada in puntuadas[:limite]]
