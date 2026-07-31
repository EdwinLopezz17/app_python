"""
LECTOR ÚNICO DE ARCHIVOS DE ORIGEN  (.csv / .xls / .xlsx)
=========================================================

Port de `src/lib/excel/read-as-text.ts`. Regla innegociable: TODO se lee como
TEXTO, sin inferencia de tipos. Motivo (ya sufrido en la versión Next):

  * Si el lector infiere fechas, "01/02/2025" se reinterpreta según el locale y
    puede salir como 02/01/2025, o convertirse en un serial de Excel (45689).
  * Si infiere números, un DNI "00123456" pierde los ceros a la izquierda.
  * Si infiere nulos, el literal "NA" de un campo de texto se vuelve NaN.

Por eso: `dtype=str`, `keep_default_na=False`, `na_filter=False`. La conversión
a tipos reales es responsabilidad de los servicios de `logic/`, que ya saben qué
formato tiene cada campo.

Detalles de CSV que este módulo resuelve y que rompen silenciosamente:

  1. BOM: se detecta y elimina A NIVEL DE BYTES, antes de decodificar. Hacerlo
     sobre el texto ya decodificado falla cuando el decoder cae a windows-1252 y
     el BOM aparece como los tres caracteres literales "ï»¿" pegados al nombre de
     la primera columna.
  2. Encoding: utf-8 estricto y, si falla, windows-1252 (lo que produce Excel en
     español por defecto).
  3. Separador: se detecta entre ; , tabulador y | contando ocurrencias en la
     cabecera. Los reportes del alcance vienen con ';' pero no todos.
  4. CSV doblemente codificado: algunos exports serializan cada fila como CSV y
     luego la envuelven como una única celda entrecomillada. El resultado es un
     DataFrame de UNA sola columna cuyo nombre es la cabecera entera. Se detecta
     y se desenvuelve.
"""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd

_BOM_UTF8 = b"\xef\xbb\xbf"
_SEPARADORES = [";", ",", "\t", "|"]

EXTENSIONES_EXCEL = {".xls", ".xlsx", ".xlsm"}
EXTENSIONES_CSV = {".csv", ".txt"}


class ErrorDeLectura(Exception):
    """El archivo no se pudo leer (formato no soportado, corrupto, vacío)."""


def strip_bom_bytes(data: bytes) -> bytes:
    """Elimina el BOM UTF-8 a nivel de bytes. Ver punto 1 del docstring."""
    return data[len(_BOM_UTF8):] if data.startswith(_BOM_UTF8) else data


def decodificar(data: bytes) -> str:
    """UTF-8 estricto con respaldo a windows-1252."""
    data = strip_bom_bytes(data)
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252", errors="replace")


def detectar_separador(primera_linea: str) -> str:
    """Elige el separador que más aparece en la cabecera."""
    conteos = {sep: primera_linea.count(sep) for sep in _SEPARADORES}
    mejor = max(conteos, key=conteos.get)
    return mejor if conteos[mejor] > 0 else ";"


def _desenvolver_csv_doble(df: pd.DataFrame) -> pd.DataFrame:
    """
    Repara el caso 'CSV dentro de CSV': una sola columna cuyo nombre contiene el
    separador. Se vuelve a parsear el contenido completo. Ver punto 4.
    """
    if df.shape[1] != 1:
        return df

    cabecera = str(df.columns[0])
    sep = detectar_separador(cabecera)
    if cabecera.count(sep) == 0:
        return df  # columna única legítima (p. ej. Prophet, que solo trae CORREO)

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


def _leer_excel(path: Path) -> pd.DataFrame:
    # cabecera en la fila 0; el resto como texto crudo.
    return pd.read_excel(path, dtype=str, keep_default_na=False, na_filter=False)


def leer_como_texto(path: str | Path) -> pd.DataFrame:
    """
    Lee un archivo de origen y devuelve un DataFrame donde TODAS las celdas son
    str. Las cabeceras se devuelven tal cual vienen (sin normalizar): la
    normalización es responsabilidad de quien compara.
    """
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

    # Garantía final: nada queda como NaN ni como número.
    df.columns = [str(c) for c in df.columns]
    return df.fillna("").astype(str)


def leer_cabeceras(path: str | Path) -> list[str]:
    """Solo la primera fila. Se usa para validar antes de procesar el archivo entero."""
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

        # CSV doblemente codificado: toda la cabecera vino como UNA celda
        # entrecomillada. Hay que desenvolverla aquí también, porque la
        # validación de columnas usa esta función y si no, rechazaría el archivo
        # antes de que `leer_como_texto` tuviera oportunidad de repararlo.
        if len(cabeceras) == 1 and cabeceras[0].count(sep) > 0:
            cabeceras = cabeceras[0].split(sep)

        return cabeceras

    if ext in EXTENSIONES_EXCEL:
        df = pd.read_excel(path, dtype=str, nrows=0)
        return [str(c) for c in df.columns]

    raise ErrorDeLectura(f"Formato no soportado: {ext}")
