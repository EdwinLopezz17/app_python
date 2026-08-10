
from __future__ import annotations

from typing import Any, Iterable

MARCA = "marca"
SI_NO = "si_no"
ESTADO = "estado"
VALIDACION = "validacion"

TEXTOS: dict[str, tuple[str, str]] = {
    MARCA: ("X", ""),
    SI_NO: ("SI", "NO"),
    ESTADO: ("Activo", "Inactivo"),
    VALIDACION: ("Correcto", "Incorrecto"),
}

FORMATOS_INVERTIDOS = {VALIDACION}

VACIO = ""


FORMATOS: dict[str, dict[str, str]] = {
    "ADRows": {
        "is_active": ESTADO,
        "is_activo_gdh": SI_NO,
        "is_cesado_gdh": SI_NO,
        "passwordneverexpires": MARCA,
        "cannotchangepassword": MARCA,
        "is_cesado_activo": MARCA,
        "is_login_post_cese": MARCA,
        "is_no_identificado": MARCA,
        "is_sin_uso_90d": MARCA,
        "is_deshabilitado_180d": MARCA,
    },
    "AppRows": {
        "is_active": ESTADO,
        "is_activo_gdh": SI_NO,
        "is_cesado_gdh": SI_NO,
        "is_cesado_activo": MARCA,
        "is_no_identificado": MARCA,
    },
    "ProfileRows": {
        "is_active": ESTADO,
        "exist_rol_mr": SI_NO,
        "val_rol_app": VALIDACION,
        "val_rol_app_perfil": VALIDACION,
        "val_rol_perfil": VALIDACION,
    },
    "DBVidaRow": {
        "is_active": ESTADO,
        "is_activo_gdh": SI_NO,
        "is_cesado_gdh": SI_NO,
        "is_cesado_activo": MARCA,
        "is_login_post_cese": MARCA,
        "is_no_identificado": MARCA,
        "is_sin_uso_90d": MARCA,
        "is_deshabilitado_180d": MARCA,
    },
    "DBGeneralsRow": {
        "is_active": ESTADO,
        "is_activo_gdh": SI_NO,
        "is_cesado_gdh": SI_NO,
        "is_cesado_activo": MARCA,
        "is_login_post_cese": MARCA,
        "is_no_identificado": MARCA,
        "is_sin_uso_90d": MARCA,
        "is_deshabilitado_180d": MARCA,
        "is_no_cesado_oportunamente": MARCA,
    },
}


PREFIJO_MARCA = "is_"


_VERDADEROS = {
    "X", "SI", "SÍ", "TRUE", "VERDADERO", "1", "Y", "YES", "ACTIVO",
    "CORRECTO",
}
_FALSOS = {
    "NO", "FALSE", "FALSO", "0", "N", "INACTIVO", "BLOQUEADO",
    "INCORRECTO",
}


def a_bool(valor: Any) -> bool | None:
    if valor is None:
        return None
    if isinstance(valor, bool):
        return valor

    try:
        if valor != valor:
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(valor, (int, float)):
        return bool(valor)

    texto = str(valor).strip().upper()
    if texto in _VERDADEROS:
        return True
    if texto in _FALSOS:
        return False
    return None


def formato(modelo: str | None, campo: str) -> str | None:
    if not modelo:
        return None
    declarado = FORMATOS.get(modelo, {}).get(campo)
    if declarado:
        return declarado
    if campo.startswith(PREFIJO_MARCA):
        return MARCA
    return None


def texto(valor: Any, fmt: str) -> str:
    verdadero, falso = TEXTOS[fmt]
    estado = a_bool(valor)
    if estado is None:
        return VACIO
    return verdadero if estado else falso


def formatear(modelo: str | None, campo: str, valor: Any) -> str | None:
    fmt = formato(modelo, campo)
    if fmt is None:
        return None
    return texto(valor, fmt)


def campos_formateados(modelo: str | None) -> dict[str, str]:
    return dict(FORMATOS.get(modelo or "", {}))


def contar_verdaderos(valores: Iterable[Any]) -> int:
    return sum(1 for v in valores if a_bool(v) is True)


def contar_falsos(valores: Iterable[Any]) -> int:
    return sum(1 for v in valores if a_bool(v) is False)


def invertido(modelo: str | None, campo: str) -> bool:
    return formato(modelo, campo) in FORMATOS_INVERTIDOS


def contar_hallazgos(modelo: str | None, campo: str, valores: Iterable[Any]) -> int:
    if invertido(modelo, campo):
        return contar_falsos(valores)
    return contar_verdaderos(valores)


def check_formatos() -> dict[str, list[str]]:
    from dataclasses import fields

    from models.reports.ad_rows import ADRows
    from models.reports.app_rows import AppRows
    from models.reports.db_generals_rows import DBGeneralsRow
    from models.reports.db_vida_rows import DBVidaRow
    from models.reports.gdh_rows import GDHRows
    from models.reports.profile_rows import ProfileRows

    reales = {
        "AppRows": AppRows,
        "ADRows": ADRows,
        "ProfileRows": ProfileRows,
        "GDHRows": GDHRows,
        "DBVidaRow": DBVidaRow,
        "DBGeneralsRow": DBGeneralsRow,
    }

    reporte: dict[str, list[str]] = {}
    for nombre, cls in reales.items():
        declarados = FORMATOS.get(nombre, {})
        reporte[nombre] = [
            f.name
            for f in fields(cls)
            if f.type in ("bool", bool)
            and f.name not in declarados
            and not f.name.startswith(PREFIJO_MARCA)
        ]
    return reporte
