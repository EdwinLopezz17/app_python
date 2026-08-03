from __future__ import annotations

APP_ROWS = {
    "tipo_aplicacion": "Tipo de Aplicación",
    "aplicacion": "Aplicación",
    "usuario": "Usuario",
    "is_active": "Activo",
    "fecha_creacion": "Fecha de Creación",
    "fecha_ultimo_login": "Fecha Último Login",
    "dni": "DNI",
    "tipo_usuario_dnivsuser": "Tipo Usuario (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "tipo_colaborador": "Tipo de Colaborador",
    "estado_entra_id": "Estado Entra ID",
    "fecha_creacion_entra_id": "Fecha Creación Entra ID",
    "fecha_login_entra_id": "Fecha Login Entra ID",
    "faxnumber_entra_id": "Fax Number Entra ID",
    "username_ad_pps": "Usuario AD PPS",
    "dni_ad_pps": "DNI AD PPS",
    "username_ad_vida": "Usuario AD Vida",
    "dni_ad_vida": "DNI AD Vida",
    "is_activo_gdh": "Activo GDH",
    "fecha_alta": "Fecha de Alta",
    "is_cesado_gdh": "Cesado GDH",
    "fecha_cese": "Fecha de Cese",
    "ticket_cese": "Ticket de Cese",
    "fecha_cierre_ticket_cese": "Fecha Cierre Ticket",
    "escenario": "Escenario",
    "is_cesado_activo": "Cesado Activo",
    "is_no_identificado": "No Identificado",
    # Columnas que la app exporta vacías para que el usuario las llene en Excel
    # y las devuelva al subir el archivo en «Generar Resumen».
    "responsable": "Responsable",
    "comentario": "Comentario",
}

AD_ROWS = {
    "dominio": "Dominio",
    "usuario": "Usuario",
    "nombre": "Nombre",
    "email": "Correo",
    "rol": "Rol",
    "dni_ad": "DNI AD",
    "dni_dnivsuser": "DNI (DNI vs User)",
    "tipo_dnivsuser": "Tipo (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "descripcion": "Descripción",
    "fecha_creacion": "Fecha de Creación",
    "fecha_cambio": "Fecha de Cambio",
    "passwordneverexpires": "Password No Expira",
    "cannotchangepassword": "No Puede Cambiar Password",
    "passwordlastset": "Último Cambio de Password",
    "title": "Cargo",
    "department": "Departamento",
    "company": "Empresa",
    "street_address": "Dirección",
    "is_active": "Activo",
    "fecha_ultimo_login_ad": "Último Login AD",
    "fecha_ultimo_login_entra": "Último Login Entra",
    "is_activo_gdh": "Activo GDH",
    "fecha_alta": "Fecha de Alta",
    "is_cesado_gdh": "Cesado GDH",
    "fecha_cese": "Fecha de Cese",
    "ticket_cese": "Ticket de Cese",
    "fecha_cierre_ticket_cese": "Fecha Cierre Ticket",
    "escenario": "Escenario",
    "is_cesado_activo": "Cesado Activo",
    "is_login_post_cese": "Login Posterior al Cese",
    "is_no_identificado": "No Identificado",
    "is_sin_uso_90d": "Sin Uso 90 Días",
    "is_deshabilitado_180d": "Deshabilitado 180 Días",
    "responsable": "Responsable",
    "comentario": "Comentario",
}

PROFILE_ROWS = {
    "aplicacion": "Aplicación",
    "asignacion": "Asignación",
    "nombre_colaborador": "Nombre del Colaborador",
    "funcion": "Función",
    "unidad_organizativa": "Unidad Organizativa",
    "servicio": "Servicio",
    "usuario": "Usuario",
    "dni": "DNI",
    "tipo_dnivsuser": "Tipo (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "is_active": "Activo",
    "perfil": "Perfil",
    "fecha_creacion": "Fecha de Creación",
    "fecha_login": "Fecha de Login",
    "fecha_creacion_entra": "Fecha Creación Entra",
    "fecha_login_entra": "Fecha Login Entra",
    "estado_entra": "Estado Entra",
    "dni_entra": "DNI Entra",
    "rol_entra": "Rol Entra",
    "jefatura_entra": "Jefatura Entra",
    "tipo_colaborador": "Tipo de Colaborador",
    "rol_gdh": "Rol GDH",
    "username_pps": "Usuario AD PPS",
    "rol_ad_pps": "Rol AD PPS",
    "username_vida": "Usuario AD Vida",
    "rol_ad_vida": "Rol AD Vida",
    "rol_final": "Rol Final",
    "exist_rol_mr": "Existe Rol en Matriz",
    "perfil_mr": "Perfil en Matriz",
    "app_mr": "Aplicación en Matriz",
    "val_rol_app": "Validación Rol / Aplicación",
    "val_rol_app_perfil": "Validación Rol / Aplicación / Perfil",
    "val_rol_perfil": "Validación Rol / Perfil",
    "escenario": "Escenario",
    "responsable": "Responsable",
    "comentario": "Comentario",
}

