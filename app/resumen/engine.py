"""Motor genérico de «Resumen por escenarios».

Port de `src/lib/resumen/scenario-engine.ts` del front Next.js. Toda la lógica
vive aquí; cada certificación solo aporta un archivo de CONFIG declarativo (una
lista de `Escenario`) en `app/catalog/`. Es a los resúmenes lo que
`catalog/fuentes.py` es a «Cargar Información».

Dos formas de resumen, ambas con el mismo criterio de pertenencia:

  · `por_escenario`  — una fila por escenario (Active Directory: H1_AD…H7_AD).
  · `por_grupo`      — una fila por valor de un campo, con columnas por
                       escenario (Aplicaciones: una fila por aplicación).

CONTEO INCLUSIVO: una fila marcada en varios escenarios cuenta en todos, así
que la suma de totales puede superar el número de filas del reporte. Lo mismo
con Responsable: «GDH | ACCESOS» suma +1 en GDH y +1 en ACCESOS.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence

# ── Normalización ──────────────────────────────────────────────────────────

# Valores que cuentan como "vacío / negativo" en una marca de escenario.
NEGATIVOS = {"", "NO", "0", "FALSE", "N", "NULL", "-", "N/A", "NAN", "NONE"}

# Valores que cuentan como marca en modo estricto. El front usa solo 'X'
# porque su backend emite 'X'; aquí el modelo trae booleanos y el Excel
# exportado puede traer «Sí», «TRUE» o «VERDADERO» según cómo se guarde.
MARCAS = {"X", "SI", "SÍ", "TRUE", "VERDADERO", "1", "Y", "YES"}


def _norm(valor: Any) -> str:
    return str(valor if valor is not None else "").strip().upper()


def es_positivo(valor: Any) -> bool:
    """Heurística amplia: positivo = cualquier cosa que no sea vacío/negativo."""
    return _norm(valor) not in NEGATIVOS


def es_marca(valor: Any) -> bool:
    """Marca estricta: la celda dice explícitamente que sí (X, Sí, TRUE, 1…)."""
    return _norm(valor) in MARCAS


def tiene_valor(valor: Any) -> bool:
    return _norm(valor) != ""


ModoMarca = Literal["positivo", "marca"]


def cumple_marca(valor: Any, modo: ModoMarca = "positivo") -> bool:
    return es_marca(valor) if modo == "marca" else es_positivo(valor)


# ── Filtros declarativos ───────────────────────────────────────────────────

Operador = Literal[
    "igual", "distinto", "en", "no_vacio", "positivo", "contiene", "no_contiene"
]


@dataclass(frozen=True)
class Filtro:
    """Condición extra sobre una fila; se aplican todas en AND."""

    campo: str
    op: Operador
    valor: str = ""
    valores: tuple[str, ...] = ()

    def cumple(self, fila: dict) -> bool:
        celda = _norm(fila.get(self.campo))
        if self.op == "igual":
            return celda == _norm(self.valor)
        if self.op == "distinto":
            return celda != _norm(self.valor)
        if self.op == "en":
            return celda in {_norm(v) for v in self.valores}
        if self.op == "no_vacio":
            return celda != ""
        if self.op == "positivo":
            return es_positivo(fila.get(self.campo))
        if self.op == "contiene":
            return _norm(self.valor) in celda
        if self.op == "no_contiene":
            return _norm(self.valor) not in celda
        return True


# ── Definición de escenario ────────────────────────────────────────────────

CAMPO_RESPONSABLE = "responsable"
CAMPO_COMENTARIO = "comentario"


@dataclass(frozen=True)
class Escenario:
    code: str
    title: str
    #: Campo que marca la pertenencia base. Vacío = solo filtros.
    flag: str = ""
    #: Cómo interpretar `flag`. "marca" exige X/Sí/TRUE; "positivo" es amplio.
    modo: ModoMarca = "positivo"
    #: Si es True, una fila sin Responsable no cuenta ni sale en el detalle.
    exige_responsable: bool = False
    campo_responsable: str = CAMPO_RESPONSABLE
    #: Campos que se pintan en la hoja de detalle, en orden.
    columnas: tuple[str, ...] = ()
    filtros: tuple[Filtro, ...] = ()

    def cumple(self, fila: dict) -> bool:
        if self.flag and not cumple_marca(fila.get(self.flag), self.modo):
            return False
        if self.exige_responsable and not tiene_valor(fila.get(self.campo_responsable)):
            return False
        return all(f.cumple(fila) for f in self.filtros)


def filas_de_escenario(filas: Sequence[dict], escenario: Escenario) -> list[dict]:
    """Único punto de decisión: lo usan la vista previa y la exportación."""
    return [f for f in filas if escenario.cumple(f)]


# ── Responsable ────────────────────────────────────────────────────────────
# Clasificación NO excluyente: «GDH | ACCESOS» suma en ambas columnas.


def tiene_gdh(valor: Any) -> bool:
    return "GDH" in _norm(valor)


def tiene_accesos(valor: Any) -> bool:
    return "ACCESO" in _norm(valor)


def contar_por_responsable(
    filas: Sequence[dict], responsable: Literal["GDH", "ACCESOS"],
    campo: str = CAMPO_RESPONSABLE,
) -> int:
    prueba = tiene_gdh if responsable == "GDH" else tiene_accesos
    return sum(1 for f in filas if prueba(f.get(campo)))


def juntar_comentarios(filas: Sequence[dict], campo: str = CAMPO_COMENTARIO) -> str:
    vistos: dict[str, None] = {}
    for fila in filas:
        texto = str(fila.get(campo) or "").strip()
        if texto:
            vistos.setdefault(texto, None)
    return " | ".join(vistos)


# ── Resumen por escenario (Active Directory) ───────────────────────────────


@dataclass
class FilaEscenario:
    code: str
    title: str
    total: int
    gdh: int
    accesos: int


@dataclass
class ResumenEscenarios:
    filas: list[FilaEscenario]
    total_registros: int
    total_hallazgos: int

    @property
    def total_gdh(self) -> int:
        return sum(f.gdh for f in self.filas)

    @property
    def total_accesos(self) -> int:
        return sum(f.accesos for f in self.filas)

    @property
    def escenarios_con_datos(self) -> int:
        return sum(1 for f in self.filas if f.total)


def por_escenario(
    filas: Sequence[dict], escenarios: Sequence[Escenario]
) -> ResumenEscenarios:
    salida: list[FilaEscenario] = []
    for escenario in escenarios:
        alcance = filas_de_escenario(filas, escenario)
        salida.append(FilaEscenario(
            code=escenario.code,
            title=escenario.title,
            total=len(alcance),
            gdh=contar_por_responsable(alcance, "GDH", escenario.campo_responsable),
            accesos=contar_por_responsable(alcance, "ACCESOS", escenario.campo_responsable),
        ))

    return ResumenEscenarios(
        filas=salida,
        total_registros=len(filas),
        total_hallazgos=sum(f.total for f in salida),
    )


# ── Resumen por grupo (Aplicaciones) ───────────────────────────────────────


@dataclass
class FilaGrupo:
    grupo: str
    #: {code_escenario: (total, gdh, accesos)}
    conteos: dict[str, tuple[int, int, int]] = field(default_factory=dict)

    def total(self, code: str) -> int:
        return self.conteos.get(code, (0, 0, 0))[0]

    def gdh(self, code: str) -> int:
        return self.conteos.get(code, (0, 0, 0))[1]

    def accesos(self, code: str) -> int:
        return self.conteos.get(code, (0, 0, 0))[2]


@dataclass
class ResumenGrupos:
    filas: list[FilaGrupo]
    total: FilaGrupo
    codes: list[str]
    total_registros: int

    @property
    def total_hallazgos(self) -> int:
        return sum(self.total.total(c) for c in self.codes)


def _clave_orden(texto: str) -> str:
    """Orden alfabético tolerante a tildes (equivalente a localeCompare 'es')."""
    import unicodedata

    base = unicodedata.normalize("NFD", texto.upper())
    return "".join(c for c in base if not unicodedata.combining(c))


def por_grupo(
    filas: Sequence[dict], escenarios: Sequence[Escenario], campo_grupo: str
) -> ResumenGrupos:
    codes = [e.code for e in escenarios]
    acumulado: dict[str, FilaGrupo] = {}

    for fila in filas:
        grupo = str(fila.get(campo_grupo) or "").strip()
        if not grupo:
            continue
        destino = acumulado.setdefault(grupo, FilaGrupo(grupo))

        for escenario in escenarios:
            if not escenario.cumple(fila):
                continue
            total, gdh, accesos = destino.conteos.get(escenario.code, (0, 0, 0))
            responsable = fila.get(escenario.campo_responsable)
            destino.conteos[escenario.code] = (
                total + 1,
                gdh + (1 if tiene_gdh(responsable) else 0),
                accesos + (1 if tiene_accesos(responsable) else 0),
            )

    ordenadas = sorted(acumulado.values(), key=lambda f: _clave_orden(f.grupo))

    total = FilaGrupo("TOTAL")
    for code in codes:
        total.conteos[code] = (
            sum(f.total(code) for f in ordenadas),
            sum(f.gdh(code) for f in ordenadas),
            sum(f.accesos(code) for f in ordenadas),
        )

    return ResumenGrupos(
        filas=ordenadas, total=total, codes=codes, total_registros=len(filas)
    )


# ── Utilidad de fechas (paridad con monthOf del front) ─────────────────────

_ISO = re.compile(r"^(\d{4})-(\d{2})")
_DMY = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})")


def mes_de(valor: Any) -> str | None:
    """'YYYY-MM' a partir de una fecha en ISO o dd/mm/yyyy. None si no parsea."""
    crudo = str(valor or "").strip()
    if not crudo:
        return None
    iso = _ISO.match(crudo)
    if iso:
        return f"{iso.group(1)}-{iso.group(2)}"
    dmy = _DMY.match(crudo)
    if dmy:
        return f"{dmy.group(3)}-{dmy.group(2).zfill(2)}"
    return None
