from dataclasses import dataclass

@dataclass
class GDHRows:
    nombre_colaborador: str
    dni: str
    sociedad: str
    cod_funcion: str
    cod_unidad_organizativa: str
    cod_servicio: str
    tipo_dnivsuser: str
    usuario_dnivsuser: str
    comentario_dnivsuser: str
    tipo_rol: str
    rol_gdh: str
    jefe_gdh: str
    jefe_entra: str
    existe_en_mr: str
    username_pps: str
    rol_pps: str
    dni_pps: str
    jefe_pps: str
    username_vida: str
    rol_vida: str
    dni_vida: str
    jefe_vida: str
    validacion_rol: str
    validacion_dni: str
    