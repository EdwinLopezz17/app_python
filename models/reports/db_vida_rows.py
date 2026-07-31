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
    estado: str
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
    activo_gdh: str
    fecha_alta: str
    cesado_gdh: str
    fecha_cese: str
    ticket_cese: str
    fecha_cierre_ticket_cese: str
    escenario: str
    cesado_activo: str
    login_post_cese: str
    no_identificado: str
    sin_uso_90d: str
    deshabilitado_180d: str

