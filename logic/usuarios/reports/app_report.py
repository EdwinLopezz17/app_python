from dataclasses import dataclass
from typing import Callable, Any

from logic.share.services.dni_vs_user_service import DNIUserService
from logic.share.services.gdh_service import GDHUserService
from logic.share.services.ad_service import ADService
from logic.share.services.tickets_report import TicketInfoService
from logic.share.services.entraid_service import EntraUserService
from logic.usuarios.services.app_acselx_service import AcselxUserService
from logic.usuarios.services.app_billing_center_service import BillingCenterUserService
from logic.usuarios.services.app_cgweb_service import CgwebUserService
from logic.usuarios.services.app_claim_center_service import ClaimCenterUserService
from logic.usuarios.services.app_contact_manager_service import ContactManagerUserService
from logic.usuarios.services.app_eas_service import EasUserService
from logic.usuarios.services.app_exactus_service import ExactusUserService
from logic.usuarios.services.app_onbase_service import OnbaseUserService
from logic.usuarios.services.app_pms_service import PmsUserService
from logic.usuarios.services.app_policycenter_service import PolicycenterUserService
from logic.usuarios.services.app_segcen_service import SegcenUserService
from logic.usuarios.services.app_sox_vida_service import SoxVidaUserService
from logic.usuarios.services.app_prophet_service import ProphetUserService
from logic.usuarios.services.app_botmaker_service import BotmakerUserService
from logic.usuarios.services.app_salesforce_service import SalesforceUserService
from logic.usuarios.services.app_addactis_service import AddactisUserService
from logic.usuarios.services.app_monokera_service import MonokeraUserService
from logic.usuarios.services.app_siniestros_web_service import SiniestrosWebUserService
from logic.usuarios.services.app_datalake_service import DatalakeUserService
from logic.usuarios.services.app_crm_service import CRMUserService
from logic.usuarios.services.app_qualys_services import QualysUserService
from logic.usuarios.services.app_ssa_service import SsaUserService
from logic.usuarios.services.app_login_service import AppLoginService
from models.reports.app_rows import AppRows

@dataclass
class AppConfig:
    service_factory: Callable[[], Any]
    tipo_app: str
    get_usuario: Callable[[Any], str]
    get_perfil_rol: Callable[[Any], str]
    get_fecha_creacion: Callable[[Any], str]
    get_ultimo_login: Callable[[Any], str]
    clave_duplicados: Callable[[AppRows], Any] = None

    def __post_init__(self):
        if self.clave_duplicados is None:
            # Cambiado para acceder al atributo del dataclass
            self.clave_duplicados = lambda fila: fila.usuario.strip().lower()

