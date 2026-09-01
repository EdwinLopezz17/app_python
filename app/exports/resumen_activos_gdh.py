from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Sequence

import pandas as pd

TIPO_PLANILLA = "Planilla"
TIPO_FFVV = "FFVV"
TIPO_PROVEEDOR = "Proveedor"

SOCIEDADES: tuple[str, ...] = ("PACIFICO CIA SEG Y REASEG", "Pacifico SA EPS")

K_TIPO_ROL = "tipo_rol"
K_SOCIEDAD = "sociedad"
K_ROL_GDH = "rol_gdh"
K_DNI = "dni"
K_VALIDACION_ROL = "validacion_rol"
K_USER_PPS = "username_pps"
K_USER_VIDA = "username_vida"

MARCA_NO_EXISTE_AD = "no existe en ad"


def _norm(valor: Any) -> str:
    return str(valor if valor is not None and valor == valor else "").strip().lower()


def _tiene_valor(valor: Any) -> bool:
    return str(valor if valor is not None and valor == valor else "").strip() != ""


def _es_no_existe_ad(valor: Any) -> bool:
    return MARCA_NO_EXISTE_AD in _norm(valor)


def _es_proveedor(tipo_rol: Any) -> bool:
    return _norm(tipo_rol) == _norm(TIPO_PROVEEDOR)


def es_hallazgo(fila: dict) -> bool:
    if _es_proveedor(fila.get(K_TIPO_ROL)):
        return _es_no_existe_ad(fila.get(K_USER_PPS)) and _es_no_existe_ad(
            fila.get(K_USER_VIDA)
        )
    return _tiene_valor(fila.get(K_VALIDACION_ROL))


def filas_de_escenario(
    filas: Sequence[dict], tipo_rol: str, sociedad: str
) -> list[dict]:
    objetivo_tipo = _norm(tipo_rol)
    objetivo_soc = _norm(sociedad)
    return [
        f
        for f in filas
        if _norm(f.get(K_TIPO_ROL)) == objetivo_tipo
        and _norm(f.get(K_SOCIEDAD)) == objetivo_soc
    ]


def filas_hallazgo(filas: Sequence[dict], tipo_rol: str, sociedad: str) -> list[dict]:
    return [f for f in filas_de_escenario(filas, tipo_rol, sociedad) if es_hallazgo(f)]


def _roles_distintos(filas: Sequence[dict]) -> int:
    return len({str(f.get(K_ROL_GDH, "")).strip() for f in filas if _tiene_valor(f.get(K_ROL_GDH))})


def _con_dni(filas: Sequence[dict]) -> int:
    return sum(1 for f in filas if _tiene_valor(f.get(K_DNI)))


@dataclass(frozen=True)
class RolUsuario:
    roles: int = 0
    usuarios: int = 0


@dataclass(frozen=True)
class BloqueSociedad:
    sociedad: str
    reporte: RolUsuario
    hallazgos: RolUsuario

    @property
    def pct_roles(self) -> float:
        return self.hallazgos.roles / self.reporte.roles if self.reporte.roles else 0.0

    @property
    def pct_usuarios(self) -> float:
        return (
            self.hallazgos.usuarios / self.reporte.usuarios
            if self.reporte.usuarios
            else 0.0
        )


@dataclass(frozen=True)
class BloqueReporte:
    titulo: str
    sociedades: list[BloqueSociedad] = field(default_factory=list)


@dataclass(frozen=True)
class BloqueProveedor:
    sociedad: str
    cuenta_dni: int
    no_existen_ad: int

    @property
    def pct(self) -> float:
        return self.no_existen_ad / self.cuenta_dni if self.cuenta_dni else 0.0


@dataclass(frozen=True)
class ResumenActivosGdh:
    reporte_gdh: list[BloqueReporte] = field(default_factory=list)
    proveedores: list[BloqueProveedor] = field(default_factory=list)


def _bloque(filas: Sequence[dict], titulo: str, tipo_rol: str) -> BloqueReporte:
    sociedades: list[BloqueSociedad] = []
    for sociedad in SOCIEDADES:
        del_escenario = filas_de_escenario(filas, tipo_rol, sociedad)
        hallazgos = [f for f in del_escenario if es_hallazgo(f)]
        sociedades.append(
            BloqueSociedad(
                sociedad=sociedad,
                reporte=RolUsuario(
                    roles=_roles_distintos(del_escenario),
                    usuarios=_con_dni(del_escenario),
                ),
                hallazgos=RolUsuario(
                    roles=_roles_distintos(hallazgos),
                    usuarios=_con_dni(hallazgos),
                ),
            )
        )
    return BloqueReporte(titulo=titulo, sociedades=sociedades)


def calcular(filas: Sequence[dict]) -> ResumenActivosGdh:
    proveedores: list[BloqueProveedor] = []
    for sociedad in SOCIEDADES:
        del_escenario = filas_de_escenario(filas, TIPO_PROVEEDOR, sociedad)
        proveedores.append(
            BloqueProveedor(
                sociedad=sociedad,
                cuenta_dni=_con_dni(del_escenario),
                no_existen_ad=sum(1 for f in del_escenario if es_hallazgo(f)),
            )
        )

    return ResumenActivosGdh(
        reporte_gdh=[
            _bloque(filas, "PLANILLA", TIPO_PLANILLA),
            _bloque(filas, "FFVV", TIPO_FFVV),
        ],
        proveedores=proveedores,
    )


def desde_dataframe(df: pd.DataFrame) -> list[dict]:
    if df is None or df.empty:
        return []
    return df.to_dict("records")


def escenarios_con_hallazgos(filas: Sequence[dict]) -> list[tuple[str, str, list[dict]]]:
    salida: list[tuple[str, str, list[dict]]] = []
    for tipo_rol in (TIPO_PLANILLA, TIPO_FFVV, TIPO_PROVEEDOR):
        for sociedad in SOCIEDADES:
            hallazgos = filas_hallazgo(filas, tipo_rol, sociedad)
            if hallazgos:
                salida.append((tipo_rol, sociedad, hallazgos))
    return salida


CODIGO_SOCIEDAD = {
    "PACIFICO CIA SEG Y REASEG": "CIA SEG",
    "Pacifico SA EPS": "SA EPS",
}

_INVALIDOS = set(r"[]:*?/\\")


def nombre_hoja(tipo_rol: str, sociedad: str) -> str:
    codigo = CODIGO_SOCIEDAD.get(sociedad, sociedad)
    crudo = f"{tipo_rol} - {codigo}"
    limpio = "".join(c for c in crudo if c not in _INVALIDOS)
    return limpio[:31]
