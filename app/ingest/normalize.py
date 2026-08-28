from __future__ import annotations

import re
import unicodedata

_INVISIBLES = re.compile(
    "["
    "\ufeff"
    "\u200b"
    "\u200c"
    "\u200d"
    "\u00ad"
    "\u2060"
    "]"
)

_COMILLAS_BORDE = re.compile(r'^["\'\u201c\u2018\u201d\u2019]+|["\'\u201c\u2018\u201d\u2019]+$')

_BOM_MAL_DECODIFICADO = re.compile("^\u00ef\u00bb\u00bf")

_ESPACIOS_RAROS = re.compile("[\u00a0\t\r\n]+")
_ESPACIOS_MULTIPLES = re.compile(r"\s+")


def norm_header(s: object) -> str:
    texto = "" if s is None else str(s)

    texto = _BOM_MAL_DECODIFICADO.sub("", texto)

    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    texto = _INVISIBLES.sub("", texto)

    texto = _ESPACIOS_RAROS.sub(" ", texto)

    texto = _COMILLAS_BORDE.sub("", texto.strip()).strip()

    texto = _ESPACIOS_MULTIPLES.sub(" ", texto)

    return texto.upper()


def norm_headers(headers) -> list[str]:
    return [norm_header(h) for h in headers]


_SECUENCIA_MOJIBAKE = re.compile(
    "(?:[\\u00c2-\\u00df][\\u0080-\\u00bf]"
    "|\\u00e0[\\u00a0-\\u00bf][\\u0080-\\u00bf]"
    "|[\\u00e1-\\u00ef][\\u0080-\\u00bf]{2}"
    "|\\u00f0[\\u0090-\\u00bf][\\u0080-\\u00bf]{2}"
    "|[\\u00f1-\\u00f3][\\u0080-\\u00bf]{3})+"
)

_MARCADORES_MOJIBAKE = ("\u00c3", "\u00c2", "\u00e2\u0080")


def _decodificar_segmento(segmento: str) -> str:
    try:
        return segmento.encode("cp1252").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    try:
        return segmento.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return segmento


def reparar_mojibake(texto: str) -> str:
    if not texto:
        return texto
    if not any(marca in texto for marca in _MARCADORES_MOJIBAKE):
        return texto

    reparado = _SECUENCIA_MOJIBAKE.sub(
        lambda m: _decodificar_segmento(m.group(0)), texto
    )

    if any(marca in reparado for marca in _MARCADORES_MOJIBAKE):
        return _SECUENCIA_MOJIBAKE.sub(
            lambda m: _decodificar_segmento(m.group(0)), reparado
        )
    return reparado


def limpiar_celda(texto: str) -> str:
    if not texto:
        return texto

    texto = reparar_mojibake(texto)
    texto = _INVISIBLES.sub("", texto)
    texto = texto.replace("\u00a0", " ")
    texto = texto.strip()

    return texto
