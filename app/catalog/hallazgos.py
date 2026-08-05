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
    usa_fecha_corte: bool = False
    #: Fuentes sin las cuales el reporte no puede ejecutarse. Si queda vacío,
    #: se asume que TODAS las fuentes del hallazgo son obligatorias (que es el
    #: comportamiento histórico). Las que no estén aquí son opcionales: el
    #: hallazgo se genera igual y simplemente no aporta filas esa fuente.
    requeridas: list[str] = field(default_factory=list)

    @property
    def fuentes(self) -> list[Fuente]:
        return [get_fuente(fid) for fid in self.fuente_ids]

    @property
    def requeridas_efectivas(self) -> list[str]:
        return list(self.requeridas) if self.requeridas else list(self.fuente_ids)

    def es_opcional(self, fuente_id: str) -> bool:
        return fuente_id not in self.requeridas_efectivas

    @property
    def fuentes_requeridas(self) -> list[Fuente]:
        return [get_fuente(fid) for fid in self.requeridas_efectivas]

    @property
    def fuentes_opcionales(self) -> list[Fuente]:
        return [get_fuente(fid) for fid in self.fuente_ids if self.es_opcional(fid)]

    @property
    def slots_requeridos(self) -> list:
        return [s for f in self.fuentes_requeridas for s in f.slots]

    @property
    def slots_opcionales(self) -> list:
        return [s for f in self.fuentes_opcionales for s in f.slots]


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
        # Las aplicaciones son opcionales: se puede certificar con las que ya
        # estén cargadas. Lo obligatorio es el núcleo de identidad/RRHH.
        requeridas=["dni-vs-usuarios", "gdh", "ad", "entra-id", "tickets-ceses"],
    ),
    Hallazgo(
        id="active-directory",
        usa_fecha_corte=True,
        label="Active Directory",
        cert_id="usuarios",
        cert_label="Certificación de Usuarios",
        modelo="ADRows",
        descripcion="Cuentas de Active Directory contrastadas con GDH y ceses.",
        fuente_ids=["dni-vs-usuarios", "gdh", "entra-id", "ad", "tickets-ceses"],
    ),

    Hallazgo(
        id="bd-vida",
        usa_fecha_corte=True,
        label="BD Vida",
        cert_id="base-datos",
        cert_label="Certificación de Base de Datos",
        modelo="DBVidaRow",
        descripcion="Accesos a las bases de datos de Vida (SQL Server).",
        fuente_ids=[*_BASE, "db-vida"],
    ),
    Hallazgo(
        id="bd-generales",
        usa_fecha_corte=True,
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
            "dni-vs-usuarios", "matriz-roles", "rol-ticket", "gdh", "ad",
            "entra-id",
            "acselx", "onbase", "sox-vida", "eas", "billing-center",
            "claim-center", "contact-manager", "policycenter", "prophet",
            "pms", "salesforce", "siniestros-web", "exactus-perfiles",
            "botmaker",
        ],
        requeridas=[
            "dni-vs-usuarios", "matriz-roles", "rol-ticket", "gdh", "ad",
            "entra-id",
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
        requeridas=["usuarios-autorizados"],
    ),
    Hallazgo(
        id="generales-ae",
        label="Generales AE",
        cert_id="generales",
        cert_label="Certificación de Generales y Especiales",
        modelo="GeneralsRow",
        descripcion="Accesos a bases de datos del entorno AE (EPPS e IGWPRD).",
        fuente_ids=["usuarios-autorizados", "epps-ae", "igwprd-ae"],
        requeridas=["usuarios-autorizados"],
    ),
]


HALLAZGOS_BY_ID: dict[str, Hallazgo] = {h.id: h for h in HALLAZGOS}


@dataclass(frozen=True)
class Certificacion:
    id: str
    label: str
    hallazgos: list[Hallazgo]
    descripcion: str = ""

    @property
    def label_corto(self) -> str:
        return self.label.replace("Certificación de ", "")

    @property
    def landing(self) -> str:
        return self.hallazgos[0].id


CERT_DESCRIPCIONES: dict[str, str] = {
    "usuarios": "Hallazgos de acceso de usuarios en aplicaciones y Active Directory.",
    "base-datos": "Hallazgos de accesos a bases de datos y Active Directory.",
    "perfiles": "Auditoría de perfiles de aplicación, dueños y segregación de funciones.",
    "generales": "Hallazgos de la certificación de Generales y Especiales.",
}


def certificaciones() -> list[Certificacion]:
    orden: list[str] = []
    agrupado: dict[str, list[Hallazgo]] = {}
    for h in HALLAZGOS:
        if h.cert_id not in agrupado:
            agrupado[h.cert_id] = []
            orden.append(h.cert_id)
        agrupado[h.cert_id].append(h)
    return [
        Certificacion(
            cid,
            agrupado[cid][0].cert_label,
            agrupado[cid],
            CERT_DESCRIPCIONES.get(cid, ""),
        )
        for cid in orden
    ]


def get(hallazgo_id: str) -> Hallazgo:
    try:
        return HALLAZGOS_BY_ID[hallazgo_id]
    except KeyError:
        raise KeyError(f"Hallazgo no registrado: {hallazgo_id!r}") from None
