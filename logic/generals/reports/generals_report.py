
from logic.generals.services.autorizados_service import AutorizedUserService
from logic.generals.services.epps_ac_service import EPPSACService
from logic.generals.services.epps_ae_service import EPPSAEService
from logic.generals.services.igwprd_ac_service import IGWPRDACService
from logic.generals.services.igwprd_ae_service import IGWPRDAEService

NO_REGISTERED = "*No Registrado*"
NO_MATCH = "*No Coincide*"

def hallazgos_ac(autorizados_srv:AutorizedUserService, epps_ac_srv:EPPSACService, igwprd_ac_srv:IGWPRDACService):

    rows = []
    for epps_ac_user in epps_ac_srv.get_all():
        
        autorized_user = autorizados_srv.get_by_usuario_red(epps_ac_user.spare1)

        usuario_utiliza = f"AC{epps_ac_user.spare1[:-2]}"
        usuario_corresponde = autorized_user.db_epps_ac if autorized_user else NO_REGISTERED

        rows.append({
            "db": "EPPS",
            "cuenta de acceso": epps_ac_user.userid,
            "host de conexión": epps_ac_user.userhost,
            "terminal": epps_ac_user.terminal,
            "fecha de cierre sesion": epps_ac_user.logoff_time,
            "elemento consultado": epps_ac_user.obj_name,
            "cuenta de usuario": epps_ac_user.spare1,
            "fecha accion": epps_ac_user.ntimestamp,
            "codigo accion": epps_ac_user.action,
            "jefe chapter lead": autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED,
            "validacion cuenta de acceso": "Registrado" if autorizados_srv.exists_by_db_epps_ac(epps_ac_user.userid) else NO_REGISTERED,
            "usuario utilizado": usuario_utiliza,
            "validacion usuario utilizado": "Coincide" if usuario_utiliza.upper() == epps_ac_user.userid.upper() else NO_MATCH,
            "usuario corresponde": usuario_corresponde,
            "validacion usuario corrsponde": "Coincide" if usuario_corresponde.upper() == epps_ac_user.userid.upper() else NO_MATCH,
        })

    for igwprd_ac_user in igwprd_ac_srv.get_all():
        
        autorized_user = autorizados_srv.get_by_usuario_red(igwprd_ac_user.spare1)

        usuario_utiliza = f"AC{igwprd_ac_user.spare1[:-2]}"
        usuario_corresponde = autorized_user.db_igwprd_ac if autorized_user else NO_REGISTERED

        rows.append({
            "db": "IGWPRD",
            "cuenta de acceso": igwprd_ac_user.userid,
            "host de conexión": igwprd_ac_user.userhost,
            "terminal": igwprd_ac_user.terminal,
            "fecha de cierre sesion": igwprd_ac_user.logoff_time,
            "elemento consultado": igwprd_ac_user.obj_name,
            "cuenta de usuario": igwprd_ac_user.spare1,
            "fecha accion": igwprd_ac_user.ntimestamp,
            "codigo accion": igwprd_ac_user.action,
            "jefe chapter lead": autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED,
            "validacion cuenta de acceso": "Registrado" if autorizados_srv.exists_by_db_igwprd_ac(igwprd_ac_user.userid) else NO_REGISTERED,
            "usuario utilizado": usuario_utiliza,
            "validacion usuario utilizado": "Coincide" if usuario_utiliza.upper() == igwprd_ac_user.userid.upper() else NO_MATCH,
            "usuario corresponde": usuario_corresponde,
            "validacion usuario corrsponde": "Coincide" if usuario_corresponde.upper() == igwprd_ac_user.userid.upper() else NO_MATCH,
        })

    return rows

def hallazgos_ae(autorizados_srv:AutorizedUserService, epps_ae_srv:EPPSAEService, igwprd_ae_srv:IGWPRDAEService):

    rows = []
    for epps_ae_user in epps_ae_srv.get_all():
        
        autorized_user = autorizados_srv.get_by_usuario_red(epps_ae_user.spare1)

        usuario_utiliza = f"AE{epps_ae_user.spare1[:-2]}"
        usuario_corresponde = autorized_user.db_epps_ae if autorized_user else NO_REGISTERED

        rows.append({
            "db": "EPPS",
            "cuenta de acceso": epps_ae_user.userid,
            "host de conexión": epps_ae_user.userhost,
            "terminal": epps_ae_user.terminal,
            "fecha de cierre sesion": epps_ae_user.logoff_time,
            "elemento consultado": epps_ae_user.obj_name,
            "cuenta de usuario": epps_ae_user.spare1,
            "fecha accion": epps_ae_user.ntimestamp,
            "codigo accion": epps_ae_user.action,
            "jefe chapter lead": autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED,
            "validacion cuenta de acceso": "Registrado" if autorizados_srv.exists_by_db_epps_ae(epps_ae_user.userid) else NO_REGISTERED,
            "usuario utilizado": usuario_utiliza,
            "validacion usuario utilizado": "Coincide" if usuario_utiliza.upper() == epps_ae_user.userid.upper() else NO_MATCH,
            "usuario corresponde": usuario_corresponde,
            "validacion usuario corrsponde": "Coincide" if usuario_corresponde.upper() == epps_ae_user.userid.upper() else NO_MATCH,
        })

    for igwprd_ae_user in igwprd_ae_srv.get_all():
        
        autorized_user = autorizados_srv.get_by_usuario_red(igwprd_ae_user.spare1)

        usuario_utiliza = f"AE{igwprd_ae_user.spare1[:-2]}"
        usuario_corresponde = autorized_user.db_igwprd_ae if autorized_user else NO_REGISTERED

        rows.append({
            "db": "IGWPRD",
            "cuenta de acceso": igwprd_ae_user.userid,
            "host de conexión": igwprd_ae_user.userhost,
            "terminal": igwprd_ae_user.terminal,
            "fecha de cierre sesion": igwprd_ae_user.logoff_time,
            "elemento consultado": igwprd_ae_user.obj_name,
            "cuenta de usuario": igwprd_ae_user.spare1,
            "fecha accion": igwprd_ae_user.ntimestamp,
            "codigo accion": igwprd_ae_user.action,
            "jefe chapter lead": autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED,
            "validacion cuenta de acceso": "Registrado" if autorizados_srv.exists_by_db_igwprd_ae(igwprd_ae_user.userid) else NO_REGISTERED,
            "usuario utilizado": usuario_utiliza,
            "validacion usuario utilizado": "Coincide" if usuario_utiliza.upper() == igwprd_ae_user.userid.upper() else NO_MATCH,
            "usuario corresponde": usuario_corresponde,
            "validacion usuario corrsponde": "Coincide" if usuario_corresponde.upper() == igwprd_ae_user.userid.upper() else NO_MATCH,
        })

    return rows

def generate_report():
    autorizados_srv = AutorizedUserService()
    epps_ac_srv = EPPSACService()
    epps_ae_srv = EPPSAEService()
    igwprd_ac_srv = IGWPRDACService()
    igwprd_ae_srv = IGWPRDAEService()

    return {
        "hallazgos_ac": hallazgos_ac(autorizados_srv, epps_ac_srv, igwprd_ac_srv),
        "hallazgos_ae": hallazgos_ae(autorizados_srv, epps_ae_srv, igwprd_ae_srv),
    }
