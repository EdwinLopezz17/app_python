from dataclasses import dataclass

@dataclass
class DBVidaRow:
    nombre_archivo: str
    username: str
    typee: str
    type_desc: str
    db_name: str
    server_role: str
    database_rol: str
    is_active: bool
    fecha_creacion: str
    fecha_actualizacion: str
    fecha_login: str
    dni: str
    tipo_dnivsuser: str
    usuario_dnivsuser: str
    comentario_dnivsuser: str
    username_ad_pps: str
    dni_ad_pps: str
    username_ad_vida: str
    dni_ad_vida: str
    is_activo_gdh: bool
    fecha_alta: str
    is_cesado_gdh: bool
    fecha_cese: str
    ticket_cese: str
    fecha_cierre_ticket_cese: str
    escenario: str
    is_cesado_activo: bool
    is_login_post_cese: bool
    is_no_identificado: bool
    is_sin_uso_90d: bool
    is_deshabilitado_180d: bool

