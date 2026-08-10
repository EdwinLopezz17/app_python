
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from app.catalog import resumenes
from app.catalog.hallazgos import certificaciones


@dataclass(frozen=True)
class Entrada:
    ruta: list[str]
    vista: str
    hallazgo_id: str
    fuente_id: str | None = None
    claves: str = ""

    @property
    def hoja(self) -> str:
        return self.ruta[-1]

    @property
    def cola(self) -> list[str]:
        return self.ruta[:-1]


def normalizar(texto: str) -> str:
    plano = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in plano if unicodedata.category(c) != "Mn")


def _cert_display(label: str) -> str:
    return re.sub(r"^Certificación de\s+", "Certificación ", label, flags=re.I)


def _construir() -> list[Entrada]:
    entradas: list[Entrada] = []

    for cert in certificaciones():
        cert_label = _cert_display(cert.label)

        for hallazgo in cert.hallazgos:
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

            base = [cert_label, "Cargar Información", hallazgo.label]
            for fuente in hallazgo.fuentes:
                etiquetas = [s.label for s in fuente.slots if s.label]
                comunes = [fuente.label, fuente.id, fuente.group]
                comunes += [s.key for s in fuente.slots]
                comunes += etiquetas

                if len(etiquetas) > 1:
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
    global _INDICE
    if not _INDICE:
        _INDICE = _construir()
    return _INDICE


def buscar(consulta: str, limite: int = 12) -> list[Entrada]:
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
            puntuadas.append((puntos, orden, entrada))

    puntuadas.sort(key=lambda p: (p[0], p[1]))
    return [entrada for _, _, entrada in puntuadas[:limite]]
