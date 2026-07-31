"""
CATÁLOGO MAESTRO DE COLUMNAS ESPERADAS  (validación de archivos al cargar)
=========================================================================

Única fuente de verdad de las cabeceras que debe traer cada archivo que sube
el usuario. Es el port directo de `src/config/fuentes.ts -> COLUMNS` del
frontend Next.js.

Editar una columna a validar = editarla AQUÍ. Se propaga a todos los hallazgos
que usen ese conjunto.

La comparación es tolerante (ver `app/ingest/normalize.py`): ignora tildes,
mayúsculas, espacios repetidos, caracteres invisibles (BOM, zero-width) y
comillas envolventes. Por eso el header canónico se escribe UNA sola vez, con
tildes, y el archivo se acepta igual venga con o sin ellas.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Compartidas por varios hallazgos
# ---------------------------------------------------------------------------

ACSELX = [
    "CODUSRPPS", "CODPERFIL", "STSUSRPPSAPLIC", "STSUSRPPS", "CODAPLIC",
    "CODCOLABORADOR", "NOMUSRPPS", "NUMDOC", "TIPOUSRPPS", "FECHACREA", "FECACCESO",
]

ONBASE = ["USUARIO", "GRUPO ONBASE", "NOMBRE COMPLETO", "CORREO", "ÚLTIMO LOGUEO"]

SOX_VIDA = [
    "IDUSUARIO", "NOMBRE_APLICACION", "CODIGO_ROL", "APELLIDO_PATERNO",
    "APELLIDO_MATERNO", "NOMBRES", "NOMBRE_ROL", "BLOQUEADO",
    "AUDITORIA_CREACION", "AUDITORIA_MODIFICACION",
]

EAS = [
    "USER_ID", "USER_NAME", "GROUP_ID", "FECHAEXPIRACION_CUENTA",
    "CUENTAAUTENTICACION_WINDOWS", "FECHAEXPIRACION_PASSWORD",
    "FECHAULTIMOLOGIN", "INDICADORBLOQUEADO",
]

# Guidewire y afines: Billing / Claim / Contact / Policy Center comparten estructura.
GUIDEWIRE = [
    "USERNAME", "ROLENAME", "NAME", "LASTNAME", "SECONDLASTNAME",
    "ROLEDESCRIPTION", "FECHA_CREACION", "ESTADO",
]

PROPHET = ["CORREO"]

PMS = [
    "LOGIN_SISTEMA", "EMPRESA_LOGIN", "DESCRIPCION_LOGIN", "CODIGO_IDENTIDAD",
    "PRIVILEGIO", "PERFIL", "ESTADO", "LOGIN_WINDOWS", "ACTIVO_BLOQUEADO",
    "FECHA_EXPIRACION",
]

SALESFORCE = ["ID DE FEDERACION", "PERFIL", "ACTIVO", "ULTIMO INICIO DE SESION"]

SINIESTROS_WEB = ["ACL ENTRY NAME", "ACL ENTRY TYPE", "ACL LEVEL"]

BOTMAKER = ["EMAIL", "ROLE", "ACTIVE", "REGISTRATION_DATE", "LAST_LOGIN_DATE"]

# Active Directory: idéntico para AD PPS y AD Vida.
AD = [
    "SAMACCOUNTNAME", "EMAILADDRESS", "LASTLOGONDATE", "DISPLAYNAME", "IPPHONE",
    "WHENCREATED", "WHENCHANGED", "FACSIMILETELEPHONENUMBER", "DESCRIPTION",
    "ENABLED", "PASSWORDNEVEREXPIRES", "CANNOTCHANGEPASSWORD", "PASSWORDLASTSET",
    "TITLE", "DEPARTMENT", "COMPANY", "STREETADDRESS",
]

GDH_ACTIVOS = [
    "NÚMERO ID", "NOMBRES", "APELLIDO PATERNO", "APELLIDO MATERNO",
    "GRUPO DE PERSONAL", "CÓDIGO FUNCIÓN", "FUNCIÓN", "CÓDIGO DE UN.ORG.",
    "UNIDAD ORGANIZATIVA", "FECHA", "SOCIEDAD", "ÁREA DE NÓMINA", "AREA BCP",
    "DIVISIÓN BCP", "CÓDIGO SERVICIO", "TEXTO SERVICIO", "CÓDIGO JEFE",
    "NOMBRE DEL JEFE", "Nº PERS.",
]

GDH_CESADOS = [
    "NÚMERO ID", "NOMBRES", "APELLIDO PATERNO", "APELLIDO MATERNO",
    "GRUPO DE PERSONAL", "FUNCIÓN", "UNIDAD ORGANIZATIVA", "FECHA", "SOCIEDAD",
]

DNI_VS_USUARIOS = ["USERNAME", "TIPO", "USUARIO", "DNI", "COMENTARIO"]

ENTRA_ID = [
    "ID", "SIGNINACTIVITY", "USERPRINCIPALNAME", "MAIL", "ACCOUNTENABLED",
    "CREATEDDATETIME", "FAXNUMBER", "POSTALCODE", "STREETADDRESS",
]

TICKETS_CESES = [
    "CREADO", "NUMERO ID", "INGRESA EL DNI DE LA PERSONA A CESAR", "ELEMENTO",
    "NÚMERO", "CERRADO",
]

# ---------------------------------------------------------------------------
# Solo hallazgo Aplicaciones
# ---------------------------------------------------------------------------

ADDACTIS = ["USER NAME", "USER DOMAIN"]

CGWEB = [
    "CODUSRPPS", "CODAPLIC", "CODCOLABORADOR", "NOMUSRPPS", "NUMDOC",
    "CODPERFIL", "STSUSRPPSAPLIC", "STSUSRPPS", "TIPOUSRPPS", "FECHACREA",
    "FECACCESO",
]

CRM = ["ID", "DISPLAYNAME", "MAIL", "USERPRINCIPALNAME"]

DATALAKE = ["ID", "MAIL", "USERPRINCIPALNAME", "DISPLAYNAME"]

MONOKERA = ["CORREO ELECTRÓNICO", "ROLES", "NOMBRE DEL USUARIO", "ESTADO"]

QUALYS = ["EMAIL", "ROLE", "NAME", "STATUS", "CREATED", "LAST LOGIN"]

SEGCEN = [
    "ID USUARIO", "ID ROL", "APELLIDO PATERNO", "APELLIDO MATERNO", "NOMBRES",
    "EMAIL", "FECHA DE CREACIÓN", "FECHA DE MODIFICACIÓN", "ESTADO",
    "NOMBRE DE ROL",
]

SSA = ["CODUSRPPS", "CODCOLABORADOR", "NOMUSRPPS", "MAIL", "STSUSRPPS"]

APP_LOGIN = ["IDUSUARIO", "NOMBRE_APLICACION", "ULTIMOLOGEO"]

EXACTUS = ["USUARIO", "ACTIVO", "CREATEDBY", "NOMBRE", "CREATEDATE", "UPDATEDBY"]

# ---------------------------------------------------------------------------
# Solo hallazgos Perfiles / Activos GDH
# ---------------------------------------------------------------------------

EXACTUS_PERFILES = ["USUARIO", "GRUPO", "NOMBRE", "ESTADO", "FECHA CREACION", "TIPO"]

MATRIZ_ROLES = [
    "ROL", "PERFIL ROL DEL ACTIVO", "NOMBRE DEL ACTIVO", "TIPO DE ROL",
    "CODIGO FUNCION", "FUNCION", "CODIGO UO", "UNIDAD ORGANIZATIVA",
    "TIPO DE ACTIVO", "DESCRIPCION", "TICKET", "MODIFIED", "CREATED",
]

# ---------------------------------------------------------------------------
# Solo hallazgo Base de Datos
# ---------------------------------------------------------------------------

BD_VIDA = [
    "USERNAME", "TYPE", "TYPE_DESC", "ISACTIVE", "ULTIMOLOGEO", "CREATED",
    "UPDATE", "DATABASEROLE", "DATABASENAME", "SERVERROLE",
]

BD_GENERALES = [
    "USERNAME", "ACCOUNT_STATUS", "LOCK_DATE", "CREATED", "PROFILE",
    "ULTIMO_LOGIN",
]

# ---------------------------------------------------------------------------
# Solo hallazgo Generales y Especiales
# ---------------------------------------------------------------------------

USUARIOS_AUTORIZADOS = [
    "NOMBRES Y APELLIDOS", "EQUIPO / CHAPTER", "EMPRESA", "CORREO",
    "JEFE / CHAPTER LEAD", "USUARIO DE RED", "BD EPPS UC", "BD DBPRODN UC",
    "BD OWEB UC", "BD ODW1 UC", "BD DBPRODN2 AE", "BD IGWPRD AE", "BD EPPS AE",
    "BD IGWPRD AC", "BD EPPS AC",
]

# EPPS / IGWPRD (AE y AC) comparten estructura de auditoría Oracle.
AUDITORIA_ORACLE = [
    "USERID", "USERHOST", "TERMINAL", "LOGOFF$TIME", "OBJ$NAME", "SPARE1",
    "NTIMESTAMP#", "ACTION#",
]