_APP_CONFIGS: list[AppConfig] = [
    AppConfig(
        service_factory=AcselxUserService,
        tipo_app="SSA",
        get_usuario= lambda u: u.usuario,
        get_perfil_rol= lambda u: u.codperfil,
        get_fecha_creacion= lambda u: u.fechacrea,
        get_ultimo_login= lambda u: u.fecacceso,
    ),
    AppConfig(
        service_factory=CgwebUserService,
        tipo_app="SSA",
        get_usuario= lambda u: u.usuario,
        get_perfil_rol= lambda u: u.codaplic,
        get_fecha_creacion= lambda u: u.fechacrea,
        get_ultimo_login= lambda u: u.fecacceso,
    ),
    AppConfig(
        service_factory=BillingCenterUserService,
        tipo_app="GW",
        get_usuario= lambda u: u.username,
        get_perfil_rol= lambda u: u.rolename,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=ClaimCenterUserService,
        tipo_app="GW",
        get_usuario= lambda u: u.username,
        get_perfil_rol= lambda u: u.rolename,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=ContactManagerUserService,
        tipo_app="GW",
        get_usuario= lambda u: u.username,
        get_perfil_rol= lambda u: u.rolename,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=PolicycenterUserService,
        tipo_app="GW",
        get_usuario= lambda u: u.username,
        get_perfil_rol= lambda u: u.rolename,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=EasUserService,
        tipo_app="Aplicación",
        get_usuario= lambda u: u.user_id,
        get_perfil_rol= lambda u: u.grupo_id,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: u.fecha_login,
    ),
    AppConfig(
        service_factory=ExactusUserService,
        tipo_app="Aplicación",
        get_usuario=        lambda u: u.usuario,
        get_perfil_rol=     lambda u: "",
        get_fecha_creacion= lambda u: u.createdate,
        get_ultimo_login=   lambda u: "",
    ),
    AppConfig(
        service_factory=OnbaseUserService,
        tipo_app="Aplicación",
        get_usuario= lambda u: u.usuario,
        get_perfil_rol= lambda u: u.grupo_onbase,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: u.ultimo_logueo,
    ),
    AppConfig(
        service_factory=PmsUserService,
        tipo_app="Aplicación",
        get_usuario= lambda u: u.usuario,
        get_perfil_rol= lambda u: u.perfil,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=SegcenUserService,
        tipo_app="SEGCEN",
        get_usuario= lambda u: u.id_usuario,
        get_perfil_rol= lambda u: u.id_rol,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=SoxVidaUserService,
        tipo_app="SEGCEN",
        get_usuario= lambda u: u.id_usuario,
        get_perfil_rol= lambda u: u.cod_rol,
        get_fecha_creacion= lambda u: u.fecha_creacion,
        get_ultimo_login= lambda u: "",
        clave_duplicados=lambda fila: (
            fila.usuario.strip().lower(),
            fila.aplicacion.strip().lower(),
        ),
    ),
    AppConfig(
        service_factory=ProphetUserService,
        tipo_app="-",
        get_usuario= lambda u: u.correo,
        get_perfil_rol= lambda u: "",
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=BotmakerUserService,
        tipo_app="-",
        get_usuario= lambda u: u.email,
        get_perfil_rol= lambda u: u.rol,
        get_fecha_creacion= lambda u: u.registration_date,
        get_ultimo_login= lambda u: u.lastlogin_date,
    ),
    AppConfig(
        service_factory=SalesforceUserService,
        tipo_app="-",
        get_usuario= lambda u: u.id_federacion,
        get_perfil_rol= lambda u: u.perfil,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: u.ult_login,
    ),
    AppConfig(
        service_factory=AddactisUserService,
        tipo_app="-",
        get_usuario= lambda u: u.username,
        get_perfil_rol= lambda u: u.userdomain,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=MonokeraUserService,
        tipo_app="-",
        get_usuario= lambda u: u.correo,
        get_perfil_rol= lambda u: u.rol,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=SiniestrosWebUserService,
        tipo_app="-",
        get_usuario= lambda u: u.acl_entry_name,
        get_perfil_rol= lambda u: u.acl_entry_type,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=DatalakeUserService,
        tipo_app="-",
        get_usuario= lambda u: u.mail,
        get_perfil_rol= lambda u: u.grupo_entra,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=CRMUserService,
        tipo_app="-",
        get_usuario= lambda u: u.mail,
        get_perfil_rol= lambda u: u.grupo_entra,
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
    AppConfig(
        service_factory=QualysUserService,
        tipo_app="-",
        get_usuario= lambda u: u.email,
        get_perfil_rol= lambda u: u.role,
        get_fecha_creacion= lambda u: u.created_at,
        get_ultimo_login= lambda u: u.last_login,
    ),
    AppConfig(
        service_factory=SsaUserService,
        tipo_app="-",
        get_usuario= lambda u: u.usuario,
        get_perfil_rol= lambda u: "",
        get_fecha_creacion= lambda u: "",
        get_ultimo_login= lambda u: "",
    ),
]

def _rows_para_app(
    cfg: AppConfig,
    dni_user_srv, gdh_user_srv, ad_user_srv, ticket_info_srv, app_login_srv,
) -> list[AppRows]:
    service = cfg.service_factory()
    vistos: dict = {}

    for user in service.get_all():
        if not user.isActive:
            continue

        fila = _construir_fila_reporte(
            tipo_app=cfg.tipo_app,
            nombre_app=user.app_name,
            usuario=cfg.get_usuario(user),
            perfil_rol=cfg.get_perfil_rol(user),
            fecha_creacion=cfg.get_fecha_creacion(user),
            ultimo_login=cfg.get_ultimo_login(user),
            dni_user_srv=dni_user_srv,
            gdh_user_srv=gdh_user_srv,
            ad_user_srv=ad_user_srv,
            ticket_info_srv=ticket_info_srv,
            app_login_srv=app_login_srv,
        )

        clave = cfg.clave_duplicados(fila)
        if clave not in vistos:
            vistos[clave] = fila

    return list(vistos.values())

def _construir_fila_reporte(
    tipo_app: str, nombre_app: str, usuario: str, perfil_rol: str,
    fecha_creacion: str, ultimo_login: str,
    dni_user_srv: DNIUserService, gdh_user_srv: GDHUserService,
    ad_user_srv: ADService, ticket_info_srv: TicketInfoService,
    app_login_srv: AppLoginService,
) -> AppRows:
    entra_srv = ad_user_srv.entra_service_instance

    dni_user_info = dni_user_srv.get_by_username(usuario)
    dni = dni_user_info.dni if dni_user_info else None
    usuario_dni = dni_user_info.usuario if dni_user_info else None

    gdh_user = gdh_user_srv.get_by_dni(dni)   if dni else None
    ticket_cese = ticket_info_srv.get_by_dni(dni) if dni else None

    ad_user_pps = ad_user_srv.get_by_dni_and_origen(dni, "PPS")
    dni_pps = None
    ad_user_pps_info = ad_user_srv.get_by_username_and_origen(usuario_dni, "PPS")
    if ad_user_pps_info:
        dni_pps = ad_user_pps_info.dni

    ad_user_vida = ad_user_srv.get_by_dni_and_origen(dni, "VIDA")
    dni_vida = None
    ad_user_vida_info = ad_user_srv.get_by_username_and_origen(usuario_dni, "VIDA")
    if ad_user_vida_info:
        dni_vida = ad_user_vida_info.dni

    user_entraid = entra_srv.get_by_email(usuario) or entra_srv.get_by_upn(usuario)

    escenario_val = ""
    if dni_user_info and dni_user_info.tipo_usuario.upper() not in ["USUARIO"]:
        escenario_val = ""
    elif gdh_user and not gdh_user.isActive and gdh_user.isCesado:
        escenario_val = "Cesado Activo"
    elif not ad_user_pps and not ad_user_vida and ticket_cese:
        escenario_val = "Cesado Activo Ticket"
    elif dni_user_info and not gdh_user and dni_user_info.tipo_usuario.upper() in ["USUARIO"]:
        escenario_val = "No Identificado"

    if not ultimo_login:
        app_login   = app_login_srv.get_by_user_and_app(usuario, nombre_app)
        ultimo_login = app_login.ultimo_logueo if app_login else ""

    return AppRows(
        tipo_aplicacion=tipo_app,
        aplicacion=nombre_app,
        usuario=usuario,
        estado="Activo",
        fecha_creacion=fecha_creacion,
        fecha_ultimo_login=ultimo_login,
        dni=dni_user_info.dni if dni_user_info else "*No esta en DNI vs Usuarios*",
        tipo_usuario_dnivsuser=dni_user_info.tipo_usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
        usuario_dnivsuser=dni_user_info.usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
        comentario_dnivsuser=dni_user_info.comentario if dni_user_info else "*No esta en DNI vs Usuarios*",
        tipo_colaborador=("Proveedor" if gdh_user and gdh_user.esProveedor else ("Planilla" if gdh_user else "")),
        estado_entra_id=("Activo" if user_entraid.isActive else "Bloqueado") if user_entraid else "",
        fecha_creacion_entra_id=user_entraid.fechaCreacion if user_entraid else "",
        fecha_login_entra_id=user_entraid.lastActivityDateTime if user_entraid else "",
        faxnumber_entra_id=user_entraid.dni if user_entraid else "",
        username_ad_pps=ad_user_pps.usuario if ad_user_pps else "*No esta en AD PPS*",
        dni_ad_pps=dni_pps if dni_pps else "*No esta en AD PPS*",
        username_ad_vida=ad_user_vida.usuario if ad_user_vida else "*No esta en AD VIDA*",
        dni_ad_vida=dni_vida if dni_vida else "*No esta en AD VIDA*",
        activo_gdh="Si" if gdh_user and gdh_user.isActive else "No",
        fecha_alta=gdh_user.fecha_alta if gdh_user else "",
        cesado_gdh="Si" if gdh_user and gdh_user.isCesado else "No",
        fecha_cese=gdh_user.fecha_cese if gdh_user else "",
        ticket_cese=ticket_cese.numero_ticket if ticket_cese else "",
        fecha_cierre_ticket_cese=ticket_cese.fecha_cierre if ticket_cese else "",
        escenario=escenario_val,
    )

def get_app_report() -> list[AppRows]:
    dni_user_srv = DNIUserService()
    gdh_user_srv = GDHUserService()
    entraid_srv = EntraUserService()
    ad_user_srv = ADService(entra_service=entraid_srv)
    ticket_info_srv = TicketInfoService()
    app_login_srv = AppLoginService()

    shared_args = (dni_user_srv, gdh_user_srv, ad_user_srv, ticket_info_srv, app_login_srv)

    rows_report = [
        fila
        for cfg in _APP_CONFIGS
        for fila in _rows_para_app(cfg, *shared_args)
    ]

    return rows_report
