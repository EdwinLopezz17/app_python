from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from datetime import date, datetime
from typing import Callable

import pandas as pd


def a_dataframe(filas: list) -> pd.DataFrame:
    if not filas:
        return pd.DataFrame()

    primera = filas[0]
    if not is_dataclass(primera):
        return pd.DataFrame(filas)

    columnas = [f.name for f in fields(primera)]
    datos = {c: [getattr(fila, c, None) for fila in filas] for c in columnas}
    return pd.DataFrame(datos, columns=columnas)


def _generar_aplicaciones(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.app_report import get_app_report

    return a_dataframe(get_app_report())


def _generar_active_directory(fecha_ref: date) -> pd.DataFrame:
    from logic.usuarios.reports.ad_report import get_ad_report

    return a_dataframe(get_ad_report(fecha_ref))


def _servicios_bd():
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

    return a_dataframe(gdh_report())


def _generales(clave: str) -> pd.DataFrame:
    from logic.generals.reports.generals_report import generate_report

    resultado = generate_report()
    filas = resultado.get(clave, [])
    return pd.DataFrame(filas) if filas else pd.DataFrame()


def _generar_generales_ac(fecha_ref: date) -> pd.DataFrame:
    return _generales("hallazgos_ac")


def _generar_generales_ae(fecha_ref: date) -> pd.DataFrame:
    return _generales("hallazgos_ae")


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


# ---------------------------------------------------------------------------
# Registro en memoria de la última generación de la sesión.
#
# No hay caché en disco: el resultado vive en la tabla de la vista mientras la
# app esté abierta. Este registro solo guarda los metadatos (filas y hora)
# para que la vista y el launcher puedan mostrar "generado hh:mm".
# Al cerrar la app se pierde, y es el comportamiento esperado.
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Generado:
    filas: int
    generado_en: datetime

    @property
    def generado_texto(self) -> str:
        return self.generado_en.strftime("%d/%m/%Y %H:%M")


_GENERADOS: dict[str, Generado] = {}


def ultimo(hallazgo_id: str) -> Generado | None:
    return _GENERADOS.get(hallazgo_id)


def olvidar(hallazgo_id: str) -> None:
    _GENERADOS.pop(hallazgo_id, None)


def generar(hallazgo_id: str, fecha_ref: date) -> pd.DataFrame:
    generador = GENERADORES.get(hallazgo_id)
    if generador is None:
        raise NotImplementedError(
            f"La generación de «{hallazgo_id}» aún no está conectada."
        )
    df = generador(fecha_ref)
    _GENERADOS[hallazgo_id] = Generado(
        filas=len(df), generado_en=datetime.now()
    )
    return df
