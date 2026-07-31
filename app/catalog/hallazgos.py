from __future__ import annotations

from dataclasses import dataclass, field

from app.catalog.fuentes import Fuente, get as get_fuente


@dataclass(frozen=True)
class Hallazgo:
    id: str
    label: str
    cert_id: str
    cert_label: str
    fuente_ids: list[str] = field(default_factory=list)
    modelo: str | None = None
    descripcion: str = ""

    @property
    def fuentes(self) -> list[Fuente]:
        return [get_fuente(fid) for fid in self.fuente_ids]


_BASE = ["dni-vs-usuarios", "gdh", "ad", "tickets-ceses"]


HALLAZGOS: list[Hallazgo] = [
    Hallazgo(
        id="aplicaciones",
        label="Aplicaciones",
        cert_id="usuarios",
        cert_label="Certificación de Usuarios",
        modelo="AppRows",
        descripcion="Accesos de usuarios en las aplicaciones del alcance.",
        fuente_ids=[
            "dni-vs-usuarios", "gdh", "entra-id", "ad", "tickets-ceses",
            "app-login", "cgweb", "acselx", "billing-center", "claim-center",
            "contact-manager", "policycenter", "eas", "exactus", "onbase",
            "pms", "segcen", "sox-vida", "prophet", "botmaker", "salesforce",
            "addactis", "monokera", "siniestros-web", "datalake", "crm",
            "qualys", "ssa",
        ],
    ),
    Hallazgo(
        id="active-directory",
        label="Active Directory",
        cert_id="usuarios",
        cert_label="Certificación de Usuarios",
        modelo="ADRows",
        descripcion="Cuentas de Active Directory contrastadas con GDH y ceses.",
        fuente_ids=list(_BASE),
    ),

    Hallazgo(
        id="bd-vida",
        label="BD Vida",
        cert_id="base-datos",
        cert_label="Certificación de Base de Datos",
        modelo="DBVidaRow",
        descripcion="Accesos a las bases de datos de Vida (SQL Server).",
        fuente_ids=[*_BASE, "db-vida"],
    ),
    Hallazgo(
        id="bd-generales",
        label="BD Generales",
        cert_id="base-datos",
        cert_label="Certificación de Base de Datos",
        modelo="DBGeneralsRow",
        descripcion="Accesos a las bases de datos de Generales (Oracle).",
        fuente_ids=[*_BASE, "db-generales"],
    ),

    Hallazgo(
        id="perfiles",
        label="Perfiles",
        cert_id="perfiles",
        cert_label="Certificación de Perfiles",
        modelo="ProfileRows",
        descripcion="Perfiles y roles asignados contrastados con la Matriz de Roles.",
        fuente_ids=[
            "dni-vs-usuarios", "matriz-roles", "gdh", "ad", "entra-id",
            "acselx", "onbase", "sox-vida", "eas", "billing-center",
            "claim-center", "contact-manager", "policycenter", "prophet",
            "pms", "salesforce", "siniestros-web", "exactus-perfiles",
            "botmaker",
        ],
    ),
    Hallazgo(
        id="activos-gdh",
        label="Activos GDH",
        cert_id="perfiles",
        cert_label="Certificación de Perfiles",
        modelo="GDHRows",
        descripcion="Colaboradores activos en GDH y su correspondencia de roles.",
        fuente_ids=["dni-vs-usuarios", "matriz-roles", "gdh", "ad", "entra-id"],
    ),

    Hallazgo(
        id="generales-ac",
        label="Generales AC",
        cert_id="generales",
        cert_label="Certificación de Generales y Especiales",
        modelo="GeneralsRow",
        descripcion="Accesos a bases de datos del entorno AC (EPPS e IGWPRD).",
        fuente_ids=["usuarios-autorizados", "epps-ac", "igwprd-ac"],
    ),
    Hallazgo(
        id="generales-ae",
        label="Generales AE",
        cert_id="generales",
        cert_label="Certificación de Generales y Especiales",
        modelo="GeneralsRow",
        descripcion="Accesos a bases de datos del entorno AE (EPPS e IGWPRD).",
        fuente_ids=["usuarios-autorizados", "epps-ae", "igwprd-ae"],
    ),
]


HALLAZGOS_BY_ID: dict[str, Hallazgo] = {h.id: h for h in HALLAZGOS}


@dataclass(frozen=True)
class Certificacion:
    id: str
    label: str
    hallazgos: list[Hallazgo]


def certificaciones() -> list[Certificacion]:
    orden: list[str] = []
    agrupado: dict[str, list[Hallazgo]] = {}
    for h in HALLAZGOS:
        if h.cert_id not in agrupado:
            agrupado[h.cert_id] = []
            orden.append(h.cert_id)
        agrupado[h.cert_id].append(h)
    return [
        Certificacion(cid, agrupado[cid][0].cert_label, agrupado[cid])
        for cid in orden
    ]


def get(hallazgo_id: str) -> Hallazgo:
    try:
        return HALLAZGOS_BY_ID[hallazgo_id]
    except KeyError:
        raise KeyError(f"Hallazgo no registrado: {hallazgo_id!r}") from None
