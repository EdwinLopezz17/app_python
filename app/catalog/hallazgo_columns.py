
from __future__ import annotations

from dataclasses import dataclass

from app.catalog.colors import GRUPO_POR_DEFECTO, GRUPOS, GrupoColor

ANCHO_POR_DEFECTO = 150

PX_POR_CARACTER = 7


@dataclass(frozen=True)
class ColumnDef:
    key: str
    header: str
    group: str = GRUPO_POR_DEFECTO
    width: int = ANCHO_POR_DEFECTO

    @property
    def color(self) -> GrupoColor:
        return GRUPOS.get(self.group, GRUPOS[GRUPO_POR_DEFECTO])

    @property
    def ancho_excel(self) -> float:
        return round(self.width / PX_POR_CARACTER, 1)


Col = ColumnDef


COLUMNAS_ANOTACION = ("responsable", "comentario")


APP_ROWS: list[ColumnDef] = [
    Col("tipo_aplicacion", "Tipo de Aplicación", "C1", 172),
    Col("aplicacion", "Aplicación", "C1", 180),
    Col("usuario", "Usuario", "C1", 120),
    Col("is_active", "Estado", "C1", 110),
    Col("fecha_creacion", "Fecha de Creación", "C1", 150),
    Col("fecha_ultimo_login", "Fecha Último Login", "C1", 150),
    Col("dni", "DNI", "C2", 120),
    Col("tipo_usuario_dnivsuser", "Tipo Usuario (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("tipo_colaborador", "Tipo de Colaborador", "C1", 180),
    Col("estado_entra_id", "Estado Entra ID", "C7", 148),
    Col("fecha_creacion_entra_id", "Fecha Creación Entra ID", "C7", 150),
    Col("fecha_login_entra_id", "Fecha Login Entra ID", "C7", 150),
    Col("faxnumber_entra_id", "Fax Number Entra ID", "C7", 180),
    Col("username_ad_pps", "Usuario AD PPS", "C3", 140),
    Col("dni_ad_pps", "DNI AD PPS", "C3", 120),
    Col("username_ad_vida", "Usuario AD Vida", "C4", 148),
    Col("dni_ad_vida", "DNI AD Vida", "C4", 120),
    Col("is_activo_gdh", "Activo GDH", "C5", 110),
    Col("fecha_alta", "Fecha de Alta", "C5", 150),
    Col("is_cesado_gdh", "Cesado GDH", "C5", 110),
    Col("fecha_cese", "Fecha de Cese", "C5", 150),
    Col("ticket_cese", "Ticket de Cese", "C6", 140),
    Col("fecha_cierre_ticket_cese", "Fecha Cierre Ticket", "C6", 150),
    Col("escenario", "Escenario", "C6", 200),
    Col("is_cesado_activo", "Cesado Activo", "C8", 110),
    Col("is_no_identificado", "No Identificado", "C8", 110),
    Col("responsable", "Responsable", "C6", 180),
    Col("comentario", "Comentario", "C6", 260),
]

AD_ROWS: list[ColumnDef] = [
    Col("dominio", "Dominio", "C1", 120),
    Col("usuario", "Usuario", "C1", 120),
    Col("nombre", "Nombre", "C1", 120),
    Col("email", "Correo", "C1", 120),
    Col("rol", "Rol", "C1", 120),
    Col("dni_ad", "DNI AD", "C1", 120),
    Col("dni_dnivsuser", "DNI (DNI vs User)", "C2", 120),
    Col("tipo_dnivsuser", "Tipo (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("descripcion", "Descripción", "C1", 240),
    Col("fecha_creacion", "Fecha de Creación", "C1", 150),
    Col("fecha_cambio", "Fecha de Cambio", "C1", 150),
    Col("passwordlastset", "Último Cambio de Password", "C1", 228),
    Col("title", "Cargo", "C1", 120),
    Col("department", "Departamento", "C1", 124),
    Col("company", "Empresa", "C1", 120),
    Col("street_address", "Dirección", "C1", 120),
    Col("is_active", "Estado", "C1", 110),
    Col("fecha_ultimo_login_ad", "Último Login AD", "C4", 150),
    Col("fecha_ultimo_login_entra", "Último Login Entra", "C4", 150),
    Col("is_activo_gdh", "Activo GDH", "C5", 110),
    Col("fecha_alta", "Fecha de Alta", "C5", 150),
    Col("is_cesado_gdh", "Cesado GDH", "C5", 110),
    Col("fecha_cese", "Fecha de Cese", "C5", 150),
    Col("ticket_cese", "Ticket de Cese", "C6", 140),
    Col("fecha_cierre_ticket_cese", "Fecha Cierre Ticket", "C6", 150),
    Col("escenario", "Escenario", "C6", 200),
    Col("is_cesado_activo", "Cesado Activo", "C6", 110),
    Col("is_login_post_cese", "Login Posterior al Cese", "C6", 110),
    Col("is_no_identificado", "No Identificado", "C6", 110),
    Col("is_sin_uso_90d", "Sin Uso 90 Días", "C6", 110),
    Col("is_deshabilitado_180d", "Deshabilitado 180 Días", "C6", 110),
    Col("passwordneverexpires", "Password No Expira", "C6", 172),
    Col("cannotchangepassword", "No Puede Cambiar Password", "C6", 228),
    Col("responsable", "Responsable", "C6", 180),
    Col("comentario", "Comentario", "C6", 260),
]

PROFILE_ROWS: list[ColumnDef] = [
    Col("aplicacion", "Aplicación", "C1", 180),
    Col("asignacion", "Asignación", "C1", 120),
    Col("nombre_colaborador", "Nombre del Colaborador", "C1", 220),
    Col("funcion", "Función", "C1", 120),
    Col("unidad_organizativa", "Unidad Organizativa", "C1", 220),
    Col("servicio", "Servicio", "C1", 200),
    Col("usuario", "Usuario", "C1", 120),
    Col("dni", "DNI", "C2", 120),
    Col("tipo_dnivsuser", "Tipo (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("is_active", "Estado", "C1", 110),
    Col("perfil", "Perfil", "C1", 120),
    Col("fecha_creacion", "Fecha de Creación", "C1", 150),
    Col("fecha_login", "Fecha de Login", "C1", 150),
    Col("fecha_creacion_entra", "Fecha Creación Entra", "C7", 150),
    Col("fecha_login_entra", "Fecha Login Entra", "C7", 150),
    Col("estado_entra", "Estado Entra", "C7", 124),
    Col("dni_entra", "DNI Entra", "C7", 120),
    Col("rol_entra", "Rol Entra", "C7", 120),
    Col("jefatura_entra", "Jefatura Entra", "C7", 140),
    Col("tipo_colaborador", "Tipo de Colaborador", "C5", 180),
    Col("rol_gdh", "Rol GDH", "C5", 120),
    Col("username_pps", "Usuario AD PPS", "C3", 140),
    Col("rol_ad_pps", "Rol AD PPS", "C3", 120),
    Col("username_vida", "Usuario AD Vida", "C4", 148),
    Col("rol_ad_vida", "Rol AD Vida", "C4", 120),
    Col("ticket", "Ticket", "C11", 130),
    Col("rol_ticket", "Rol Ticket", "C11", 180),
    Col("rol_final", "Rol Final", "C9", 140),
    Col("exist_rol_mr", "Existe Rol en Matriz", "C10", 110),
    Col("perfil_mr", "Perfil en Matriz", "C10", 156),
    Col("app_mr", "Aplicación en Matriz", "C10", 188),
    Col("val_rol_app", "Validación Rol / Aplicación", "C10", 244),
    Col("val_rol_app_perfil", "Validación Rol / Aplicación / Perfil", "C10", 280),
    Col("val_rol_perfil", "Validación Rol / Perfil", "C10", 212),
    Col("escenario", "Escenario", "C8", 200),
    Col("responsable", "Responsable", "C8", 180),
    Col("comentario", "Comentario", "C8", 260),
]

GDH_ROWS: list[ColumnDef] = [
    Col("nombre_colaborador", "Nombre del Colaborador", "C5", 220),
    Col("dni", "DNI", "C5", 120),
    Col("sociedad", "Sociedad", "C5", 120),
    Col("cod_funcion", "Código Función", "C5", 140),
    Col("cod_unidad_organizativa", "Código Unidad Organizativa", "C5", 236),
    Col("cod_servicio", "Código Servicio", "C5", 148),
    Col("tipo_dnivsuser", "Tipo (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("tipo_rol", "Tipo de Rol", "C5", 120),
    Col("rol_gdh", "Rol GDH", "C5", 120),
    Col("jefe_gdh", "Jefe GDH", "C5", 120),
    Col("jefe_entra", "Jefe Entra", "C5", 120),
    Col("existe_en_mr", "Existe en Matriz de Roles", "C10", 228),
    Col("username_pps", "Usuario AD PPS", "C3", 140),
    Col("rol_pps", "Rol PPS", "C3", 120),
    Col("dni_pps", "DNI PPS", "C3", 120),
    Col("jefe_pps", "Jefe PPS", "C3", 120),
    Col("username_vida", "Usuario AD Vida", "C4", 148),
    Col("rol_vida", "Rol Vida", "C4", 120),
    Col("dni_vida", "DNI Vida", "C4", 120),
    Col("jefe_vida", "Jefe Vida", "C4", 120),
    Col("validacion_rol", "Validación de Rol", "C10", 164),
    Col("validacion_dni", "Validación de DNI", "C10", 120),
]

DB_VIDA_ROW: list[ColumnDef] = [
    Col("nombre_archivo", "Nombre de Archivo", "C1", 200),
    Col("username", "Usuario", "C1", 120),
    Col("typee", "Tipo", "C1", 120),
    Col("type_desc", "Descripción del Tipo", "C1", 188),
    Col("db_name", "Base de Datos", "C1", 132),
    Col("server_role", "Rol de Servidor", "C1", 148),
    Col("database_rol", "Rol de Base de Datos", "C1", 188),
    Col("is_active", "Estado", "C1", 110),
    Col("fecha_creacion", "Fecha de Creación", "C1", 150),
    Col("fecha_actualizacion", "Fecha de Actualización", "C1", 150),
    Col("fecha_login", "Fecha de Login", "C1", 150),
    Col("dni", "DNI", "C2", 120),
    Col("tipo_dnivsuser", "Tipo (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("username_ad_pps", "Usuario AD PPS", "C3", 140),
    Col("dni_ad_pps", "DNI AD PPS", "C3", 120),
    Col("username_ad_vida", "Usuario AD Vida", "C4", 148),
    Col("dni_ad_vida", "DNI AD Vida", "C4", 120),
    Col("is_activo_gdh", "Activo GDH", "C5", 110),
    Col("fecha_alta", "Fecha de Alta", "C5", 150),
    Col("is_cesado_gdh", "Cesado GDH", "C5", 110),
    Col("fecha_cese", "Fecha de Cese", "C5", 150),
    Col("ticket_cese", "Ticket de Cese", "C6", 140),
    Col("fecha_cierre_ticket_cese", "Fecha Cierre Ticket", "C6", 150),
    Col("escenario", "Escenario", "C8", 200),
    Col("is_cesado_activo", "Cesado Activo", "C8", 110),
    Col("is_login_post_cese", "Login Posterior al Cese", "C8", 110),
    Col("is_no_identificado", "No Identificado", "C8", 110),
    Col("is_sin_uso_90d", "Sin Uso 90 Días", "C8", 110),
    Col("is_deshabilitado_180d", "Deshabilitado 180 Días", "C8", 110),
    Col("responsable", "Responsable", "C6", 180),
    Col("comentario", "Comentario", "C6", 260),
]

DB_GENERALS_ROW: list[ColumnDef] = [
    Col("nombre_archivo", "Nombre de Archivo", "C1", 200),
    Col("username", "Usuario", "C1", 120),
    Col("perfil", "Perfil", "C1", 120),
    Col("is_active", "Estado", "C1", 110),
    Col("fecha_bloqueo", "Fecha de Bloqueo", "C1", 150),
    Col("fecha_creacion", "Fecha de Creación", "C1", 150),
    Col("fecha_login", "Fecha de Login", "C1", 150),
    Col("dni", "DNI", "C2", 120),
    Col("tipo_dnivsuser", "Tipo (DNI vs User)", "C2", 120),
    Col("usuario_dnivsuser", "Usuario (DNI vs User)", "C2", 120),
    Col("comentario_dnivsuser", "Comentario (DNI vs User)", "C2", 240),
    Col("username_ad_pps", "Usuario AD PPS", "C3", 140),
    Col("dni_ad_pps", "DNI AD PPS", "C3", 120),
    Col("username_ad_vida", "Usuario AD Vida", "C4", 148),
    Col("dni_ad_vida", "DNI AD Vida", "C4", 120),
    Col("is_activo_gdh", "Activo GDH", "C5", 110),
    Col("fecha_alta", "Fecha de Alta", "C5", 150),
    Col("is_cesado_gdh", "Cesado GDH", "C5", 110),
    Col("fecha_cese", "Fecha de Cese", "C5", 150),
    Col("ticket_cese", "Ticket de Cese", "C6", 140),
    Col("fecha_cierre_ticket_cese", "Fecha Cierre Ticket", "C6", 150),
    Col("escenario", "Escenario", "C8", 200),
    Col("is_cesado_activo", "Cesado Activo", "C8", 110),
    Col("is_login_post_cese", "Login Posterior al Cese", "C8", 110),
    Col("is_no_identificado", "No Identificado", "C8", 110),
    Col("is_sin_uso_90d", "Sin Uso 90 Días", "C8", 110),
    Col("is_deshabilitado_180d", "Deshabilitado 180 Días", "C8", 110),
    Col("is_no_cesado_oportunamente", "No Cesado Oportunamente", "C8", 110),
    Col("responsable", "Responsable", "C6", 180),
    Col("comentario", "Comentario", "C6", 260),
]

GENERALS_ROW: list[ColumnDef] = [
    Col("db", "Base de Datos", "C1", 132),
    Col("cuenta de acceso", "Cuenta de Acceso", "C1", 156),
    Col("host de conexión", "Host de Conexión", "C1", 156),
    Col("terminal", "Terminal", "C1", 120),
    Col("fecha de cierre sesion", "Fecha de Cierre de Sesión", "C1", 150),
    Col("elemento consultado", "Elemento Consultado", "C1", 180),
    Col("cuenta de usuario", "Cuenta de Usuario", "C1", 164),
    Col("fecha accion", "Fecha de Acción", "C1", 150),
    Col("codigo accion", "Código de Acción", "C1", 156),
    Col("jefe chapter lead", "Jefe / Chapter Lead", "C5", 180),
    Col("validacion cuenta de acceso", "Validación Cuenta de Acceso", "C10", 244),
    Col("usuario utilizado", "Usuario Utilizado", "C1", 164),
    Col("validacion usuario utilizado", "Validación Usuario Utilizado", "C10", 252),
    Col("usuario corresponde", "Usuario que Corresponde", "C1", 212),
    Col("validacion usuario corrsponde", "Validación Usuario que Corresponde", "C10", 280),
]


COLUMNAS: dict[str, list[ColumnDef]] = {
    "AppRows": APP_ROWS,
    "ADRows": AD_ROWS,
    "ProfileRows": PROFILE_ROWS,
    "GDHRows": GDH_ROWS,
    "DBVidaRow": DB_VIDA_ROW,
    "DBGeneralsRow": DB_GENERALS_ROW,
    "GeneralsRow": GENERALS_ROW,
}


def columnas(modelo: str | None) -> list[ColumnDef]:
    if not modelo:
        return []
    try:
        return COLUMNAS[modelo]
    except KeyError:
        raise KeyError(f"Modelo sin columnas definidas: {modelo!r}") from None


def por_campo(modelo: str | None) -> dict[str, ColumnDef]:
    return {c.key: c for c in columnas(modelo)}


def etiquetas(modelo: str | None) -> dict[str, str]:
    return {c.key: c.header for c in columnas(modelo)}


def campos(modelo: str | None) -> list[str]:
    return [c.key for c in columnas(modelo)]


def cabeceras(modelo: str | None) -> list[str]:
    return [c.header for c in columnas(modelo)]


def definicion(modelo: str | None, campo: str) -> ColumnDef:
    return por_campo(modelo).get(campo) or ColumnDef(campo, campo)


def grupo(modelo: str | None, campo: str) -> GrupoColor:
    return definicion(modelo, campo).color


def ancho(modelo: str | None, campo: str) -> int:
    return definicion(modelo, campo).width


def ordenar(modelo: str | None, presentes: list[str]) -> list[str]:
    declarados = [c.key for c in columnas(modelo) if c.key in presentes]
    return declarados + [c for c in presentes if c not in set(declarados)]


def check_modelos() -> dict[str, dict[str, list[str]]]:
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

    reporte: dict[str, dict[str, list[str]]] = {}
    for nombre, cls in reales.items():
        declarados = [f.name for f in fields(cls)]
        registrados = campos(nombre)
        reporte[nombre] = {
            "faltan": [c for c in declarados if c not in registrados],
            "sobran": [
                c for c in registrados
                if c not in declarados and c not in COLUMNAS_ANOTACION
            ],
        }
    return reporte


# ---------------------------------------------------------------------------
# Alias de importación
#
# El Excel de detalle que se lee para armar el resumen puede venir del
# frontend Next.js (nextjs-laboratorio, src/features/bd/bd-columns.ts), cuyas
# cabeceras NO son idénticas a las de esta app: "Fecha Cese" vs "Fecha de
# Cese", "Type Desc" vs "Descripción del Tipo", "Sin Uso 90d" vs "Sin Uso 90
# Días"...
#
# Sin estos alias el importador no reconoce las columnas de flags, todos los
# escenarios cuentan 0 y el resumen sale vacío. Las cadenas de abajo están
# copiadas TAL CUAL de bd-columns.ts: si allá cambia una cabecera, hay que
# reflejarlo aquí.
# ---------------------------------------------------------------------------

_ALIAS_BD_COMUN: dict[str, tuple[str, ...]] = {
    "nombre_archivo": ("Nombre Archivo",),
    "username": ("Usuario", "Userame"),
    "fecha_creacion": ("Fecha Creación",),
    "fecha_login": ("Fecha Login",),
    "username_ad_pps": ("Username AD PPS",),
    "username_ad_vida": ("Username AD VIDA",),
    "fecha_alta": ("Fecha Alta",),
    "fecha_cese": ("Fecha Cese",),
    "ticket_cese": ("Ticket Cese",),
    "fecha_cierre_ticket_cese": ("Fecha Cierre Ticket Cese",),
    "is_cesado_activo": ("Cesado Activo",),
    "is_login_post_cese": ("Login Post Cese",),
    "is_no_identificado": ("No Identificado",),
    "is_sin_uso_90d": ("Sin Uso 90d",),
    "is_deshabilitado_180d": ("Deshabilitado 180d",),
}

ALIAS_IMPORTACION: dict[str, dict[str, tuple[str, ...]]] = {
    "DBVidaRow": {
        **_ALIAS_BD_COMUN,
        "typee": ("Type",),
        "type_desc": ("Type Desc",),
        "db_name": ("DB Name",),
        "server_role": ("Server Role",),
        "database_rol": ("DB Role",),
        "fecha_actualizacion": ("Fecha Actualización", "Fecha Actualizacion"),
    },
    "DBGeneralsRow": {
        **_ALIAS_BD_COMUN,
        "fecha_bloqueo": ("Fecha Bloqueo",),
        "is_no_cesado_oportunamente": ("No Cesado Oportunamente",),
    },
}


def alias(modelo: str | None) -> dict[str, tuple[str, ...]]:
    """Cabeceras alternativas aceptadas al importar, por campo."""
    return ALIAS_IMPORTACION.get(modelo or "", {})
