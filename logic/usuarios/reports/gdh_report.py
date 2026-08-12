from logic.share.services.gdh_service import GDHUserService
from logic.share.services.mr_service import MatrizRolesService
from logic.share.services.ad_service import ADService, ADUserInfo
from logic.share.services.dni_vs_user_service import DNIUserInfo, DNIUserService
from logic.share.services.entraid_service import EntraUserService
from models.reports.gdh_rows import GDHRows
    
def gdh_report():
    gdh_srv = GDHUserService()
    mr_srv = MatrizRolesService()
    ad_srv = ADService()
    dni_srv = DNIUserService()
    entra_srv = EntraUserService()

    ROLES_BASICOS = {"R000020934", "RP00011202"}
    rows = []

    for user in gdh_srv.get_all():
        if not user.isActive:
            continue

        rol_gdh = user.get_rol()
        if user.esProveedor:
            existe_en_mr = "no aplica"
        else:
            existe_en_mr = "Si" if mr_srv.exists_by_rol(rol_gdh) else "No"

        user_pps:ADUserInfo = None
        user_vida:ADUserInfo = None
        dni_info_encontrado:DNIUserInfo = None
        correo = ""

        for dni_info in dni_srv.get_by_dni(user.dni):
            if dni_info.tipo_usuario != "USUARIO": 
                continue

            if not user_pps:
                user_pps = ad_srv.get_by_username_and_origen(dni_info.username, "PPS")
                if user_pps:
                    dni_info_encontrado = dni_info 
                    correo = user_pps.correo

            if not user_vida:
                user_vida = ad_srv.get_by_username_and_origen(dni_info.username, "PVIDA")
                if user_vida:
                    dni_info_encontrado = dni_info
                    correo = user_vida.correo

            if user_pps and user_vida:
                break

        if not dni_info_encontrado:
            dni_info_encontrado = next(
                (d for d in dni_srv.get_by_dni(user.dni) if d.tipo_usuario == "USUARIO"), 
                None
            )

        entra_user = entra_srv.get_by_email(correo)
        if not entra_user:
            entra_user = entra_srv.get_by_upn(correo)

        jefe_gdh = ""
        gdh_user_aux = gdh_srv.get_by_n_personal(user.cod_jefe)
        if gdh_user_aux:
            ad_user_pps = ad_srv.get_by_dni_and_origen(gdh_user_aux.dni, "PPS")
            if ad_user_pps:
                jefe_gdh = ad_user_pps.correo
            
            if not jefe_gdh:
                ad_user_vida = ad_srv.get_by_dni_and_origen(gdh_user_aux.dni, "PVIDA")
                if ad_user_vida:
                    jefe_gdh = ad_user_vida.correo


        def calcular_validacion_dni():
            observaciones = []
            
            dni_gdh = user.dni if user.dni else ""
            dni_pps = user_pps.dni if (user_pps and user_pps.dni) else ""
            dni_vida = user_vida.dni if (user_vida and user_vida.dni) else ""

            existe_pps = user_pps is not None
            existe_vida = user_vida is not None

            if not existe_pps and not existe_vida:
                observaciones.append("No existe en ADs")
                return " + ".join(observaciones)

            if (existe_pps and not dni_pps) or (existe_vida and not dni_vida):
                observaciones.append("DNI vacio en AD")

            if existe_pps and existe_vida:
                if dni_pps and dni_vida and dni_pps != dni_vida:
                    observaciones.append("Diferencia de DNIs entre ADs")
                
                if dni_pps == dni_vida and dni_pps and dni_pps != dni_gdh:
                    observaciones.append("pps/vida no coincide con dni gdh")
                else:
                    if dni_pps and dni_pps != dni_gdh:
                        observaciones.append("pps dni no coincide con gdh")
                    if dni_vida and dni_vida != dni_gdh:
                        observaciones.append("vida dni no coincide con gdh")

            elif existe_pps and not existe_vida:
                if dni_pps and dni_pps != dni_gdh:
                    observaciones.append("pps dni no coincide con gdh")
                
            elif existe_vida and not existe_pps:
                if dni_vida and dni_vida != dni_gdh:
                    observaciones.append("vida dni no coincide con gdh")

            return " + ".join(observaciones) if observaciones else ""
        
        def calcular_validacion_rol():
            observaciones = []
            rol_pps = user_pps.rol if (user_pps and user_pps.rol) else ""
            rol_vida = user_vida.rol if (user_vida and user_vida.rol) else ""

            existe_pps = user_pps is not None
            existe_vida = user_vida is not None

            if user.esProveedor:
                if not existe_pps and not existe_vida:
                    observaciones.append("No existe en ADs")
                else:
                    if (existe_pps and not rol_pps) or (existe_vida and not rol_vida):
                        observaciones.append("sin rol registrado")

                    if (rol_pps in ROLES_BASICOS) or (rol_vida in ROLES_BASICOS):
                        observaciones.append("Rol Basico")
                    
                    if existe_pps and existe_vida:
                        if rol_pps != rol_vida:
                            observaciones.append("No Coincide en ADs")
            else:
                if not existe_pps and not existe_vida:
                    observaciones.append("No existe en ADs")
                else:
                    if existe_pps and existe_vida:
                        if rol_pps == rol_vida:
                            if rol_pps != rol_gdh:
                                observaciones.append("pps/vida no coincide con gdh")
                        else:
                            observaciones.append("Diferencia de roles entre ADs")
                            if rol_pps != rol_gdh:
                                observaciones.append("pps no coincide con gdh")
                            if rol_vida != rol_gdh:
                                observaciones.append("vida no coincide con gdh")
                    
                    elif existe_pps and not existe_vida:
                        if rol_pps != rol_gdh:
                            observaciones.append("pps no coincide con gdh")

                    elif existe_vida and not existe_pps:
                        if rol_vida != rol_gdh:
                            observaciones.append("vida no coincide con gdh")

            return " + ".join(observaciones) if observaciones else ""

        rows.append(
            GDHRows(
                nombre_colaborador=user.fullname(),
                dni=user.dni,
                sociedad=user.sociedad,
                cod_funcion=user.cod_funcion,
                cod_unidad_organizativa=user.cod_uni_orga,
                cod_servicio=user.cod_servicio,
                tipo_dnivsuser=dni_info_encontrado.tipo_usuario if dni_info_encontrado else "*No esta en DNI vs Usuarios*",
                usuario_dnivsuser=dni_info_encontrado.usuario if dni_info_encontrado else "*No esta en DNI vs Usuarios*",
                comentario_dnivsuser=dni_info_encontrado.comentario if dni_info_encontrado else "*No esta en DNI vs Usuarios*",
                tipo_rol=user.calculate_role_type(),
                rol_gdh=rol_gdh,
                jefe_gdh=jefe_gdh,
                jefe_entra=entra_user.jefe if entra_user else "*No existe en Entra ID*",
                existe_en_mr=existe_en_mr,
                username_pps=user_pps.usuario if user_pps else "*No existe en AD*",
                rol_pps=user_pps.rol if user_pps else "*No existe en AD*",
                dni_pps=user_pps.dni if user_pps else "*No existe en AD*",
                jefe_pps=user_pps.jefe if user_pps else "*No existe en AD*",
                username_vida=user_vida.usuario if user_vida else "*No existe en AD*",
                rol_vida=user_vida.rol if user_vida else "*No existe en AD*",
                dni_vida=user_vida.dni if user_vida else "*No existe en AD*",
                jefe_vida=user_vida.jefe if user_vida else "*No existe en AD*",
                validacion_rol=calcular_validacion_rol(),
                validacion_dni=calcular_validacion_dni(),
            )
        )

    return rows
