from __future__ import annotations

from dataclasses import dataclass, field

from models.file_names import FileName

from app.catalog import columns as C

FORMATOS_ACEPTADOS = (".csv", ".xls", ".xlsx")


@dataclass(frozen=True)
class Slot:

    file_name: FileName
    columns: list[str]
    label: str | None = None
    multiple: bool = False
    origin_file: bool = False
    subfolder: str | None = None

    @property
    def key(self) -> str:
        return self.file_name.value

    @property
    def display_label(self) -> str:
        return self.label or self.file_name.value


@dataclass(frozen=True)
class Fuente:

    id: str
    label: str
    group: str
    slots: list[Slot] = field(default_factory=list)

    @property
    def file_names(self) -> list[str]:
        return [s.key for s in self.slots]


APLICACIONES = "Aplicaciones"
OTROS_REPORTES = "Otros Reportes"
BASES_DE_DATOS = "Bases de Datos"


def _one(fn: FileName, cols: list[str], **kw) -> list[Slot]:
    return [Slot(file_name=fn, columns=cols, **kw)]


FUENTES: dict[str, Fuente] = {}


def _reg(f: Fuente) -> Fuente:
    if f.id in FUENTES:
        raise ValueError(f"Fuente duplicada en el registro: {f.id}")
    FUENTES[f.id] = f
    return f


_reg(Fuente("dni-vs-usuarios", "DNI vs Usuarios", OTROS_REPORTES,
            _one(FileName.DNI_VS_USUARIOS, C.DNI_VS_USUARIOS)))

_reg(Fuente("gdh", "GDH Activos y Cesados", OTROS_REPORTES, [
    Slot(FileName.ACTIVOS_GDH, C.GDH_ACTIVOS, label="Activos GDH"),
    Slot(FileName.CESADOS_GDH, C.GDH_CESADOS, label="Cesados GDH"),
]))

_reg(Fuente("ad", "Active Directory", OTROS_REPORTES, [
    Slot(FileName.AD_PPS, C.AD, label="AD PPS"),
    Slot(FileName.AD_VIDA, C.AD, label="AD Vida"),
]))

_reg(Fuente("tickets-ceses", "Tickets Ceses", OTROS_REPORTES,
            _one(FileName.TICKETS_CESES, C.TICKETS_CESES)))

_reg(Fuente("entra-id", "Entra ID", OTROS_REPORTES,
            _one(FileName.ENTRA_ID, C.ENTRA_ID)))

_reg(Fuente("matriz-roles", "Matriz de Roles", OTROS_REPORTES,
            _one(FileName.MATRIZ_ROLES, C.MATRIZ_ROLES)))


_reg(Fuente("app-login", "Login de Aplicaciones", APLICACIONES,
            _one(FileName.APP_LOGIN, C.APP_LOGIN)))
_reg(Fuente("cgweb", "Carta de Garantía Web", APLICACIONES,
            _one(FileName.CGWEB, C.CGWEB)))
_reg(Fuente("acselx", "Acselx", APLICACIONES,
            _one(FileName.ACSELX, C.ACSELX)))
_reg(Fuente("billing-center", "Billing Center", APLICACIONES,
            _one(FileName.BILLING_CENTER, C.GUIDEWIRE)))
_reg(Fuente("claim-center", "Claim Center", APLICACIONES,
            _one(FileName.CLAIM_CENTER, C.GUIDEWIRE)))
_reg(Fuente("contact-manager", "Contact Manager", APLICACIONES,
            _one(FileName.CONTACT_MANAGER, C.GUIDEWIRE)))
_reg(Fuente("policycenter", "Policy Center", APLICACIONES,
            _one(FileName.POLICYCENTER, C.GUIDEWIRE)))
_reg(Fuente("eas", "EAS", APLICACIONES,
            _one(FileName.EAS, C.EAS)))
_reg(Fuente("exactus", "Exactus", APLICACIONES,
            _one(FileName.EXACTUS, C.EXACTUS)))
_reg(Fuente("onbase", "Onbase", APLICACIONES,
            _one(FileName.ONBASE, C.ONBASE)))
_reg(Fuente("pms", "PMS", APLICACIONES,
            _one(FileName.PMS, C.PMS)))
_reg(Fuente("segcen", "Segcen", APLICACIONES,
            _one(FileName.SEGCEN, C.SEGCEN)))
_reg(Fuente("sox-vida", "Sox Vida", APLICACIONES,
            _one(FileName.SOX_VIDA, C.SOX_VIDA)))
_reg(Fuente("prophet", "Prophet", APLICACIONES,
            _one(FileName.PROPHET, C.PROPHET)))
_reg(Fuente("botmaker", "Botmaker", APLICACIONES,
            _one(FileName.BOTMAKER, C.BOTMAKER)))
_reg(Fuente("salesforce", "Salesforce", APLICACIONES,
            _one(FileName.SALESFORCE, C.SALESFORCE)))
_reg(Fuente("addactis", "Addactis", APLICACIONES,
            _one(FileName.ADDACTIS, C.ADDACTIS)))
_reg(Fuente("monokera", "Monokera", APLICACIONES,
            _one(FileName.MONOKERA, C.MONOKERA)))
_reg(Fuente("siniestros-web", "Siniestros Web", APLICACIONES,
            _one(FileName.SINIESTROS_WEB, C.SINIESTROS_WEB)))
_reg(Fuente("qualys", "Qualys", APLICACIONES,
            _one(FileName.QUALYS, C.QUALYS)))
_reg(Fuente("ssa", "SSA", APLICACIONES,
            _one(FileName.SSA, C.SSA)))
_reg(Fuente("datalake", "Datalake", APLICACIONES,
            _one(FileName.DATALAKE, C.DATALAKE, multiple=True)))
_reg(Fuente("crm", "CRM", APLICACIONES,
            _one(FileName.CRM, C.CRM, multiple=True)))

_reg(Fuente("exactus-perfiles", "Exactus Perfiles", APLICACIONES,
            _one(FileName.EXACTUS_PERFILES, C.EXACTUS_PERFILES)))


_reg(Fuente("db-vida", "DBs Vida", BASES_DE_DATOS,
            _one(FileName.DB_VIDA, C.BD_VIDA,
                 multiple=True, origin_file=True, subfolder="DB Vida")))
_reg(Fuente("db-generales", "DBs Generales", BASES_DE_DATOS,
            _one(FileName.DB_GENERALES, C.BD_GENERALES,
                 multiple=True, origin_file=True, subfolder="DB Generales")))


_reg(Fuente("usuarios-autorizados", "Listas Usuarios Autorizados", APLICACIONES,
            _one(FileName.USUARIOS_AUTORIZADOS, C.USUARIOS_AUTORIZADOS)))
_reg(Fuente("epps-ae", "EPPS AE", APLICACIONES,
            _one(FileName.EPPS_AE, C.AUDITORIA_ORACLE)))
_reg(Fuente("epps-ac", "EPPS AC", APLICACIONES,
            _one(FileName.EPPS_AC, C.AUDITORIA_ORACLE)))
_reg(Fuente("igwprd-ac", "IGWPRD AC", APLICACIONES,
            _one(FileName.IGWPRD_AC, C.AUDITORIA_ORACLE)))
_reg(Fuente("igwprd-ae", "IGWPRD AE", APLICACIONES,
            _one(FileName.IGWPRD_AE, C.AUDITORIA_ORACLE)))


def get(fuente_id: str) -> Fuente:
    try:
        return FUENTES[fuente_id]
    except KeyError:
        raise KeyError(f"Fuente no registrada: {fuente_id!r}") from None
