from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass

from app.__version__ import (
    GITHUB_OWNER, GITHUB_REPO, __version__, es_mas_nueva,
)

TIMEOUT = 12
AGENTE = "CertificacionAccesos-Updater"

URL_API = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
URL_RAW = (
    f"https://raw.githubusercontent.com/{GITHUB_OWNER}/{GITHUB_REPO}"
    "/main/version.json"
)


@dataclass(frozen=True)
class Actualizacion:
    version: str
    url: str
    sha256: str
    notas: str
    tamano: int = 0

    @property
    def hay_novedad(self) -> bool:
        return es_mas_nueva(self.version, __version__)


class ErrorRed(RuntimeError):
    pass


def _contexto_permisivo() -> ssl.SSLContext:
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def abrir(url: str, timeout: int = TIMEOUT):
    peticion = urllib.request.Request(url, headers={"User-Agent": AGENTE})
    try:
        return urllib.request.urlopen(peticion, timeout=timeout)
    except urllib.error.URLError as exc:
        if isinstance(exc.reason, ssl.SSLError):
            return urllib.request.urlopen(
                peticion, timeout=timeout, context=_contexto_permisivo()
            )
        raise


def _leer_json(url: str) -> dict:
    try:
        with abrir(url) as respuesta:
            return json.loads(respuesta.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise ErrorRed(f"El servidor respondió {exc.code} al consultar {url}") from exc
    except Exception as exc:
        raise ErrorRed(f"No se pudo contactar con el servidor: {exc}") from exc


def _desde_api(datos: dict) -> Actualizacion | None:
    version = str(datos.get("tag_name") or "").strip()
    if not version:
        return None

    asset = None
    for candidato in datos.get("assets") or []:
        nombre = str(candidato.get("name") or "").lower()
        if nombre.endswith(".exe") and "setup" in nombre:
            asset = candidato
            break

    if asset is None:
        return None

    sha = ""
    digest = str(asset.get("digest") or "")
    if digest.startswith("sha256:"):
        sha = digest.split(":", 1)[1]

    return Actualizacion(
        version=version,
        url=str(asset.get("browser_download_url") or ""),
        sha256=sha,
        notas=str(datos.get("body") or "").strip(),
        tamano=int(asset.get("size") or 0),
    )


def _desde_raw(datos: dict) -> Actualizacion | None:
    version = str(datos.get("version") or "").strip()
    url = str(datos.get("url") or "").strip()
    if not version or not url:
        return None
    return Actualizacion(
        version=version,
        url=url,
        sha256=str(datos.get("sha256") or "").strip().lower(),
        notas=str(datos.get("notas") or "").strip(),
        tamano=int(datos.get("tamano") or 0),
    )


def buscar_actualizacion() -> Actualizacion | None:
    fallos = []

    try:
        info = _desde_api(_leer_json(URL_API))
        if info is not None:
            return info if info.hay_novedad else None
    except ErrorRed as exc:
        fallos.append(str(exc))

    try:
        info = _desde_raw(_leer_json(URL_RAW))
        if info is not None:
            return info if info.hay_novedad else None
    except ErrorRed as exc:
        fallos.append(str(exc))

    if fallos:
        raise ErrorRed(" | ".join(fallos))

    return None
