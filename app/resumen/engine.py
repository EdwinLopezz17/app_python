from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Literal, Sequence


NEGATIVOS = {"", "NO", "0", "FALSE", "N", "NULL", "-", "N/A", "NAN", "NONE"}


MARCAS = {"X", "SI", "SÍ", "TRUE", "VERDADERO", "1", "Y", "YES"}


def _norm(valor: Any) -> str:
    return str(valor if valor is not None else "").strip().upper()


def es_positivo(valor: Any) -> bool:
    return _norm(valor) not in NEGATIVOS


def es_marca(valor: Any) -> bool:
    return _norm(valor) in MARCAS


def tiene_valor(valor: Any) -> bool:
    return _norm(valor) != ""


ModoMarca = Literal["positivo", "marca"]


def cumple_marca(valor: Any, modo: ModoMarca = "positivo") -> bool:
    return es_marca(valor) if modo == "marca" else es_positivo(valor)


Operador = Literal[
    "igual", "distinto", "en", "no_vacio", "positivo", "contiene", "no_contiene"
]


@dataclass(frozen=True)
class Filtro:
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


CAMPO_RESPONSABLE = "responsable"
CAMPO_COMENTARIO = "comentario"


@dataclass(frozen=True)
class Escenario:
    code: str
    title: str

    flag: str = ""

    modo: ModoMarca = "positivo"


    reporta_responsable: bool = True
    campo_responsable: str = CAMPO_RESPONSABLE

    columnas: tuple[str, ...] = ()
    filtros: tuple[Filtro, ...] = ()

    def cumple(self, fila: dict) -> bool:
        if self.flag and not cumple_marca(fila.get(self.flag), self.modo):
            return False
        return all(f.cumple(fila) for f in self.filtros)


@dataclass(frozen=True)
class ConfigResumen:
    hallazgo_id: str
    modelo: str
    escenarios: tuple[Escenario, ...]

    archivo: str

    titulo: str

    campo_grupo: str | None = None

    etiqueta_grupo: str = ""


def filas_de_escenario(filas: Sequence[dict], escenario: Escenario) -> list[dict]:
    return [f for f in filas if escenario.cumple(f)]


def campos_requeridos(escenarios: Sequence[Escenario]) -> dict[str, list[str]]:
    """campo del modelo -> códigos de escenario que dependen de él.

    Son los campos sin los cuales un escenario no puede contar: la bandera y
    los campos de sus filtros.
    """
    requeridos: dict[str, list[str]] = {}
    for escenario in escenarios:
        if escenario.flag:
            requeridos.setdefault(escenario.flag, []).append(escenario.code)
        for filtro in escenario.filtros:
            requeridos.setdefault(filtro.campo, []).append(escenario.code)
    return requeridos


def escenarios_sin_campo(
    filas: Sequence[dict], escenarios: Sequence[Escenario]
) -> dict[str, list[str]]:
    """Campos que los escenarios necesitan y que NO llegaron en las filas.

    Cuando el Excel de detalle trae una cabecera que el importador no
    reconoce, el campo simplemente no existe en la fila: ``fila.get(campo)``
    devuelve ``None``, ``cumple_marca(None)`` es ``False`` y el escenario
    cuenta 0 sin ningún error. Esta función expone ese caso para poder
    avisarlo en la UI en lugar de fallar en silencio.
    """
    if not filas:
        return {}
    presentes = set(filas[0])
    return {
        campo: codes
        for campo, codes in campos_requeridos(escenarios).items()
        if campo not in presentes
    }


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


@dataclass
class FilaGrupo:
    grupo: str

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


_ISO = re.compile(r"^(\d{4})-(\d{2})")
_DMY = re.compile(r"^(\d{1,2})[/-](\d{1,2})[/-](\d{4})")


def mes_de(valor: Any) -> str | None:
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
