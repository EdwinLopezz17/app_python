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
import math
from datetime import date, datetime, time
from decimal import Decimal
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


# ---------------------------------------------------------------------------
# Conversión de celda a texto  (el corazón del bug del ".0")
# ---------------------------------------------------------------------------
#
# `pd.read_excel(dtype=str)` NO lee como texto: deja que openpyxl/xlrd
# interpreten la celda y recién después hace `astype(str)`. Una celda con el
# número 123 llega a pandas como float 123.0 y termina escrita como "123.0".
# Lo mismo pasa con códigos largos ("2000000000001" -> "2e+12") y con fechas
# reales de Excel, que llegan como serial y se reformatean.
#
# La única forma de leer TEXTO de verdad es tomar el valor nativo de la celda y
# convertirlo nosotros, con reglas explícitas. Eso es lo que hace `texto_celda`.


def texto_celda(valor: object) -> str:
    """Convierte el valor nativo de una celda a texto SIN perder información."""
    if valor is None:
        return ""

    if isinstance(valor, str):
        return valor

    # bool antes que int: en Python, bool ES subclase de int.
    if isinstance(valor, bool):
        return "TRUE" if valor else "FALSE"

    # datetime antes que date: datetime ES subclase de date.
    # Se escribe en ISO (YYYY-MM-DD) a propósito: es el único formato que
    # `logic/share/utils.to_datetime` interpreta igual con dayfirst=True y con
    # dayfirst=False. Con "01/02/2025" el resultado depende del servicio que lo
    # lea, y ahí es donde aparecen los meses y días intercambiados.
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
        # 123.0 -> "123". Es el caso que rompía los códigos de usuario.
        if valor.is_integer() and abs(valor) < 1e16:
            return str(int(valor))
        return _sin_notacion_cientifica(repr(valor))

    if isinstance(valor, Decimal):
        if valor == valor.to_integral_value():
            return str(int(valor))
        return _sin_notacion_cientifica(format(valor.normalize(), "f"))

    return str(valor)


def _sin_notacion_cientifica(texto: str) -> str:
    """'2e+12' -> '2000000000000'. Excel muestra el número, no el exponente."""
    if "e" not in texto.lower():
        return texto
    try:
        return format(Decimal(texto), "f")
    except Exception:
        return texto


def _cabeceras_unicas(cabeceras: list[str]) -> list[str]:
    """Desambigua columnas repetidas igual que pandas: NOMBRE, NOMBRE.1, ..."""
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
    """Excel arrastra columnas/filas fantasma al final. Se descartan."""
    fin = len(valores)
    while fin > 0 and (valores[fin - 1] is None or str(valores[fin - 1]).strip() == ""):
        fin -= 1
    return valores[:fin]


def _leer_xlsx(path: Path) -> pd.DataFrame:
    """Lee .xlsx/.xlsm con openpyxl en modo streaming, celda por celda."""
    from openpyxl import load_workbook

    # data_only=True: si la celda tiene fórmula se toma el valor calculado, no
    # el texto "=BUSCARV(...)". read_only=True: no carga el libro entero en RAM.
    libro = load_workbook(path, read_only=True, data_only=True)
    try:
        hoja = libro[libro.sheetnames[0]]
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
            if any(c.strip() for c in celdas):  # descarta filas totalmente vacías
                datos.append(celdas)
    finally:
        libro.close()

    return pd.DataFrame(datos, columns=cabeceras, dtype=object)


def _leer_xls(path: Path) -> pd.DataFrame:
    """
    .xls (formato binario antiguo) solo lo lee xlrd, vía pandas.

    Aquí sí pasa por el intérprete de pandas, pero se pide `dtype=object` para
    que NO haga el `astype(str)` que produce el ".0": la conversión la hace
    `texto_celda`, celda por celda, con las mismas reglas que el .xlsx.
    """
    df = pd.read_excel(path, dtype=object, keep_default_na=False, na_filter=False)
    return df.map(texto_celda) if hasattr(df, "map") else df.applymap(texto_celda)


def _leer_excel(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xls":
        return _leer_xls(path)
    return _leer_xlsx(path)


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
    #
    # OJO: aquí NO se usa `.astype(str)` a secas. Si una columna quedara como
    # float, `astype(str)` es justamente lo que produce el "123.0". Se pasa cada
    # valor por `texto_celda`, que ya sabe que 123.0 es 123.
    df.columns = [str(c) for c in df.columns]
    df = df.map(texto_celda) if hasattr(df, "map") else df.applymap(texto_celda)
    return df


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
        # Misma ruta de lectura que `leer_como_texto`, para que la validación
        # nunca vea una cabecera distinta de la que se va a cargar. Una cabecera
        # numérica leída con pandas llegaría como "1.0" y no haría match.
        if ext == ".xls":
            df = pd.read_excel(path, dtype=object, nrows=0)
            return [texto_celda(c) for c in df.columns]

        from openpyxl import load_workbook

        libro = load_workbook(path, read_only=True, data_only=True)
        try:
            hoja = libro[libro.sheetnames[0]]
            cruda = next(hoja.iter_rows(min_row=1, max_row=1, values_only=True), None)
        finally:
            libro.close()
        if cruda is None:
            raise ErrorDeLectura(f"El archivo no tiene cabecera: {path.name}")
        return _cabeceras_unicas(
            [texto_celda(c) for c in _recortar_cola_vacia(list(cruda))]
        )

    raise ErrorDeLectura(f"Formato no soportado: {ext}")
