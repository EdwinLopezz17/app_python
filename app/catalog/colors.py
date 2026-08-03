"""Grupos de color de las cabeceras de los hallazgos.

Port literal de `src/lib/theme.ts` del front Next.js: los mismos hex, los mismos
identificadores C1–C10 y el mismo criterio (el color indica el ORIGEN del dato,
no su tipo). Se usan idénticos en la tabla de la app y en el Excel exportado,
igual que allá.

    C1  Aplicación / origen        C6  Ticket Cese
    C2  DNI vs Usuario             C7  Estado Entra ID
    C3  AD PPS                     C8  Escenarios
    C4  AD VIDA                    C9  Rol Final (Perfiles)
    C5  GDH                        C10 Matriz de Roles (Perfiles)

El mapeo por modelo traduce los `key` del front (que son las cabeceras del JSON
del backend) a los nombres de campo de `models/reports/*` que usa esta app.
Cualquier campo sin mapear cae en C1.
"""

from __future__ import annotations

from dataclasses import dataclass

# Paleta (idéntica a `palette` en lib/theme.ts).
SURFACE_CONTAINER_HIGH = "#e2e7ff"
ON_SURFACE = "#131b2e"
INVERSE_SURFACE = "#283044"
OUTLINE = "#6e7880"
PRIMARY = "#006386"
SECONDARY = "#006d38"
TERTIARY = "#964400"
ERROR = "#ba1a1a"


@dataclass(frozen=True)
class GrupoColor:
    id: str
    label: str
    fill: str
    text: str


GRUPOS: dict[str, GrupoColor] = {
    "C1": GrupoColor("C1", "Aplicación", PRIMARY, "#ffffff"),
    "C2": GrupoColor("C2", "DNI vs Usuario", SECONDARY, "#ffffff"),
    "C3": GrupoColor("C3", "AD PPS", TERTIARY, "#ffffff"),
    "C4": GrupoColor("C4", "AD VIDA", INVERSE_SURFACE, "#ffffff"),
    "C5": GrupoColor("C5", "GDH", OUTLINE, "#ffffff"),
    "C6": GrupoColor("C6", "Ticket Cese", ERROR, "#ffffff"),
    "C7": GrupoColor("C7", "Estado Entra ID", ON_SURFACE, "#ffffff"),
    "C8": GrupoColor("C8", "Escenarios", "#bc5800", "#ffffff"),
    "C9": GrupoColor("C9", "Rol Final", "#8a5a00", "#ffffff"),
    "C10": GrupoColor("C10", "Matriz de Roles", "#3f6212", "#ffffff"),
}

GRUPO_POR_DEFECTO = "C1"


# ── AppRows · features/usuarios/hallazgos/aplicaciones/columns.ts ───────────
APP_ROWS = {
    "tipo_aplicacion": "C1",
    "aplicacion": "C1",
    "usuario": "C1",
    "is_active": "C1",
    "fecha_creacion": "C1",
    "fecha_ultimo_login": "C1",
    "dni": "C2",
    "tipo_usuario_dnivsuser": "C2",
    "usuario_dnivsuser": "C2",
    "comentario_dnivsuser": "C2",
    "tipo_colaborador": "C1",
    "estado_entra_id": "C7",
    "fecha_creacion_entra_id": "C7",
    "fecha_login_entra_id": "C7",
    "faxnumber_entra_id": "C7",
    "username_ad_pps": "C3",
    "dni_ad_pps": "C3",
    "username_ad_vida": "C4",
    "dni_ad_vida": "C4",
    "is_activo_gdh": "C5",
    "fecha_alta": "C5",
    "is_cesado_gdh": "C5",
    "fecha_cese": "C5",
    "ticket_cese": "C6",
    "fecha_cierre_ticket_cese": "C6",
    "escenario": "C6",
    "is_cesado_activo": "C8",
    "is_no_identificado": "C8",
    "responsable": "C6",
    "comentario": "C6",
}

# ── ADRows · features/usuarios/hallazgos/active-directory/ad-columns.ts ─────
AD_ROWS = {
    "dominio": "C1",
    "usuario": "C1",
    "nombre": "C1",
    "email": "C1",
    "rol": "C1",
    "dni_ad": "C1",
    "dni_dnivsuser": "C2",
    "tipo_dnivsuser": "C2",
    "usuario_dnivsuser": "C2",
    "comentario_dnivsuser": "C2",
    "descripcion": "C1",
    "fecha_creacion": "C1",
    "fecha_cambio": "C1",
    "passwordneverexpires": "C3",
    "cannotchangepassword": "C3",
    "passwordlastset": "C3",
    "title": "C1",
    "department": "C1",
    "company": "C1",
    "street_address": "C1",
    "is_active": "C1",
    "fecha_ultimo_login_ad": "C4",
    "fecha_ultimo_login_entra": "C4",
    "is_activo_gdh": "C5",
    "fecha_alta": "C5",
    "is_cesado_gdh": "C5",
    "fecha_cese": "C5",
    "ticket_cese": "C6",
    "fecha_cierre_ticket_cese": "C6",
    "escenario": "C6",
    "is_cesado_activo": "C6",
    "is_login_post_cese": "C6",
    "is_no_identificado": "C6",
    "is_sin_uso_90d": "C6",
    "is_deshabilitado_180d": "C6",
    "responsable": "C6",
    "comentario": "C6",
}

