"""
Normalización de cabeceras para comparación tolerante.

Port directo de `normHeader` de `src/features/usuarios/cargar/validate-fuente.ts`.
Es el ÚNICO punto de normalización de nombres de columna en toda la aplicación:
lo usan la validación, el consolidado de varios archivos y la escritura final.
Si dos lugares normalizan distinto, aparecen bugs silenciosos de columnas que
"no hacen match" sin razón visible.

Pasos, en orden:
  1. NFD + quitar diacríticos          -> "Á" == "A"
  2. quitar caracteres invisibles      -> BOM, zero-width, soft hyphen
  3. NBSP / tab / saltos -> espacio
  4. recortar y quitar comillas envolventes
  5. colapsar espacios internos
  6. MAYÚSCULAS

Con esto, 'ï»¿"samaccountname"' y 'SAMACCOUNTNAME' se consideran la misma columna.
"""

from __future__ import annotations

import re
import unicodedata

# Invisibles que se cuelan al exportar desde PowerShell / Excel / Entra y que
# rompen el match sin dejar rastro visible. str.strip() NO los elimina.
_INVISIBLES = re.compile(
    "["
    "\ufeff"  # BOM / zero-width no-break space
    "\u200b"  # zero-width space
    "\u200c"  # zero-width non-joiner
    "\u200d"  # zero-width joiner
    "\u00ad"  # soft hyphen
    "\u2060"  # word joiner
    "]"
)

# Comillas envolventes (solo en los bordes, nunca en medio del texto).
_COMILLAS_BORDE = re.compile(r'^["\'\u201c\u2018\u201d\u2019]+|["\'\u201c\u2018\u201d\u2019]+$')

# BOM mal decodificado como latin-1, solo al inicio.
_BOM_MAL_DECODIFICADO = re.compile("^\u00ef\u00bb\u00bf")

_ESPACIOS_RAROS = re.compile("[\u00a0\t\r\n]+")
_ESPACIOS_MULTIPLES = re.compile(r"\s+")


def norm_header(s: object) -> str:
    """Normaliza una cabecera para compararla de forma tolerante."""
    texto = "" if s is None else str(s)

    # 1) BOM mal decodificado ("ï»¿"), ANTES de normalizar.
    #
    #    El orden es crítico y aquí se corrige un bug que la versión TypeScript
    #    todavía arrastra: si primero se aplica NFD, la "ï" se descompone en
    #    "i" + diéresis combinante, la diéresis se elimina como cualquier otro
    #    diacrítico, y el patrón "ï»¿" ya no existe para poder detectarlo. El
    #    resultado es una cabecera "I»¿SAMACCOUNTNAME" que nunca hace match.
    texto = _BOM_MAL_DECODIFICADO.sub("", texto)

    # 2) descomponer y eliminar diacríticos combinantes
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))

    # 3) invisibles (BOM real U+FEFF, zero-width, soft hyphen, word joiner)
    texto = _INVISIBLES.sub("", texto)

    # 3) espacios raros a espacio normal
    texto = _ESPACIOS_RAROS.sub(" ", texto)

    # 4) recortar, quitar comillas de los bordes, recortar de nuevo
    texto = _COMILLAS_BORDE.sub("", texto.strip()).strip()

    # 5) colapsar espacios internos
    texto = _ESPACIOS_MULTIPLES.sub(" ", texto)

    return texto.upper()


def norm_headers(headers) -> list[str]:
    return [norm_header(h) for h in headers]
