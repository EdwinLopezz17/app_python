from dataclasses import dataclass
from datetime import datetime

@dataclass
class ADRows:
    dominio: str
    usuario: str
    nombre: str
    email: str
    rol: str
    dni_ad: str
    dni_dnivsuser: str
    tipo_dnivsuser: str
    usuario_dnivsuser: str
    comentario_dnivsuser: str
    descripcion: str
    fecha_creacion: datetime
    fecha_cambio: datetime
    passwordneverexpires: bool
    cannotchangepassword: bool
    passwordlastset: datetime
    title: str
    department: str
    company: str
    street_address: str
    is_active: bool
    fecha_ultimo_login_ad: datetime
    fecha_ultimo_login_entra: datetime
    is_activo_gdh: bool
    fecha_alta: datetime
    is_cesado_gdh: bool
    fecha_cese: datetime
    ticket_cese: str
    fecha_cierre_ticket_cese: datetime
    escenario: str
    is_cesado_activo: bool
    is_login_post_cese: bool
    is_no_identificado: bool
    is_sin_uso_90d: bool
    is_deshabilitado_180d: bool

