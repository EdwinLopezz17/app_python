from logic.usuarios.services.app_onbase_service import OnbaseUserService
from logic.usuarios.services.app_acselx_service import AcselxUserService
from logic.usuarios.services.app_sox_vida_service import SoxVidaUserService
from logic.usuarios.services.app_eas_service import EasUserService
from logic.usuarios.services.app_billing_center_service import BillingCenterUserService
from logic.usuarios.services.app_claim_center_service import ClaimCenterUserService
from logic.usuarios.services.app_contact_manager_service import ContactManagerUserService
from logic.usuarios.services.app_policycenter_service import PolicycenterUserService
from logic.usuarios.services.app_pms_service import PmsUserService
from logic.usuarios.services.app_prophet_service import ProphetUserService
from logic.usuarios.services.app_salesforce_service import SalesforceUserService
from logic.usuarios.services.app_siniestros_web_service import SiniestrosWebUserService
from logic.usuarios.services.app_exactus_prf_service import ExactusPflService
from logic.usuarios.services.app_botmaker_service import BotmakerUserService
from logic.share.services.mr_service import MatrizRolesService
from logic.share.services.ad_service import ADService
from logic.share.services.dni_vs_user_service import DNIUserService
from logic.share.services.gdh_service import GDHUserService
from logic.share.services.entraid_service import EntraUserService
from logic.usuarios.services.rol_ticket import RolTicketService

from models.reports.profile_rows import ProfileRows

def _construir_fila_reporte(app_name: str, tipo_app:str, usuario: str, perfil_rol: str, 
                            fecha_creacion: str, ultimo_login: str, 
                            dni_user_srv:DNIUserService, gdh_user_srv:GDHUserService,
                            ad_user_srv:ADService, mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                            rol_ticket_srv:RolTicketService
                            ) -> ProfileRows:

    dni_user_info = dni_user_srv.get_by_username(usuario)
    dni = dni_user_info.dni if dni_user_info else None

    rol_ticket_obj = rol_ticket_srv.get_by_dni(dni)
    rol_ticket = rol_ticket_obj.assigned_role if rol_ticket_obj else ""
    ticket = rol_ticket_obj.ticket_number if rol_ticket_obj else ""

    gdh_user = gdh_user_srv.get_by_dni(dni_user_info.dni) if dni_user_info else None

    entra_user = entra_srv.get_by_email(usuario)
    if not entra_user:
        entra_user = entra_srv.get_by_upn(usuario)

    ad_user_pps = ad_user_srv.get_by_dni_and_origen(dni, "PPS")
    ad_user_vida = ad_user_srv.get_by_dni_and_origen(dni, "PVIDA")

    rol_gdh = gdh_user.get_rol() if gdh_user else "*No esta en GDH*"
    rol_final = ""

    if gdh_user and gdh_user.isActive:
        if gdh_user.esProveedor:
            if ad_user_pps and ad_user_vida:
                if ad_user_pps.rol == ad_user_vida.rol:
                    rol_final = ad_user_vida.rol
                else:
                    rol_final = "*[Proveedor] Roles no coinciden en ADs*"
            
            elif ad_user_vida:
                rol_final = ad_user_vida.rol

            elif ad_user_pps:
                rol_final = ad_user_pps.rol
            
        else:
            if ad_user_vida and ad_user_pps:
                if ad_user_pps.rol == ad_user_vida.rol == rol_gdh:
                    rol_final = ad_user_vida.rol
                elif ad_user_pps.rol == ad_user_vida.rol:
                    rol_final = "*Rol GDH no Coincide con ADs*"
                else:
                    rol_final = "*Roles no Coinciden*"

            elif ad_user_vida:
                if ad_user_vida.rol == rol_gdh:
                    rol_final = ad_user_vida.rol
                else:
                    rol_final = "*Rol GDH no coincide con VIDA*"

            elif ad_user_pps:
                if ad_user_pps.rol == rol_gdh:
                    rol_final = ad_user_pps.rol
                else:
                    rol_final = "*Rol GDH difiere con PPS*"
            else:
                rol_final = rol_gdh
    else:
        if ad_user_vida and ad_user_pps:
            if ad_user_vida.rol == ad_user_pps.rol:
                rol_final = ad_user_vida.rol
            else:
                rol_final = "*Roles no coinciden en ADs*"
        elif ad_user_pps:
            rol_final = ad_user_pps.rol

        elif ad_user_vida:
            rol_final = ad_user_vida.rol

    profiles_mr = " | ".join({p.perfil_rol for p in mr_srv.get_by_rol_and_activo(rol_final, app_name)})
    apps_mr = " | ".join({a.nombre_activo for a in mr_srv.get_by_rol_and_perfil(rol_final, perfil_rol)})

    nombre_colaborador_ad = ""
    if ad_user_pps:
        nombre_colaborador_ad = ad_user_pps.nombre

    if ad_user_vida and not nombre_colaborador_ad:
        nombre_colaborador_ad = ad_user_vida.nombre

    return ProfileRows(
        aplicacion=app_name,
        asignacion=tipo_app,
        nombre_colaborador=nombre_colaborador_ad,
        funcion=gdh_user.funcion if gdh_user else "",
        unidad_organizativa=gdh_user.u_organizativa if gdh_user else "",
        servicio=gdh_user.servicio if gdh_user else "",
        usuario=usuario,
        dni=dni_user_info.dni if dni_user_info else "*No esta en DNI vs Usuarios*",
        tipo_dnivsuser=dni_user_info.tipo_usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
        usuario_dnivsuser=dni_user_info.usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
        comentario_dnivsuser=dni_user_info.comentario if dni_user_info else "*No esta en DNI vs Usuarios*",
        is_active=True,
        perfil=perfil_rol,
        fecha_creacion=fecha_creacion,
        fecha_login=ultimo_login,
        fecha_creacion_entra=entra_user.fechaCreacion if entra_user else "",
        fecha_login_entra=entra_user.lastActivityDateTime if entra_user else "",
        estado_entra=("Activo" if entra_user.isActive else "Bloqueado") if entra_user else "",
        dni_entra=entra_user.dni if entra_user else "",
        rol_entra=entra_user.rol if entra_user else "",
        jefatura_entra=entra_user.jefe if entra_user else "",
        tipo_colaborador=gdh_user.calculate_role_type() if gdh_user else "",
        rol_gdh=rol_gdh,
        username_pps=ad_user_pps.usuario if ad_user_pps else "*No esta en AD PPS*",
        rol_ad_pps=ad_user_pps.rol if ad_user_pps else "*No esta en AD PPS*",
        username_vida=ad_user_vida.usuario if ad_user_vida else "*No esta en AD VIDA*",
        rol_ad_vida=ad_user_vida.rol if ad_user_vida else "*No esta en AD VIDA*",
        ticket=ticket,
        rol_ticket=rol_ticket,
        rol_final=rol_final,
        exist_rol_mr=mr_srv.exists_by_rol(rol_final),
        perfil_mr=profiles_mr,
        app_mr=apps_mr,
        val_rol_app=mr_srv.exists_by_rol_and_activo(rol_final, app_name),
        val_rol_app_perfil=mr_srv.exists_by_rol_activo_and_perfil(rol_final, app_name,perfil_rol),
        val_rol_perfil=mr_srv.exists_by_rol_and_perfil(rol_final, perfil_rol),
        escenario="",
        responsable="",
        comentario=""
    )

