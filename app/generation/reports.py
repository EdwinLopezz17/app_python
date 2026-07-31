"""
GENERACIÓN DE HALLAZGOS
=======================

Única frontera de salida con `logic/`. Aquí se declara, por hallazgo, qué
función de reporte lo produce; el resto de la aplicación no importa nada de
`logic/` directamente.

`logic/` NO se toca: estos adaptadores solo lo invocan y convierten la lista de
dataclasses que devuelve en un DataFrame, respetando el orden de campos de
`models/reports/`.

Sobre `reporte_dbs.py`: a diferencia de los otros reportes, no expone una
función pública — solo `_rows_vida` y `_rows_generales`, que reciben los
servicios ya construidos. Se invocan tal cual, armando los servicios aquí. Si
más adelante el backend agrega un `get_db_report()` público, basta con cambiar
el adaptador correspondiente.
"""

from __future__ import annotations

from dataclasses import fields, is_dataclass
from datetime import date
from typing import Callable

import pandas as pd

from app.generation.compat import puente_parquet


def a_dataframe(filas: list) -> pd.DataFrame:
    """
    Convierte la lista de dataclasses de un reporte en DataFrame.

    Conserva el orden de campos declarado en `models/reports/` y preserva los
    tipos (bool sigue siendo bool, datetime sigue siendo datetime) para que
    Parquet los guarde correctamente y la tabla los muestre bien.
    """
    if not filas:
        return pd.DataFrame()

    primera = filas[0]
    if not is_dataclass(primera):
        return pd.DataFrame(filas)

    columnas = [f.name for f in fields(primera)]
    datos = {c: [getattr(fila, c, None) for fila in filas] for c in columnas}
    return pd.DataFrame(datos, columns=columnas)


# ---------------------------------------------------------------------------
# Adaptadores. Cada uno recibe la fecha de corte y devuelve un DataFrame.
# ---------------------------------------------------------------------------

def _generar_aplicaciones(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.app_report import get_app_report

    # get_app_report() no recibe fecha de corte: la lógica de escenarios de
    # Aplicaciones no la usa.
    return a_dataframe(get_app_report())


def _generar_active_directory(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.ad_report import get_ad_report

    return a_dataframe(get_ad_report(fecha_ref))


def _servicios_bd():
    """Servicios compartidos que requieren los reportes de base de datos."""
    from logic.share.services.ad_service import ADService
    from logic.share.services.dni_vs_user_service import DNIUserService
    from logic.share.services.gdh_service import GDHUserService
    from logic.share.services.tickets_report import TicketInfoService

    return (DNIUserService(), ADService(), GDHUserService(), TicketInfoService())


def _generar_bd_vida(fecha_ref: date) -> pd.DataFrame:
    from logic.base_datos.reports.reporte_dbs import _rows_vida

    dni_srv, ad_srv, gdh_srv, ticket_srv = _servicios_bd()
    return a_dataframe(_rows_vida(fecha_ref, dni_srv, ad_srv, gdh_srv, ticket_srv))


def _generar_bd_generales(fecha_ref: date) -> pd.DataFrame:
    from logic.base_datos.reports.reporte_dbs import _rows_generales

    dni_srv, ad_srv, gdh_srv, ticket_srv = _servicios_bd()
    return a_dataframe(_rows_generales(fecha_ref, dni_srv, ad_srv, gdh_srv, ticket_srv))


def _generar_perfiles(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.profiles_report import get_profiles_report

    return a_dataframe(get_profiles_report())


def _generar_activos_gdh(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.gdh_report import gdh_report

    # La función se llama `gdh_report`, sin prefijo `get_`, a diferencia de los
    # demás reportes. Se respeta el nombre tal como está en `logic/`.
    return a_dataframe(gdh_report())


def _generales(clave: str) -> pd.DataFrame:
    """
    Generales y Especiales devuelve un dict con dos conjuntos de filas: los
    accesos AC y los AE. Cada uno es un hallazgo independiente en la aplicación.

    A diferencia de los otros reportes, las filas son diccionarios y no
    dataclasses, y sus claves ya vienen en español legible, así que se usan
    directamente como cabeceras.
    """
    from logic.generals.reports.generals_report import generate_report

    resultado = generate_report()
    filas = resultado.get(clave, [])
    return pd.DataFrame(filas) if filas else pd.DataFrame()


def _generar_generales_ac(fecha_ref: date) -> pd.DataFrame:
    return _generales("hallazgos_ac")


def _generar_generales_ae(fecha_ref: date) -> pd.DataFrame:
    return _generales("hallazgos_ae")


# hallazgo_id -> función generadora
GENERADORES: dict[str, Callable[[date], pd.DataFrame]] = {
    "aplicaciones": _generar_aplicaciones,
    "active-directory": _generar_active_directory,
    "bd-vida": _generar_bd_vida,
    "bd-generales": _generar_bd_generales,
    "perfiles": _generar_perfiles,
    "activos-gdh": _generar_activos_gdh,
    "generales-ac": _generar_generales_ac,
    "generales-ae": _generar_generales_ae,
}


def disponible(hallazgo_id: str) -> bool:
    return hallazgo_id in GENERADORES


def generar(hallazgo_id: str, fecha_ref: date) -> pd.DataFrame:
    generador = GENERADORES.get(hallazgo_id)
    if generador is None:
        raise NotImplementedError(
            f"La generación de «{hallazgo_id}» aún no está conectada."
        )
    # El puente permite que los servicios de `logic/`, que todavía piden .csv,
    # lean los .parquet que escribe la aplicación. Ver app/generation/compat.py.
    with puente_parquet():
        return generador(fecha_ref)
