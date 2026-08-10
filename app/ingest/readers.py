from __future__ import annotations

import io
import math
import re
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path

import pandas as pd

_BOM_UTF8 = b"\xef\xbb\xbf"
_SEPARADORES = [";", ",", "\t", "|"]

EXTENSIONES_EXCEL = {".xls", ".xlsx", ".xlsm"}
EXTENSIONES_CSV = {".csv", ".txt"}


class ErrorDeLectura(Exception):
    pass


def strip_bom_bytes(data: bytes) -> bytes:
    return data[len(_BOM_UTF8):] if data.startswith(_BOM_UTF8) else data


def decodificar(data: bytes) -> str:
    data = strip_bom_bytes(data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def detectar_separador(primera_linea: str) -> str:
    conteos = {sep: primera_linea.count(sep) for sep in _SEPARADORES}
    mejor = max(conteos, key=conteos.get)
    return mejor if conteos[mejor] > 0 else ";"


def _desenvolver_csv_doble(df: pd.DataFrame) -> pd.DataFrame:
    if df.shape[1] != 1:
        return df

    cabecera = str(df.columns[0])
    sep = detectar_separador(cabecera)
    if cabecera.count(sep) == 0:
        return df

    lineas = [cabecera] + [str(v) for v in df.iloc[:, 0].tolist()]
    texto = "\n".join(lineas)
    return pd.read_csv(
        io.StringIO(texto), sep=sep, dtype=str,
        keep_default_na=False, na_filter=False, engine="python",
    )


def _leer_csv(path: Path) -> pd.DataFrame:
    texto = decodificar(path.read_bytes())
    if not texto.strip():
        raise ErrorDeLectura(f"El archivo está vacío: {path.name}")

    primera = texto.splitlines()[0] if texto.splitlines() else ""
    sep = detectar_separador(primera)

    df = pd.read_csv(
        io.StringIO(texto), sep=sep, dtype=str,
        keep_default_na=False, na_filter=False, engine="python",
    )
    return _desenvolver_csv_doble(df)


_ENTERO_CON_DECIMAL_CERO = re.compile(r"[+-]?\d+\.0+")
_CIENTIFICA = re.compile(r"[+-]?\d+(?:\.\d+)?[eE][+-]?\d+")


def normalizar_numero_texto(texto: str) -> str:
    if "." not in texto and "e" not in texto and "E" not in texto:
        return texto

    limpio = texto.strip()
    if not limpio:
        return texto

    if _ENTERO_CON_DECIMAL_CERO.fullmatch(limpio):
        return limpio.split(".", 1)[0]

    if _CIENTIFICA.fullmatch(limpio):
        try:
            numero = Decimal(limpio)
        except Exception:
            return texto
        if numero == numero.to_integral_value():
            return str(int(numero))
        return format(numero, "f")

    return texto


def texto_celda(valor: object) -> str:
    if valor is None:
        return ""

    if isinstance(valor, str):
        return normalizar_numero_texto(valor)

    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"

    if isinstance(valor, datetime):
        sin_hora = (
            valor.hour == 0 and valor.minute == 0
            and valor.second == 0 and valor.microsecond == 0
        )
        return valor.strftime("%Y-%m-%d" if sin_hora else "%Y-%m-%d %H:%M:%S")
    if isinstance(valor, date):
        return valor.strftime("%Y-%m-%d")
    if isinstance(valor, time):
        return valor.strftime("%H:%M:%S")

    if isinstance(valor, int):
        return str(valor)

    if isinstance(valor, float):
        if math.isnan(valor) or math.isinf(valor):
            return ""
        if valor.is_integer() and abs(valor) < 1e16:
            return str(int(valor))
        return _sin_notacion_cientifica(repr(valor))

    if isinstance(valor, Decimal):
        if valor == valor.to_integral_value():
            return str(int(valor))
        return _sin_notacion_cientifica(format(valor.normalize(), "f"))

    return str(valor)


def _sin_notacion_cientifica(texto: str) -> str:
    if "e" not in texto.lower():
        return texto
    try:
        return format(Decimal(texto), "f")
    except Exception:
        return texto


def _cabeceras_unicas(cabeceras: list[str]) -> list[str]:
    vistas: dict[str, int] = {}
    salida: list[str] = []
    for indice, bruta in enumerate(cabeceras):
        nombre = bruta.strip() or f"Columna_{indice + 1}"
        if nombre in vistas:
            vistas[nombre] += 1
            nombre = f"{nombre}.{vistas[nombre]}"
        else:
            vistas[nombre] = 0
        salida.append(nombre)
    return salida


def _recortar_cola_vacia(valores: list) -> list:
    fin = len(valores)
    while fin > 0 and (valores[fin - 1] is None or str(valores[fin - 1]).strip() == ""):
        fin -= 1
    return valores[:fin]


def _hoja_principal(libro):
    hoja = libro[libro.sheetnames[0]]
    if hasattr(hoja, "reset_dimensions"):
        hoja.reset_dimensions()
    return hoja


def _leer_xlsx(path: Path) -> pd.DataFrame:
    from openpyxl import load_workbook

    libro = load_workbook(path, read_only=True, data_only=True)
    try:
        hoja = _hoja_principal(libro)
        filas = hoja.iter_rows(values_only=True)

        try:
            cruda = next(filas)
        except StopIteration:
            raise ErrorDeLectura(f"El archivo no tiene cabecera: {path.name}") from None

        cabeceras = _cabeceras_unicas(
            [texto_celda(c) for c in _recortar_cola_vacia(list(cruda))]
        )
        if not cabeceras:
            raise ErrorDeLectura(f"El archivo no tiene cabecera: {path.name}")

        ancho = len(cabeceras)
        datos: list[list[str]] = []
        for fila in filas:
            celdas = [texto_celda(v) for v in fila][:ancho]
            if len(celdas) < ancho:
                celdas += [""] * (ancho - len(celdas))
            if any(c.strip() for c in celdas):
                datos.append(celdas)
    finally:
        libro.close()

    return pd.DataFrame(datos, columns=cabeceras, dtype=object)


def _leer_xls(path: Path) -> pd.DataFrame:
    df = pd.read_excel(path, dtype=object, keep_default_na=False, na_filter=False)
    return df.map(texto_celda) if hasattr(df, "map") else df.applymap(texto_celda)


def _leer_excel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xls":
        return _leer_xls(path)
    return _leer_xlsx(path)


def leer_como_texto(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if not path.exists():
        raise ErrorDeLectura(f"No existe el archivo: {path}")

    ext = path.suffix.lower()
    if ext in EXTENSIONES_CSV:
        df = _leer_csv(path)
    elif ext in EXTENSIONES_EXCEL:
        df = _leer_excel(path)
    else:
        raise ErrorDeLectura(f"Formato no soportado: {ext}")

    df.columns = [str(c) for c in df.columns]
    df = df.map(texto_celda) if hasattr(df, "map") else df.applymap(texto_celda)
    return df


def leer_cabeceras(path: str | Path) -> list[str]:
    path = Path(path)
    ext = path.suffix.lower()

    if ext in EXTENSIONES_CSV:
        with open(path, "rb") as fh:
            crudo = fh.readline()
        linea = decodificar(crudo).rstrip("\r\n")
        if not linea:
            raise ErrorDeLectura(f"El archivo no tiene cabecera: {path.name}")
        sep = detectar_separador(linea)
        cabeceras = next(iter(
            pd.read_csv(io.StringIO(linea), sep=sep, dtype=str, header=None,
                        keep_default_na=False, na_filter=False,
                        engine="python").itertuples(index=False, name=None)
        ))
        cabeceras = [str(c) for c in cabeceras]

        if len(cabeceras) == 1 and cabeceras[0].count(sep) > 0:
            cabeceras = cabeceras[0].split(sep)

        return cabeceras

    if ext in EXTENSIONES_EXCEL:
        if ext == ".xls":
            df = pd.read_excel(path, dtype=object, nrows=0)
            return [texto_celda(c) for c in df.columns]

        from openpyxl import load_workbook

        libro = load_workbook(path, read_only=True, data_only=True)
        try:
            hoja = _hoja_principal(libro)
            cruda = next(hoja.iter_rows(min_row=1, max_row=1, values_only=True), None)
        finally:
            libro.close()
        if cruda is None:
            raise ErrorDeLectura(f"El archivo no tiene cabecera: {path.name}")
        return _cabeceras_unicas(
            [texto_celda(c) for c in _recortar_cola_vacia(list(cruda))]
        )

    raise ErrorDeLectura(f"Formato no soportado: {ext}")