def _rows_acselx(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                 mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    acselx_srv = AcselxUserService()
    
    rows = []
    
    for user in acselx_srv.get_all():
        if not user.isActive: 
            continue
            
        fila = _construir_fila_reporte(
            app_name = user.app_name,
            tipo_app = "SSA",
            usuario = user.usuario,
            perfil_rol = user.codperfil,
            fecha_creacion = user.fechacrea,
            ultimo_login = user.fecacceso,
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_onbase(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                 mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    onbase_srv = OnbaseUserService()
    
    rows = []
    
    for user_onbase in onbase_srv.get_all():
        if not user_onbase.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_onbase.app_name,
            tipo_app = "Windows (AD)",
            usuario = user_onbase.usuario,
            perfil_rol = user_onbase.grupo_onbase,
            fecha_creacion = "",
            ultimo_login = user_onbase.ultimo_logueo,
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_sox_vida(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                   mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    soxvida_srv = SoxVidaUserService()
    rows = []
    
    for user_sox_vida in soxvida_srv.get_all():
        if not user_sox_vida.isActive:
            continue

        if user_sox_vida.app_name.upper() == "SISTEMA DE PRODUCTOS MÁSIVOS":
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_sox_vida.app_name,
            tipo_app = "Segcen",
            usuario = user_sox_vida.id_usuario,
            perfil_rol = user_sox_vida.cod_rol,
            fecha_creacion = user_sox_vida.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            rol_ticket_srv=rol_ticket_srv,
            entra_srv=entra_srv,
        )
        rows.append(fila)
    
    return rows

def _rows_eas(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
              mr_srv:MatrizRolesService, entra_srv:EntraUserService, rol_ticket_srv:RolTicketService):
    eas_srv = EasUserService()
    rows = []
    
    for user_eas in eas_srv.get_all():
        if not user_eas.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_eas.app_name,
            tipo_app = "Propia",
            usuario = user_eas.user_id,
            perfil_rol = user_eas.grupo_id,
            fecha_creacion = "",
            ultimo_login = user_eas.fecha_login,
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv,
        )
        rows.append(fila)
    
    return rows

def _rows_billing_center(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                         mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    billing_center_srv = BillingCenterUserService()
    rows = []
    
    for user_bc in billing_center_srv.get_all():
        if not user_bc.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_bc.app_name,
            tipo_app = "Propia",
            usuario = user_bc.username,
            perfil_rol = user_bc.rolename,
            fecha_creacion = user_bc.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv,
        )
        rows.append(fila)
    
    return rows

def _rows_claim_center(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                       mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    claim_center_srv = ClaimCenterUserService()
    rows = []
    
    for user_cc in claim_center_srv.get_all():
        if not user_cc.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_cc.app_name,
            tipo_app = "Propia",
            usuario = user_cc.username,
            perfil_rol = user_cc.rolename,
            fecha_creacion = user_cc.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_contact_manager(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                          mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    contact_manager_srv =ContactManagerUserService()
    rows = []
    
    for user_cm in contact_manager_srv.get_all():
        if not user_cm.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_cm.app_name,
            tipo_app = "Propia",
            usuario = user_cm.username,
            perfil_rol = user_cm.rolename,
            fecha_creacion = user_cm.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_policy_center(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                        mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    policy_center_srv = PolicycenterUserService()
    rows = []
    
    for user_pc in policy_center_srv.get_all():
        if not user_pc.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_pc.app_name,
            tipo_app = "Propia",
            usuario = user_pc.username,
            perfil_rol = user_pc.rolename,
            fecha_creacion = user_pc.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_prophet(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                  mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    prophet_srv = ProphetUserService()
    rows = []
    
    for user_prophet in prophet_srv.get_all():
        if not user_prophet.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_prophet.app_name,
            tipo_app = "Propia",
            usuario = user_prophet.correo,
            perfil_rol = "",
            fecha_creacion = "",
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_pms(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
              mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    pms_srv = PmsUserService()
    rows = []
    
    for user_pms in pms_srv.get_all():
        if not user_pms.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_pms.app_name,
            tipo_app = "Propia",
            usuario = user_pms.usuario,
            perfil_rol = user_pms.perfil,
            fecha_creacion ="",
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_salesforce(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                     mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    salesforce_srv = SalesforceUserService()
    rows = []
    
    for user_sf in salesforce_srv.get_all():
        if not user_sf.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_sf.app_name,
            tipo_app = "Propia",
            usuario = user_sf.id_federacion,
            perfil_rol = user_sf.perfil,
            fecha_creacion = "",
            ultimo_login = user_sf.ult_login,
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_siniestros_web(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                         mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    siniestrosweb_srv = SiniestrosWebUserService()
    rows = []
    
    for user_siniestros in siniestrosweb_srv.get_all():
        if not user_siniestros.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_siniestros.app_name,
            tipo_app = "Lotus",
            usuario = user_siniestros.acl_entry_name,
            perfil_rol = user_siniestros.acl_level,
            fecha_creacion = "",
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_exactus(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                  mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    exactus_prf_srv = ExactusPflService()
    rows = []
    
    for user_exactus in exactus_prf_srv.get_all():
        if not user_exactus.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_exactus.app_name,
            tipo_app = "Propia",
            usuario = user_exactus.usuario,
            perfil_rol = user_exactus.grupo,
            fecha_creacion = user_exactus.fecha_creacion,
            ultimo_login = "",
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv
        )
        rows.append(fila)
    
    return rows

def _rows_botmaker(dni_srv:DNIUserService, gdh_srv:GDHUserService, ad_srv:ADService,
                   mr_srv:MatrizRolesService, entra_srv:EntraUserService,
                 rol_ticket_srv:RolTicketService):
    botmaker_srv = BotmakerUserService()
    rows = []
    
    for user_botmaker in botmaker_srv.get_all():
        if not user_botmaker.isActive:
            continue
            
        fila = _construir_fila_reporte(
            app_name = user_botmaker.app_name,
            tipo_app = "Botmaker",
            usuario = user_botmaker.email,
            perfil_rol = user_botmaker.rol,
            fecha_creacion = user_botmaker.registration_date,
            ultimo_login = user_botmaker.lastlogin_date,
            dni_user_srv=dni_srv,
            gdh_user_srv = gdh_srv,
            ad_user_srv = ad_srv,
            mr_srv= mr_srv,
            entra_srv=entra_srv,
            rol_ticket_srv=rol_ticket_srv,
        )
        rows.append(fila)
    
    return rows

def get_profiles_report()-> list[ProfileRows]:
    mr_srv = MatrizRolesService()
    dni_user_srv = DNIUserService()
    gdh_srv = GDHUserService()
    entra_srv = EntraUserService()
    ad_srv = ADService()
    ad_srv.sync_last_activity_entra(entra_srv)
    rol_ticket_srv = RolTicketService()
    
    reporte_total = []

    reporte_total.extend(_rows_acselx(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_onbase(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_sox_vida(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_eas(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_billing_center(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_claim_center(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_contact_manager(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_policy_center(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_prophet(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_pms(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_salesforce(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_siniestros_web(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_exactus(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))
    reporte_total.extend(_rows_botmaker(dni_user_srv, gdh_srv, ad_srv,mr_srv,entra_srv,rol_ticket_srv))

    reporte_total.sort(key=lambda x: str(x.aplicacion).strip().upper())

    return reporte_total
