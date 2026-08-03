from __future__ import annotations

from app.resumen.engine import ConfigResumen, Escenario, Filtro

COLUMNAS_EDITABLES = ("responsable", "comentario")


_FLAGS_AD = [
    "is_cesado_activo",
    "is_login_post_cese",
    "is_no_identificado",
    "is_sin_uso_90d",
    "is_deshabilitado_180d",
    "passwordneverexpires",
    "cannotchangepassword",
]

_TODAS_AD = [
    "dominio", "usuario", "nombre", "email", "rol", "dni_ad",
    "dni_dnivsuser", "tipo_dnivsuser", "usuario_dnivsuser",
    "comentario_dnivsuser", "descripcion", "fecha_creacion", "fecha_cambio",
    "passwordneverexpires", "cannotchangepassword", "passwordlastset",
    "title", "department", "company", "street_address", "is_active",
    "fecha_ultimo_login_ad", "fecha_ultimo_login_entra", "is_activo_gdh",
    "fecha_alta", "is_cesado_gdh", "fecha_cese", "ticket_cese",
    "fecha_cierre_ticket_cese", "escenario", "is_cesado_activo",
    "is_login_post_cese", "is_no_identificado", "is_sin_uso_90d",
    "is_deshabilitado_180d", "responsable", "comentario",
]


def _todas_salvo_otros_flags(conservar: str) -> tuple[str, ...]:
    return tuple(c for c in _TODAS_AD if c not in _FLAGS_AD or c == conservar)


ESCENARIOS_AD: tuple[Escenario, ...] = (
    Escenario(
        code="H1_AD",
        title="Colaboradores Cesados con cuenta activa",
        flag="is_cesado_activo",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "email", "dni_ad", "dni_dnivsuser",
            "tipo_dnivsuser", "descripcion", "fecha_creacion", "title",
            "is_active", "fecha_ultimo_login_ad", "fecha_ultimo_login_entra",
            "is_cesado_gdh", "fecha_cese", "ticket_cese",
            "fecha_cierre_ticket_cese", "escenario", "responsable", "comentario",
        ),
    ),
    Escenario(
        code="H2_AD",
        title="Usuarios con acceso posterior al cese del empleado",
        flag="is_login_post_cese",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "email", "dni_dnivsuser",
            "tipo_dnivsuser", "descripcion", "fecha_creacion", "title",
            "street_address", "is_active", "fecha_ultimo_login_ad",
            "fecha_ultimo_login_entra", "is_activo_gdh", "fecha_alta",
            "is_cesado_gdh", "fecha_cese", "escenario", "responsable",
            "comentario",
        ),
    ),
    Escenario(
        code="H3_AD",
        title="Usuarios no identificados o sin sustento",
        flag="is_no_identificado",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "dni_ad", "dni_dnivsuser",
            "tipo_dnivsuser", "descripcion", "fecha_creacion", "is_active",
            "fecha_ultimo_login_ad", "fecha_ultimo_login_entra",
            "is_activo_gdh", "is_cesado_gdh", "escenario", "responsable",
            "comentario",
        ),
    ),
    Escenario(
        code="H4_AD",
        title="Identificación de usuarios sin uso más de 90 días de inactividad",
        flag="is_sin_uso_90d",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "email", "dni_ad", "dni_dnivsuser",
            "tipo_dnivsuser", "fecha_creacion", "title", "street_address",
            "is_active", "fecha_ultimo_login_ad", "fecha_ultimo_login_entra",
            "is_activo_gdh", "fecha_alta", "is_cesado_gdh", "fecha_cese",
            "escenario", "responsable", "comentario",
        ),
    ),
    Escenario(
        code="H5_AD",
        title=(
            "Identificación de usuarios deshabilitados más de 6 meses (AD) "
            "que no fueron eliminados"
        ),
        flag="is_deshabilitado_180d",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "email", "dni_ad", "dni_dnivsuser",
            "tipo_dnivsuser", "descripcion", "fecha_creacion", "title",
            "street_address", "is_active", "fecha_ultimo_login_ad",
            "fecha_ultimo_login_entra", "is_activo_gdh", "fecha_alta",
            "is_cesado_gdh", "fecha_cese", "escenario", "responsable",
            "comentario",
        ),
    ),
    Escenario(
        code="H6_AD",
        title="Usuarios con contraseña que no expire",
        flag="passwordneverexpires",
        modo="marca",
        exige_responsable=True,
        columnas=(
            "dominio", "usuario", "nombre", "email", "passwordneverexpires",
            "responsable", "comentario",
        ),
    ),
    Escenario(
        code="H7_AD",
        title="Usuarios que no pueden cambiar su contraseña",
        flag="cannotchangepassword",
        modo="marca",
        exige_responsable=True,
        columnas=_todas_salvo_otros_flags("cannotchangepassword"),
    ),
)


_COLUMNAS_APPS_H1 = (
    "aplicacion", "usuario", "is_active", "fecha_creacion", "fecha_ultimo_login",
    "dni", "tipo_colaborador", "username_ad_pps", "username_ad_vida",
    "estado_entra_id", "fecha_creacion_entra_id", "fecha_login_entra_id",
    "is_activo_gdh", "is_cesado_gdh", "fecha_cese", "ticket_cese",
    "fecha_cierre_ticket_cese", "escenario", "responsable", "comentario",
)


_COLUMNAS_APPS_H2 = tuple(c for c in _COLUMNAS_APPS_H1 if c != "fecha_cese")

ESCENARIOS_APLICACIONES: tuple[Escenario, ...] = (
    Escenario(
        code="H1_APLICACIONES",
        title="Identificación de usuarios cesados",
        columnas=_COLUMNAS_APPS_H1,
        filtros=(
            Filtro("escenario", "contiene", "CESADO ACTIVO"),
            Filtro("escenario", "no_contiene", "CESADO ACTIVO TICKET"),
        ),
    ),
    Escenario(
        code="H2_APLICACIONES",
        title="Identificación de usuarios no identificados o sin sustento",
        columnas=_COLUMNAS_APPS_H2,
        filtros=(Filtro("escenario", "contiene", "NO IDENTIFICADO"),),
    ),
)


CONFIGS: dict[str, ConfigResumen] = {
    "active-directory": ConfigResumen(
        hallazgo_id="active-directory",
        modelo="ADRows",
        escenarios=ESCENARIOS_AD,
        archivo="resumen-hallazgos-active-directory.xlsx",
        titulo="AD",
    ),
    "aplicaciones": ConfigResumen(
        hallazgo_id="aplicaciones",
        modelo="AppRows",
        escenarios=ESCENARIOS_APLICACIONES,
        archivo="Resumen_Aplicaciones.xlsx",
        titulo="APLICACIONES SOX VIDA",
        campo_grupo="aplicacion",
        etiqueta_grupo="Aplicación",
    ),
}
