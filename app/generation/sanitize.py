from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal

import pandas as pd

FORMATO_FECHA = "%d/%m/%Y"
FORMATO_FECHA_HORA = "%d/%m/%Y %H:%M"


def _es_nulo(valor) -> bool:
    if valor is None:
        return True
    if isinstance(valor, float) and pd.isna(valor):
        return True
    return valor is pd.NaT


def _familia(valor) -> str:
    if isinstance(valor, (datetime, pd.Timestamp)):
        return "fecha"
    if isinstance(valor, date):
        return "fecha"
    if isinstance(valor, time):
        return "hora"
    if isinstance(valor, bool):
        return "bool"
    if isinstance(valor, str):
        return "texto"
    if isinstance(valor, int):
        return "entero"
    if isinstance(valor, float):
        return "decimal"
    if isinstance(valor, Decimal):
        return "decimal_exacto"
    if isinstance(valor, (list, tuple, dict, set)):
        return "compuesto"
    return "otro"


def texto_de(valor) -> str:
    if _es_nulo(valor):
        return ""
    if isinstance(valor, (datetime, pd.Timestamp)):
        sin_hora = valor.hour == 0 and valor.minute == 0 and valor.second == 0
        return valor.strftime(FORMATO_FECHA if sin_hora else FORMATO_FECHA_HORA)
    if isinstance(valor, date):
        return valor.strftime(FORMATO_FECHA)
    if isinstance(valor, time):
        return valor.strftime("%H:%M")
    if isinstance(valor, bool):
        return "Sí" if valor else "No"
    return str(valor)


def _necesita_normalizar(serie: pd.Series) -> bool:
    familias: set[str] = set()
    for valor in serie:
        if _es_nulo(valor):
            continue
        familias.add(_familia(valor))
        if len(familias) > 1:
            return True

    if not familias:
        return False

    unica = next(iter(familias))
    return unica in {"otro", "compuesto"}


def normalizar(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    problematicas = [
        col for col in df.columns
        if df[col].dtype == object and _necesita_normalizar(df[col])
    ]
    if not problematicas:
        return df

    salida = df.copy()
    for col in problematicas:
        salida[col] = salida[col].map(texto_de).astype("string")
    return salida


def forzar_texto(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return df

    salida = df.copy()
    for col in salida.columns:
        if salida[col].dtype == object:
            salida[col] = salida[col].map(texto_de).astype("string")
    return salida
