from dataclasses import dataclass
from datetime import datetime

@dataclass
class AppRows:
    tipo_aplicacion: str
    aplicacion: str
    usuario: str
    is_active: bool
    fecha_creacion: datetime
    fecha_ultimo_login: datetime
    dni: str
    tipo_usuario_dnivsuser: str
    usuario_dnivsuser: str
    comentario_dnivsuser: str
    sociedad: str
    tipo_colaborador: str
    estado_entra_id: str
    fecha_creacion_entra_id: datetime
    fecha_login_entra_id: datetime
    faxnumber_entra_id: str
    username_ad_pps: str
    dni_ad_pps: str
    username_ad_vida: str
    dni_ad_vida: str
    is_activo_gdh: bool
    fecha_alta: str
    is_cesado_gdh: bool
    fecha_cese: datetime
    ticket_cese: str
    fecha_cierre_ticket_cese: str
    escenario: str
    is_cesado_activo: bool
    is_no_identificado: bool
