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
    passwordneverexpires: str
    cannotchangepassword: str
    passwordlastset: datetime
    title: str
    department: str
    company: str
    street_address: str
    estado: str
    fecha_ultimo_login_ad: datetime
    fecha_ultimo_login_entra: datetime
    activo_gdh: str
    fecha_alta: datetime
    cesado_gdh: str
    fecha_cese: datetime
    ticket_cese: str
    fecha_cierre_ticket_cese: datetime
    escenario: str
    cesado_activo: str
    login_post_cese: str
    no_identificado: str
    sin_uso_90d: str
    deshabilitado_180d: str
    contrasena_no_expira: str
    no_puede_cambiar_contrasena: str
