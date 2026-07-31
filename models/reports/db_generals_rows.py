
from dataclasses import dataclass

@dataclass
class DBGeneralsRow:
    nombre_archivo: str
    username: str
    perfil: str
    estado: str
    fecha_bloqueo: str
    fecha_creacion: str
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
    no_cesado_oportunamente: str
