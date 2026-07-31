from datetime import datetime, timedelta, date, time
from logic.base_datos.services.db_generales_service import DBGeneralesService
from logic.base_datos.services.db_vida_service import DBVidaService
from logic.share.services.dni_vs_user_service import DNIUserService
from logic.share.services.ad_service import ADService
from logic.share.services.gdh_service import GDHUserService
from logic.share.services.tickets_report import TicketInfoService

from models.reports.db_generals_rows import DBGeneralsRow
from models.reports.db_vida_rows import DBVidaRow

def _normalizar_a_date(fecha) -> date:
    if not fecha:
        return None
    if isinstance(fecha, datetime):
        return fecha.date()
    if isinstance(fecha, date):
        return fecha
    
    str_fecha = str(fecha)[:10].replace("-", "/")
    for formato in ("%d/%m/%Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(str_fecha, formato).date()
        except ValueError:
            continue
    return None


def _rows_vida(fecha_ref: date, dni_user_srv:DNIUserService, ad_srv:ADService,
               gdh_srv:GDHUserService, ticket_srv:TicketInfoService) -> list[DBVidaRow]:
    db_vida_srv = DBVidaService()
    rows = []

    ahora = datetime.combine(fecha_ref, time.max) 
    limit_90 = timedelta(days=90)
    limit_180 = timedelta(days=180)

    for db_vida in db_vida_srv.get_all():
        username = db_vida.username

        dni_user_info = dni_user_srv.get_by_username(username)

        ad_user_pps = ad_srv.get_by_username_and_origen(username, "PPS")
        ad_user_vida = ad_srv.get_by_username_and_origen(username, "VIDA")

        dni = dni_user_info.dni if dni_user_info else None

        gdh_user = gdh_srv.get_by_dni(dni) if dni else None
        ticket_cese = ticket_srv.get_by_dni(dni) if dni else None

        escenarios = []
        ces_act:bool = False
        no_ident:bool = False
        s90d:bool = False
        b180d:bool = False
        postcese:bool = False

        #escenarios
        if db_vida.isActive:
            if gdh_user and not gdh_user.isActive and gdh_user.isCesado:
                escenarios.append("Cesado Activo")
                ces_act = True
            elif ticket_cese and not ad_user_pps and not ad_user_vida:
                escenarios.append("Cesado Activo Ticket")
                ces_act = True

        if gdh_user and not gdh_user.isActive and gdh_user.isCesado:
            if db_vida.fecha_login and gdh_user.fecha_cese:
                same_month = gdh_user.fecha_cese.month == fecha_ref.month
                same_year = gdh_user.fecha_cese.year == fecha_ref.year
                
                if same_month and same_year:
                    if db_vida.fecha_login > gdh_user.fecha_cese:
                        escenarios.append("Actividad Post Cese")
                        postcese = True

        if dni_user_info and str(dni_user_info.tipo_usuario).upper() == "USUARIO":

            if db_vida.isActive and db_vida.fecha_creacion and db_vida.fecha_login:
                create_gt_90 = (ahora - db_vida.fecha_creacion) > limit_90
                login_gt_90 = (ahora - db_vida.fecha_login) > limit_90
                if create_gt_90 and login_gt_90:
                    escenarios.append("Sin Actividad 90d")
                    s90d = True

            if not db_vida.isActive and db_vida.fecha_creacion and db_vida.fecha_login:
                create_gt_180 = (ahora - db_vida.fecha_creacion) > limit_180
                login_gt_180 = (ahora - db_vida.fecha_login) > limit_180
                if create_gt_180 and login_gt_180:
                    escenarios.append("Bloqueado 180d")
                    b180d = True
            
            if db_vida.isActive and not gdh_user:
                escenarios.append("No Identificado")
                no_ident = True
            
        escenarios_str = " + ".join(escenarios)

        rows.append(DBVidaRow(
            nombre_archivo=db_vida.file_name,
            username=username,
            typee=db_vida.typee,
            type_desc=db_vida.type_desc,
            db_name=db_vida.database_name,
            server_role=db_vida.server_role,
            database_rol=db_vida.database_rol,
            is_active=db_vida.isActive,
            fecha_creacion=db_vida.fecha_creacion,
            fecha_actualizacion=db_vida.fecha_actualizacion,
            fecha_login=db_vida.fecha_login,
            dni=dni_user_info.dni if dni_user_info else "*No esta en DNI vs Usuarios*",
            tipo_dnivsuser=dni_user_info.tipo_usuario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            usuario_dnivsuser=dni_user_info.usuario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            comentario_dnivsuser=dni_user_info.comentario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            username_ad_pps=ad_user_pps.usuario if ad_user_pps else "*No esta en AD PPS*",
            dni_ad_pps=ad_user_pps.dni if ad_user_pps else "*No esta en AD PPS*",
            username_ad_vida=ad_user_vida.usuario if ad_user_vida else "*No esta en AD VIDA*",
            dni_ad_vida=ad_user_vida.dni if ad_user_vida else "*No esta en AD VIDA*",
            is_activo_gdh=(gdh_user and gdh_user.isActive),
            fecha_alta=gdh_user.fecha_alta if gdh_user else "",
            is_cesado_gdh=(gdh_user and gdh_user.isCesado),
            fecha_cese=gdh_user.fecha_cese if gdh_user else "",
            ticket_cese=ticket_cese.numero_ticket if ticket_cese else "",
            fecha_cierre_ticket_cese=ticket_cese.fecha_cierre if ticket_cese else "",
            escenario=escenarios_str,
            is_cesado_activo=ces_act,
            is_login_post_cese=postcese,
            is_no_identificado=no_ident,
            is_sin_uso_90d=s90d,
            is_deshabilitado_180d=b180d,
        ))

    return rows


def _rows_generales(fecha_ref: date, dni_user_srv: DNIUserService, ad_srv: ADService,
                    gdh_srv: GDHUserService, ticket_srv: TicketInfoService) -> list[DBGeneralsRow]:

    db_generales_srv = DBGeneralesService()
    rows = []

    ahora = datetime.combine(fecha_ref, time.max) 
    limit_90 = timedelta(days=90)
    limit_180 = timedelta(days=180)

    for db_gen in db_generales_srv.get_all():
        username = db_gen.username

        dni_user_info = dni_user_srv.get_by_username(username)

        ad_user_pps = ad_srv.get_by_username_and_origen(username, "PPS")
        ad_user_vida = ad_srv.get_by_username_and_origen(username, "VIDA")

        dni = dni_user_info.dni if dni_user_info else None

        gdh_user = gdh_srv.get_by_dni(dni) if dni else None
        ticket_cese = ticket_srv.get_by_dni(dni) if dni else None

        escenarios = []
        ces_act:bool = False
        no_ident:bool = False
        s90d:bool = False
        b180d:bool = False
        no_ces_oport:bool = False
        postcese:bool = False

        # escenarios
        if db_gen.isActive:
            if db_gen.isActive and gdh_user and not gdh_user.isActive and gdh_user.isCesado:
                escenarios.append("Cesado Activo")
                ces_act = True
            elif ticket_cese and not ad_user_pps and not ad_user_vida:
                escenarios.append("Cesado Activo Ticket")
                ces_act = True

        if gdh_user and not db_gen.isActive:
            if db_gen.fecha_bloqueo and gdh_user.fecha_cese:
                same_month = gdh_user.fecha_cese.month == fecha_ref.month
                same_year = gdh_user.fecha_cese.year == fecha_ref.year
                
                if same_month and same_year:
                    f_bloqueo = _normalizar_a_date(db_gen.fecha_bloqueo)
                    f_cese = _normalizar_a_date(gdh_user.fecha_cese)
                    
                    if f_bloqueo and f_cese:
                        diferencia_dias = (f_bloqueo - f_cese).days
                        
                        if diferencia_dias >= 2:
                            escenarios.append("No Cesado Oportunamente")
                            no_ces_oport = True

        if gdh_user and not gdh_user.isActive and gdh_user.isCesado:
            if db_gen.fecha_login and gdh_user.fecha_cese:
                same_month = gdh_user.fecha_cese.month == fecha_ref.month
                same_year = gdh_user.fecha_cese.year == fecha_ref.year
                
                if same_month and same_year:
                    if db_gen.fecha_login > gdh_user.fecha_cese:
                        escenarios.append("Actividad Post Cese")
                        postcese = True

        if dni_user_info and str(dni_user_info.tipo_usuario).upper() == "USUARIO":

            if db_gen.isActive and db_gen.fecha_creacion and db_gen.fecha_login:
                create_gt_90 = (ahora - db_gen.fecha_creacion) > limit_90
                login_gt_90 = (ahora - db_gen.fecha_login) > limit_90
                if create_gt_90 and login_gt_90:
                    escenarios.append("Sin Actividad 90d")
                    s90d = True

            if not db_gen.isActive and db_gen.fecha_creacion and db_gen.fecha_login:
                create_gt_180 = (ahora - db_gen.fecha_creacion) > limit_180
                login_gt_180 = (ahora - db_gen.fecha_login) > limit_180
                if create_gt_180 and login_gt_180:
                    escenarios.append("Bloqueado 180d")
                    b180d = True
            
            if db_gen.isActive and not gdh_user:
                escenarios.append("No Identificado")
                no_ident = True
            
        escenarios_str = " + ".join(escenarios)

        rows.append(DBGeneralsRow(
            nombre_archivo=db_gen.file_name,
            username=username,
            perfil=db_gen.profile,
            is_active=db_gen.isActive,
            fecha_bloqueo=db_gen.fecha_bloqueo,
            fecha_creacion=db_gen.fecha_creacion,
            fecha_login=db_gen.fecha_login,
            dni=dni_user_info.dni if dni_user_info else "*No esta en DNI vs Usuarios*",
            tipo_dnivsuser=dni_user_info.tipo_usuario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            usuario_dnivsuser=dni_user_info.usuario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            comentario_dnivsuser=dni_user_info.comentario  if dni_user_info else "*No esta en DNI vs Usuarios*",
            username_ad_pps=ad_user_pps.usuario if ad_user_pps else "*No esta en AD PPS*",
            dni_ad_pps=ad_user_pps.dni if ad_user_pps else "*No esta en AD PPS*",
            username_ad_vida=ad_user_vida.usuario if ad_user_vida else "*No esta en AD VIDA*",
            dni_ad_vida=ad_user_vida.dni if ad_user_vida else "*No esta en AD VIDA*",
            is_activo_gdh=(gdh_user and gdh_user.isActive),
            fecha_alta=gdh_user.fecha_alta if gdh_user else "",
            is_cesado_gdh=(gdh_user and gdh_user.isCesado),
            fecha_cese=gdh_user.fecha_cese if gdh_user else "",
            ticket_cese=ticket_cese.numero_ticket if ticket_cese else "",
            fecha_cierre_ticket_cese=ticket_cese.fecha_cierre if ticket_cese else "",
            escenario=escenarios_str,
            is_cesado_activo=ces_act,
            is_login_post_cese=postcese,
            is_no_identificado=no_ident,
            is_sin_uso_90d=s90d,
            is_deshabilitado_180d=b180d,
            is_no_cesado_oportunamente=no_ces_oport,
        ))

    return rows

