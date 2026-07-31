from datetime import datetime, timedelta, date, time
from logic.share.services.dni_vs_user_service import DNIUserService
from logic.share.services.gdh_service import GDHUserService
from logic.share.services.ad_service import ADService
from logic.share.services.tickets_report import TicketInfoService
from models.reports.ad_rows import ADRows

def get_ad_report(fecha_ref: date)-> list[ADRows]:
    dni_user_srv = DNIUserService()
    gdh_user_srv = GDHUserService()
    ad_user_srv = ADService()
    ticket_info_srv = TicketInfoService()

    ahora = datetime.combine(fecha_ref, time.max) 
    limit_90 = timedelta(days=90)
    limit_180 = timedelta(days=180)

    rows = list[ADRows]()
    for ad_user in ad_user_srv.get_all():

        dni_user_info = dni_user_srv.get_by_username(ad_user.usuario)

        dni = dni_user_info.dni if dni_user_info else None
        
        gdh_user = gdh_user_srv.get_by_dni(dni) if dni else None
        ticket_cese = ticket_info_srv.get_by_dni(dni) if dni else None

        escenarios = []
        ces_act:bool = False
        postcese:bool = False
        no_ident:bool = False
        s90d:bool = False
        b180d:bool = False

        if gdh_user and not gdh_user.isActive and gdh_user.isCesado and ad_user.isActive:
            escenarios.append("Cesado Activo")
            ces_act = True

        if gdh_user and not gdh_user.isActive and gdh_user.isCesado:
            if ad_user.last_activity and gdh_user.fecha_cese:
                same_month = gdh_user.fecha_cese.month == fecha_ref.month
                same_year = gdh_user.fecha_cese.year == fecha_ref.year
                
                if same_month and same_year:
                    if ad_user.last_activity > gdh_user.fecha_cese:
                        escenarios.append("Actividad Post Cese")
                        postcese = True

        if dni_user_info and str(dni_user_info.tipo_usuario).upper() == "USUARIO":
            if ad_user.isActive and ad_user.fecha_creacion and ad_user.last_activity:
                create_gt_90 = (ahora - ad_user.fecha_creacion) > limit_90
                login_gt_90 = (ahora - ad_user.last_activity) > limit_90
                if create_gt_90 and login_gt_90:
                    escenarios.append("Sin Actividad 90d")
                    s90d = True
            
            if not ad_user.isActive and ad_user.fecha_creacion and ad_user.last_activity:
                create_gt_180 = (ahora - ad_user.fecha_creacion) > limit_180
                login_gt_180 = (ahora - ad_user.last_activity) > limit_180
                if create_gt_180 and login_gt_180:
                    escenarios.append("Bloqueado 180d")
                    b180d = True

            if ad_user.isActive and not gdh_user:
                escenarios.append("No Identificado")
                no_ident = True

        if ad_user.passwordneverexpires:
            escenarios.append("Contraseña No Expira")
        if ad_user.cannotchangepassword:
            escenarios.append("No Puede Cambiar Contraseña")

        escenarios_str = " + ".join(escenarios)

        rows.append(
            ADRows(
                dominio=ad_user.origen,
                usuario=ad_user.usuario,
                nombre=ad_user.nombre,
                email=ad_user.correo,
                rol=ad_user.rol,
                dni_ad=ad_user.dni,
                dni_dnivsuser=dni_user_info.dni if dni_user_info else "*No esta en DNI vs Usuarios*",
                tipo_dnivsuser=dni_user_info.tipo_usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
                usuario_dnivsuser=dni_user_info.usuario if dni_user_info else "*No esta en DNI vs Usuarios*",
                comentario_dnivsuser=dni_user_info.comentario if dni_user_info else "*No esta en DNI vs Usuarios*",
                descripcion=ad_user.description,
                fecha_creacion=ad_user.fecha_creacion,
                fecha_cambio=ad_user.fecha_cambio,
                passwordneverexpires=ad_user.passwordneverexpires,
                cannotchangepassword=ad_user.cannotchangepassword,
                passwordlastset=ad_user.passwordlastset,
                title=ad_user.title,
                department=ad_user.department,
                company=ad_user.company,
                street_address=ad_user.jefe,
                is_active=ad_user.isActive,
                fecha_ultimo_login_ad=ad_user.fecha_ult_login,
                fecha_ultimo_login_entra=ad_user.ultima_actividad_entra,
                is_activo_gdh= (gdh_user and gdh_user.isActive),
                fecha_alta=gdh_user.fecha_alta if gdh_user else "",
                is_cesado_gdh= (gdh_user and gdh_user.isCesado),
                fecha_cese=gdh_user.fecha_cese if gdh_user else "",
                ticket_cese=ticket_cese.numero_ticket if ticket_cese else "",
                fecha_cierre_ticket_cese=ticket_cese.fecha_cierre if ticket_cese else "",
                escenario=escenarios_str,
                is_cesado_activo=ces_act,
                is_login_post_cese=postcese,
                is_no_identificado=no_ident,
                is_sin_uso_90d=s90d,
                is_deshabilitado_180d=b180d,
            )
        )

    return rows