GDH_ROWS = {
    "nombre_colaborador": "Nombre del Colaborador",
    "dni": "DNI",
    "sociedad": "Sociedad",
    "cod_funcion": "Código Función",
    "cod_unidad_organizativa": "Código Unidad Organizativa",
    "cod_servicio": "Código Servicio",
    "tipo_dnivsuser": "Tipo (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "tipo_rol": "Tipo de Rol",
    "rol_gdh": "Rol GDH",
    "jefe_gdh": "Jefe GDH",
    "jefe_entra": "Jefe Entra",
    "existe_en_mr": "Existe en Matriz de Roles",
    "username_pps": "Usuario AD PPS",
    "rol_pps": "Rol PPS",
    "dni_pps": "DNI PPS",
    "jefe_pps": "Jefe PPS",
    "username_vida": "Usuario AD Vida",
    "rol_vida": "Rol Vida",
    "dni_vida": "DNI Vida",
    "jefe_vida": "Jefe Vida",
    "validacion_rol": "Validación de Rol",
    "validacion_dni": "Validación de DNI",
}

DB_VIDA_ROW = {
    "nombre_archivo": "Nombre de Archivo",
    "username": "Usuario",
    "typee": "Tipo",
    "type_desc": "Descripción del Tipo",
    "db_name": "Base de Datos",
    "server_role": "Rol de Servidor",
    "database_rol": "Rol de Base de Datos",
    "is_active": "Activo",
    "fecha_creacion": "Fecha de Creación",
    "fecha_actualizacion": "Fecha de Actualización",
    "fecha_login": "Fecha de Login",
    "dni": "DNI",
    "tipo_dnivsuser": "Tipo (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "username_ad_pps": "Usuario AD PPS",
    "dni_ad_pps": "DNI AD PPS",
    "username_ad_vida": "Usuario AD Vida",
    "dni_ad_vida": "DNI AD Vida",
    "is_activo_gdh": "Activo GDH",
    "fecha_alta": "Fecha de Alta",
    "is_cesado_gdh": "Cesado GDH",
    "fecha_cese": "Fecha de Cese",
    "ticket_cese": "Ticket de Cese",
    "fecha_cierre_ticket_cese": "Fecha Cierre Ticket",
    "escenario": "Escenario",
    "is_cesado_activo": "Cesado Activo",
    "is_login_post_cese": "Login Posterior al Cese",
    "is_no_identificado": "No Identificado",
    "is_sin_uso_90d": "Sin Uso 90 Días",
    "is_deshabilitado_180d": "Deshabilitado 180 Días",
}

DB_GENERALS_ROW = {
    "nombre_archivo": "Nombre de Archivo",
    "username": "Usuario",
    "perfil": "Perfil",
    "is_active": "Activo",
    "fecha_bloqueo": "Fecha de Bloqueo",
    "fecha_creacion": "Fecha de Creación",
    "fecha_login": "Fecha de Login",
    "dni": "DNI",
    "tipo_dnivsuser": "Tipo (DNI vs User)",
    "usuario_dnivsuser": "Usuario (DNI vs User)",
    "comentario_dnivsuser": "Comentario (DNI vs User)",
    "username_ad_pps": "Usuario AD PPS",
    "dni_ad_pps": "DNI AD PPS",
    "username_ad_vida": "Usuario AD Vida",
    "dni_ad_vida": "DNI AD Vida",
    "is_activo_gdh": "Activo GDH",
    "fecha_alta": "Fecha de Alta",
    "is_cesado_gdh": "Cesado GDH",
    "fecha_cese": "Fecha de Cese",
    "ticket_cese": "Ticket de Cese",
    "fecha_cierre_ticket_cese": "Fecha Cierre Ticket",
    "escenario": "Escenario",
    "is_cesado_activo": "Cesado Activo",
    "is_login_post_cese": "Login Posterior al Cese",
    "is_no_identificado": "No Identificado",
    "is_sin_uso_90d": "Sin Uso 90 Días",
    "is_deshabilitado_180d": "Deshabilitado 180 Días",
    "is_no_cesado_oportunamente": "No Cesado Oportunamente",
}


GENERALS_ROW = {
    "db": "Base de Datos",
    "cuenta de acceso": "Cuenta de Acceso",
    "host de conexión": "Host de Conexión",
    "terminal": "Terminal",
    "fecha de cierre sesion": "Fecha de Cierre de Sesión",
    "elemento consultado": "Elemento Consultado",
    "cuenta de usuario": "Cuenta de Usuario",
    "fecha accion": "Fecha de Acción",
    "codigo accion": "Código de Acción",
    "jefe chapter lead": "Jefe / Chapter Lead",
    "validacion cuenta de acceso": "Validación Cuenta de Acceso",
    "usuario utilizado": "Usuario Utilizado",
    "validacion usuario utilizado": "Validación Usuario Utilizado",
    "usuario corresponde": "Usuario que Corresponde",
    "validacion usuario corrsponde": "Validación Usuario que Corresponde",
}


MODELOS: dict[str, dict[str, str]] = {
    "AppRows": APP_ROWS,
    "ADRows": AD_ROWS,
    "ProfileRows": PROFILE_ROWS,
    "GDHRows": GDH_ROWS,
    "DBVidaRow": DB_VIDA_ROW,
    "DBGeneralsRow": DB_GENERALS_ROW,
    "GeneralsRow": GENERALS_ROW,
}


def etiquetas(modelo: str) -> dict[str, str]:
    try:
        return MODELOS[modelo]
    except KeyError:
        raise KeyError(f"Modelo sin etiquetas definidas: {modelo!r}") from None


def campos(modelo: str) -> list[str]:
    return list(etiquetas(modelo).keys())


def cabeceras(modelo: str) -> list[str]:
    return list(etiquetas(modelo).values())


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
        etiquetados = campos(nombre)
        reporte[nombre] = {
            "faltan": [c for c in declarados if c not in etiquetados],
            "sobran": [c for c in etiquetados if c not in declarados],
        }
    return reporte
