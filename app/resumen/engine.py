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


ModoResumen = Literal["escenario", "grupo", "poblacion"]


@dataclass(frozen=True)
class Metrica:
    id: str
    label: str
    campo: str
    modo: Literal["conteo", "distinto"] = "conteo"

    def medir(self, filas: Sequence[dict]) -> int:
        presentes = [f for f in filas if tiene_valor(f.get(self.campo))]
        if self.modo == "distinto":
            return len({str(f.get(self.campo)).strip() for f in presentes})
        return len(presentes)


@dataclass(frozen=True)
class BloquePoblacion:
    titulo: str
    valor: str

    metricas: tuple[Metrica, ...]

    hallazgo: tuple[Filtro, ...]

    etiqueta_total: str = "Total"
    etiqueta_hallazgo: str = "# Hallazgos inicial"
    etiqueta_porcentaje: str = "% Hallazgos inicial"

    def es_hallazgo(self, fila: dict) -> bool:
        return all(f.cumple(fila) for f in self.hallazgo)


@dataclass(frozen=True)
class ConfigPoblacion:
    campo_bloque: str
    campo_columna: str
    columnas: tuple[str, ...]
    bloques: tuple[BloquePoblacion, ...]

    codigos_columna: dict[str, str] = field(default_factory=dict)

    def codigo(self, columna: str) -> str:
        return self.codigos_columna.get(columna, columna)


@dataclass(frozen=True)
class ConfigResumen:
    hallazgo_id: str
    modelo: str
    escenarios: tuple[Escenario, ...]

    archivo: str

    titulo: str

    campo_grupo: str | None = None

    etiqueta_grupo: str = ""

    poblacion: ConfigPoblacion | None = None

    columnas_accion: tuple[str, ...] = ()

    @property
    def modo(self) -> ModoResumen:
        if self.poblacion is not None:
            return "poblacion"
        if self.campo_grupo:
            return "grupo"
        return "escenario"


def filas_de_escenario(filas: Sequence[dict], escenario: Escenario) -> list[dict]:
    return [f for f in filas if escenario.cumple(f)]


def campos_requeridos(escenarios: Sequence[Escenario]) -> dict[str, list[str]]:
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


@dataclass
class CeldaPoblacion:
    columna: str
    total: dict[str, int] = field(default_factory=dict)
    hallazgo: dict[str, int] = field(default_factory=dict)

    def porcentaje(self, metrica_id: str) -> float:
        base = self.total.get(metrica_id, 0)
        return self.hallazgo.get(metrica_id, 0) / base if base else 0.0


@dataclass
class BloqueResumen:
    titulo: str
    metricas: tuple[Metrica, ...]
    celdas: list[CeldaPoblacion]

    etiqueta_total: str
    etiqueta_hallazgo: str
    etiqueta_porcentaje: str

    @property
    def total_hallazgos(self) -> int:
        principal = self.metricas[-1].id if self.metricas else ""
        return sum(c.hallazgo.get(principal, 0) for c in self.celdas)


@dataclass
class ResumenPoblacion:
    bloques: list[BloqueResumen]
    total_registros: int

    @property
    def total_hallazgos(self) -> int:
        return sum(b.total_hallazgos for b in self.bloques)


def _filas_de(
    filas: Sequence[dict], campo_bloque: str, valor: str,
    campo_columna: str, columna: str,
) -> list[dict]:
    objetivo_bloque = _norm(valor)
    objetivo_columna = _norm(columna)
    return [
        f for f in filas
        if _norm(f.get(campo_bloque)) == objetivo_bloque
        and _norm(f.get(campo_columna)) == objetivo_columna
    ]


def filas_de_poblacion(
    filas: Sequence[dict], config: ConfigPoblacion,
    bloque: BloquePoblacion, columna: str, solo_hallazgos: bool = False,
) -> list[dict]:
    alcance = _filas_de(
        filas, config.campo_bloque, bloque.valor, config.campo_columna, columna
    )
    if solo_hallazgos:
        return [f for f in alcance if bloque.es_hallazgo(f)]
    return alcance


def por_poblacion(
    filas: Sequence[dict], config: ConfigPoblacion
) -> ResumenPoblacion:
    bloques: list[BloqueResumen] = []

    for bloque in config.bloques:
        celdas: list[CeldaPoblacion] = []
        for columna in config.columnas:
            alcance = filas_de_poblacion(filas, config, bloque, columna)
            hallazgos = [f for f in alcance if bloque.es_hallazgo(f)]
            celdas.append(CeldaPoblacion(
                columna=columna,
                total={m.id: m.medir(alcance) for m in bloque.metricas},
                hallazgo={m.id: m.medir(hallazgos) for m in bloque.metricas},
            ))

        bloques.append(BloqueResumen(
            titulo=bloque.titulo,
            metricas=bloque.metricas,
            celdas=celdas,
            etiqueta_total=bloque.etiqueta_total,
            etiqueta_hallazgo=bloque.etiqueta_hallazgo,
            etiqueta_porcentaje=bloque.etiqueta_porcentaje,
        ))

    return ResumenPoblacion(bloques=bloques, total_registros=len(filas))


def campos_requeridos_poblacion(config: ConfigPoblacion) -> list[str]:
    campos = [config.campo_bloque, config.campo_columna]
    for bloque in config.bloques:
        campos += [m.campo for m in bloque.metricas]
        campos += [f.campo for f in bloque.hallazgo]

    vistos: list[str] = []
    for campo in campos:
        if campo and campo not in vistos:
            vistos.append(campo)
    return vistos


def campos_poblacion_ausentes(
    filas: Sequence[dict], config: ConfigPoblacion
) -> list[str]:
    if not filas:
        return []
    presentes = set(filas[0])
    return [c for c in campos_requeridos_poblacion(config) if c not in presentes]


def escenarios_poblacion_con_hallazgos(
    filas: Sequence[dict], config: ConfigPoblacion
) -> list[tuple[BloquePoblacion, str, list[dict]]]:
    salida: list[tuple[BloquePoblacion, str, list[dict]]] = []
    for bloque in config.bloques:
        for columna in config.columnas:
            hallazgos = filas_de_poblacion(
                filas, config, bloque, columna, solo_hallazgos=True
            )
            if hallazgos:
                salida.append((bloque, columna, hallazgos))
    return salida


_CARACTERES_INVALIDOS = set(r"[]:*?/\\")


def nombre_hoja(titulo: str, codigo: str) -> str:
    crudo = f"{titulo} - {codigo}"
    limpio = "".join(c for c in crudo if c not in _CARACTERES_INVALIDOS)
    return limpio[:31]


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
