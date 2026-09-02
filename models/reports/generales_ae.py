from dataclasses import dataclass
from datetime import datetime

@dataclass
class GeneralesAE:
    db: str
    cuenta_acceso: str
    host_conexion: str
    terminal: str
    fecha_cierre_sesion: str
    elemento_consultado: str
    cuenta_usuario: str
    fecha_accion: str
    codigo_accion: str
    jefe_chapter_lead: str
    val_cuenta_acceso: str
    usuario_utilizado: str
    val_usuario_utilizado: str
    usuario_corresponde: str
    val_usuario_corresponde: str
