from dataclasses import dataclass
from datetime import datetime

@dataclass
class ProfileRows:
    aplicacion: str
    asignacion: str
    nombre_colaborador: str
    funcion: str
    unidad_organizativa: str
    servicio: str
    usuario: str
    dni: str
    tipo_dnivsuser: str
    usuario_dnivsuser: str
    comentario_dnivsuser: str
    is_active: bool
    perfil: str
    fecha_creacion: str
    fecha_login: str
    fecha_creacion_entra: str
    fecha_login_entra: str
    estado_entra: str
    dni_entra: str
    rol_entra: str
    jefatura_entra: str
    sociedad: str
    tipo_colaborador: str
    rol_gdh: str
    fecha_cese: datetime
    username_pps: str
    rol_ad_pps: str
    username_vida: str
    rol_ad_vida: str
    ticket:str
    rol_ticket: str
    rol_final: str
    exist_rol_mr: bool
    perfil_mr: str
    app_mr: str
    val_rol_app: bool
    val_rol_app_perfil: bool
    val_rol_perfil: bool
    escenario: str
    responsable: str
    comentario: str
