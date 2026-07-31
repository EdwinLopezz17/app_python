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
