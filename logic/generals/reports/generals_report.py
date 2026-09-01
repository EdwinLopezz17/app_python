from logic.generals.services.autorizados_service import AutorizedUserService
from logic.generals.services.epps_ac_service import EPPSACService
from logic.generals.services.epps_ae_service import EPPSAEService
from logic.generals.services.igwprd_ac_service import IGWPRDACService
from logic.generals.services.igwprd_ae_service import IGWPRDAEService
from models.reports.generales_ac import GeneralesAC
from models.reports.generales_ae import GeneralesAE

NO_REGISTERED = "*No Registrado*"
NO_MATCH = "*No Coincide*"

def hallazgos_ac() -> list[GeneralesAC]:
    autorizados_srv = AutorizedUserService()
    epps_ac_srv = EPPSACService()
    igwprd_ac_srv = IGWPRDACService()
    rows: list[GeneralesAC] = []

    for epps_ac_user in epps_ac_srv.get_all():
        autorized_user = autorizados_srv.get_by_usuario_red(epps_ac_user.spare1)
        usuario_utiliza = f"AC{epps_ac_user.spare1[:-2]}"
        usuario_corresponde = (
            autorized_user.db_epps_ac if autorized_user else NO_REGISTERED
        )

        rows.append(
            GeneralesAC(
                db="EPPS",
                cuenta_acceso=epps_ac_user.userid,
                host_conexion=epps_ac_user.userhost,
                terminal=epps_ac_user.terminal,
                fecha_cierre_sesion=epps_ac_user.logoff_time,
                elemento_consultado=epps_ac_user.obj_name,
                cuenta_usuario=epps_ac_user.spare1,
                fecha_accion=epps_ac_user.ntimestamp,
                codigo_accion=epps_ac_user.action,
                jefe_chapter_lead=( autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED),
                val_cuenta_acceso=( "Registrado" if autorizados_srv.exists_by_db_epps_ac(epps_ac_user.userid) else NO_REGISTERED),
                usuario_utilizado=usuario_utiliza,
                val_usuario_utilizado=( "Coincide" if usuario_utiliza.upper() == epps_ac_user.userid.upper() else NO_MATCH),
                usuario_corresponde=usuario_corresponde,
                val_usuario_corrsponde=("Coincide" if usuario_corresponde.upper() == epps_ac_user.userid.upper() else NO_MATCH),
            )
        )

    for igwprd_ac_user in igwprd_ac_srv.get_all():
        autorized_user = autorizados_srv.get_by_usuario_red(igwprd_ac_user.spare1)
        usuario_utiliza = f"AC{igwprd_ac_user.spare1[:-2]}"
        usuario_corresponde = (
            autorized_user.db_igwprd_ac if autorized_user else NO_REGISTERED
        )

        rows.append(
            GeneralesAC(
                db="IGWPRD",
                cuenta_acceso=igwprd_ac_user.userid,
                host_conexion=igwprd_ac_user.userhost,
                terminal=igwprd_ac_user.terminal,
                fecha_cierre_sesion=igwprd_ac_user.logoff_time,
                elemento_consultado=igwprd_ac_user.obj_name,
                cuenta_usuario=igwprd_ac_user.spare1,
                fecha_accion=igwprd_ac_user.ntimestamp,
                codigo_accion=igwprd_ac_user.action,
                jefe_chapter_lead=(autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED),
                val_cuenta_acceso=("Registrado" if autorizados_srv.exists_by_db_igwprd_ac( igwprd_ac_user.userid) else NO_REGISTERED),
                usuario_utilizado=usuario_utiliza,
                val_usuario_utilizado=("Coincide" if usuario_utiliza.upper() == igwprd_ac_user.userid.upper() else NO_MATCH),
                usuario_corresponde=usuario_corresponde,
                val_usuario_corrsponde=("Coincide" if usuario_corresponde.upper() == igwprd_ac_user.userid.upper() else NO_MATCH),
            )
        )

    return rows

def hallazgos_ae() -> list[GeneralesAE]:
    autorizados_srv = AutorizedUserService()
    epps_ae_srv = EPPSAEService()
    igwprd_ae_srv = IGWPRDAEService()

    rows: list[GeneralesAE] = []

    for epps_ae_user in epps_ae_srv.get_all():
        autorized_user = autorizados_srv.get_by_usuario_red(epps_ae_user.spare1)
        usuario_utiliza = f"AE{epps_ae_user.spare1[:-2]}"
        usuario_corresponde = (
            autorized_user.db_epps_ae if autorized_user else NO_REGISTERED
        )

        rows.append(
            GeneralesAE(
                db="EPPS",
                cuenta_acceso=epps_ae_user.userid,
                host_conexion=epps_ae_user.userhost,
                terminal=epps_ae_user.terminal,
                fecha_cierre_sesion=epps_ae_user.logoff_time,
                elemento_consultado=epps_ae_user.obj_name,
                cuenta_usuario=epps_ae_user.spare1,
                fecha_accion=epps_ae_user.ntimestamp,
                codigo_accion=epps_ae_user.action,
                jefe_chapter_lead=(autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED),
                val_cuenta_acceso=("Registrado" if autorizados_srv.exists_by_db_epps_ae(epps_ae_user.userid) else NO_REGISTERED),
                usuario_utilizado=usuario_utiliza,
                val_usuario_utilizado=("Coincide" if usuario_utiliza.upper() == epps_ae_user.userid.upper() else NO_MATCH),
                usuario_corresponde=usuario_corresponde,
                val_usuario_corrsponde=("Coincide" if usuario_corresponde.upper() == epps_ae_user.userid.upper() else NO_MATCH),
            )
        )

    for igwprd_ae_user in igwprd_ae_srv.get_all():
        autorized_user = autorizados_srv.get_by_usuario_red(igwprd_ae_user.spare1)
        usuario_utiliza = f"AE{igwprd_ae_user.spare1[:-2]}"
        usuario_corresponde = (
            autorized_user.db_igwprd_ae if autorized_user else NO_REGISTERED
        )

        rows.append(
            GeneralesAE(
                db="IGWPRD",
                cuenta_acceso=igwprd_ae_user.userid,
                host_conexion=igwprd_ae_user.userhost,
                terminal=igwprd_ae_user.terminal,
                fecha_cierre_sesion=igwprd_ae_user.logoff_time,
                elemento_consultado=igwprd_ae_user.obj_name,
                cuenta_usuario=igwprd_ae_user.spare1,
                fecha_accion=igwprd_ae_user.ntimestamp,
                codigo_accion=igwprd_ae_user.action,
                jefe_chapter_lead=(autorized_user.jefe_chapter_lead if autorized_user else NO_REGISTERED),
                val_cuenta_acceso=("Registrado" if autorizados_srv.exists_by_db_igwprd_ae(igwprd_ae_user.userid) else NO_REGISTERED),
                usuario_utilizado=usuario_utiliza,
                val_usuario_utilizado=("Coincide" if usuario_utiliza.upper() == igwprd_ae_user.userid.upper() else NO_MATCH),
                usuario_corresponde=usuario_corresponde,
                val_usuario_corrsponde=("Coincide" if usuario_corresponde.upper() == igwprd_ae_user.userid.upper() else NO_MATCH),
            )
        )

    return rows