# ── ProfileRows · features/perfiles/perfiles-columns.ts ─────────────────────
PROFILE_ROWS = {
    "aplicacion": "C1",
    "asignacion": "C1",
    "nombre_colaborador": "C1",
    "funcion": "C1",
    "unidad_organizativa": "C1",
    "servicio": "C1",
    "usuario": "C1",
    "dni": "C2",
    "tipo_dnivsuser": "C2",
    "usuario_dnivsuser": "C2",
    "comentario_dnivsuser": "C2",
    "is_active": "C1",
    "perfil": "C1",
    "fecha_creacion": "C1",
    "fecha_login": "C1",
    "fecha_creacion_entra": "C7",
    "fecha_login_entra": "C7",
    "estado_entra": "C7",
    "dni_entra": "C7",
    "rol_entra": "C7",
    "jefatura_entra": "C7",
    "tipo_colaborador": "C5",
    "rol_gdh": "C5",
    "username_pps": "C3",
    "rol_ad_pps": "C3",
    "username_vida": "C4",
    "rol_ad_vida": "C4",
    "rol_final": "C9",
    "exist_rol_mr": "C10",
    "perfil_mr": "C10",
    "app_mr": "C10",
    "val_rol_app": "C10",
    "val_rol_app_perfil": "C10",
    "val_rol_perfil": "C10",
    "escenario": "C8",
    "responsable": "C8",
    "comentario": "C8",
}

# ── GDHRows · features/perfiles/activos-gdh/columns.ts ──────────────────────
GDH_ROWS = {
    "nombre_colaborador": "C5",
    "dni": "C5",
    "sociedad": "C5",
    "cod_funcion": "C5",
    "cod_unidad_organizativa": "C5",
    "cod_servicio": "C5",
    "tipo_dnivsuser": "C2",
    "usuario_dnivsuser": "C2",
    "comentario_dnivsuser": "C2",
    "tipo_rol": "C5",
    "rol_gdh": "C5",
    "jefe_gdh": "C5",
    "jefe_entra": "C5",
    "existe_en_mr": "C10",
    "username_pps": "C3",
    "rol_pps": "C3",
    "dni_pps": "C3",
    "jefe_pps": "C3",
    "username_vida": "C4",
    "rol_vida": "C4",
    "dni_vida": "C4",
    "jefe_vida": "C4",
    "validacion_rol": "C10",
    "validacion_dni": "C10",
}

# ── DBVidaRow / DBGeneralsRow · features/bd/bd-columns.ts ──────────────────
_BD_COMUN = {
    "dni": "C2",
    "tipo_dnivsuser": "C2",
    "usuario_dnivsuser": "C2",
    "comentario_dnivsuser": "C2",
    "username_ad_pps": "C3",
    "dni_ad_pps": "C3",
    "username_ad_vida": "C4",
    "dni_ad_vida": "C4",
    "is_activo_gdh": "C5",
    "fecha_alta": "C5",
    "is_cesado_gdh": "C5",
    "fecha_cese": "C5",
    "ticket_cese": "C6",
    "fecha_cierre_ticket_cese": "C6",
    "escenario": "C8",
    "is_cesado_activo": "C8",
    "is_login_post_cese": "C8",
    "is_no_identificado": "C8",
    "is_sin_uso_90d": "C8",
    "is_deshabilitado_180d": "C8",
    "is_no_cesado_oportunamente": "C8",
}

DB_VIDA_ROW = {
    "nombre_archivo": "C1",
    "username": "C1",
    "typee": "C1",
    "type_desc": "C1",
    "db_name": "C1",
    "server_role": "C1",
    "database_rol": "C1",
    "is_active": "C1",
    "fecha_creacion": "C1",
    "fecha_actualizacion": "C1",
    "fecha_login": "C1",
    **_BD_COMUN,
}

DB_GENERALS_ROW = {
    "nombre_archivo": "C1",
    "username": "C1",
    "perfil": "C1",
    "is_active": "C1",
    "fecha_bloqueo": "C1",
    "fecha_creacion": "C1",
    "fecha_login": "C1",
    **_BD_COMUN,
}

# ── GeneralsRow ────────────────────────────────────────────────────────────
# En el front este set está marcado como esqueleto (TODO), así que aquí se
# mapea por origen del dato: acceso/consulta en C1, jefatura en C5 y las tres
# validaciones en C10.
GENERALS_ROW = {
    "db": "C1",
    "cuenta de acceso": "C1",
    "host de conexión": "C1",
    "terminal": "C1",
    "fecha de cierre sesion": "C1",
    "elemento consultado": "C1",
    "cuenta de usuario": "C1",
    "fecha accion": "C1",
    "codigo accion": "C1",
    "jefe chapter lead": "C5",
    "validacion cuenta de acceso": "C10",
    "usuario utilizado": "C1",
    "validacion usuario utilizado": "C10",
    "usuario corresponde": "C1",
    "validacion usuario corrsponde": "C10",
}


GRUPOS_POR_MODELO: dict[str, dict[str, str]] = {
    "AppRows": APP_ROWS,
    "ADRows": AD_ROWS,
    "ProfileRows": PROFILE_ROWS,
    "GDHRows": GDH_ROWS,
    "DBVidaRow": DB_VIDA_ROW,
    "DBGeneralsRow": DB_GENERALS_ROW,
    "GeneralsRow": GENERALS_ROW,
}


def grupo(modelo: str | None, campo: str) -> GrupoColor:
    """Grupo de color de una columna. Sin modelo o sin mapeo devuelve C1."""
    mapa = GRUPOS_POR_MODELO.get(modelo or "", {})
    return GRUPOS[mapa.get(campo, GRUPO_POR_DEFECTO)]


def check_mapeos() -> dict[str, list[str]]:
    """Campos con etiqueta en display.py pero sin grupo de color asignado."""
    from app.catalog import display

    reporte: dict[str, list[str]] = {}
    for modelo, etiquetas in display.MODELOS.items():
        mapa = GRUPOS_POR_MODELO.get(modelo, {})
        reporte[modelo] = [c for c in etiquetas if c not in mapa]
    return reporte
