"""Cómo se MUESTRA cada campo booleano (tabla, Excel de hallazgos y Excel de
resumen usan este mismo diccionario, así que no se pueden desalinear).

`logic/` devuelve `bool` nativos. El backend del Next.js, en cambio, ya mandaba
el texto final (`"X"`, `"Si"`, `"Activo"`). Esta capa hace esa misma traducción
sin tocar `logic/` ni `models/`.

Es formato de PRESENTACIÓN: el DataFrame que se cachea en Parquet conserva los
`bool` nativos. Los KPIs siguen contando sobre booleanos, no sobre texto.

Tres formatos:

    marca    True -> "X"        False -> ""          sin dato -> ""
    si_no    True -> "SI"       False -> "NO"        sin dato -> ""
    estado   True -> "Activo"   False -> "Inactivo"  sin dato -> ""

El "sin dato" existe de verdad: `logic/` escribe
`is_activo_gdh = (gdh_user and gdh_user.isActive)`, que devuelve `None` cuando
el DNI no aparece en GDH. Eso es un tercer estado, distinto de "No".

--------------------------------------------------------------------------
CÓMO CAMBIAR EL FORMATO DE UN CAMPO
--------------------------------------------------------------------------
Una sola línea en el diccionario del modelo. Por ejemplo, para que
`exist_rol_mr` deje de mostrar SI/NO y pase a X/vacío:

    "ProfileRows": {
        "is_active": ESTADO,
        "exist_rol_mr": MARCA,     # <- antes SI_NO
    },

El cambio se aplica a la vez en la tabla, en el Excel del hallazgo y en el
Excel del resumen. No hay que tocar nada más.
"""

from __future__ import annotations

from typing import Any, Iterable

MARCA = "marca"
SI_NO = "si_no"
ESTADO = "estado"
#: Validaciones de configuración: True = Correcto. El HALLAZGO es el False.
VALIDACION = "validacion"

#: texto para (verdadero, falso). El "sin dato" siempre es cadena vacía.
TEXTOS: dict[str, tuple[str, str]] = {
    MARCA: ("X", ""),
    SI_NO: ("SI", "NO"),
    ESTADO: ("Activo", "Inactivo"),
    VALIDACION: ("Correcto", "Incorrecto"),
}

#: Formatos en los que el hallazgo es el False, no el True. Los KPIs y el
#: resumen consultan esto en vez de tener listas paralelas que se desincronizan.
FORMATOS_INVERTIDOS = {VALIDACION}

VACIO = ""


# ---------------------------------------------------------------------------
# Qué formato usa cada campo de cada modelo
# ---------------------------------------------------------------------------

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
    # GDHRows y GeneralsRow no tienen campos booleanos.
}


#: Red de seguridad: si algún día `models/` agrega un booleano nuevo y nadie
#: lo registra arriba, se muestra como X/vacío en vez de "True"/"False".
PREFIJO_MARCA = "is_"


# ---------------------------------------------------------------------------
# Lectura de valores
# ---------------------------------------------------------------------------

_VERDADEROS = {
    "X", "SI", "SÍ", "TRUE", "VERDADERO", "1", "Y", "YES", "ACTIVO",
    "CORRECTO",
}
_FALSOS = {
    "NO", "FALSE", "FALSO", "0", "N", "INACTIVO", "BLOQUEADO",
    "INCORRECTO",
}


def a_bool(valor: Any) -> bool | None:
    """Tres estados: True, False o None (sin dato).

    Acepta tanto el `bool` nativo que sale de `logic/` como el texto ya
    formateado. Esto último importa porque el resumen vuelve a leer el Excel
    que la propia app exportó: ahí la celda ya dice "X" o "SI", no `True`.
    Así `formatear` es idempotente.
    """
    if valor is None:
        return None
    if isinstance(valor, bool):
        return valor

    try:
        if valor != valor:  # NaN / NaT
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
    """Formato declarado para el campo, o None si no lleva formato especial."""
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
    """Texto ya formateado, o None si el campo no lleva formato.

    None significa "no aplica"; la cadena vacía es un resultado válido (es el
    False de una marca y el sin-dato de todos los formatos).
    """
    fmt = formato(modelo, campo)
    if fmt is None:
        return None
    return texto(valor, fmt)


def campos_formateados(modelo: str | None) -> dict[str, str]:
    return dict(FORMATOS.get(modelo or "", {}))


def contar_verdaderos(valores: Iterable[Any]) -> int:
    """Conteo tolerante para los KPIs: cuenta True, "X", "SI"…"""
    return sum(1 for v in valores if a_bool(v) is True)


def contar_falsos(valores: Iterable[Any]) -> int:
    """Cuenta False, "NO", "Incorrecto"…

    Usa `is False` y no `not`: el sin-dato (None) NO se cuenta como incorrecto.
    Una fila sin rol que validar no es un hallazgo.
    """
    return sum(1 for v in valores if a_bool(v) is False)


def invertido(modelo: str | None, campo: str) -> bool:
    """True si el hallazgo de este campo es el False (validaciones)."""
    return formato(modelo, campo) in FORMATOS_INVERTIDOS


def contar_hallazgos(modelo: str | None, campo: str, valores: Iterable[Any]) -> int:
    """Cuenta las filas que SON hallazgo, según el sentido del campo."""
    if invertido(modelo, campo):
        return contar_falsos(valores)
    return contar_verdaderos(valores)


def check_formatos() -> dict[str, list[str]]:
    """Booleanos de `models/reports/` que no tienen formato declarado.

    Los que empiezan por `is_` caen en la red de seguridad (X/vacío) y no se
    reportan. Cualquier otro booleano nuevo aparecerá aquí para que se decida
    explícitamente si va X/vacío, SI/NO o Activo/Inactivo.
    """
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
