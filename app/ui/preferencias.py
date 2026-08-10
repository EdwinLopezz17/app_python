
from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings


def _settings() -> QSettings:
    return QSettings()


def guardar_geometria(datos: QByteArray) -> None:
    _settings().setValue("ventana/geometria", datos)


def leer_geometria() -> QByteArray | None:
    valor = _settings().value("ventana/geometria")
    return valor if isinstance(valor, QByteArray) and not valor.isEmpty() else None


def guardar_panel(visible: bool | None) -> None:
    ajustes = _settings()
    if visible is None:
        ajustes.remove("cargar/panel_visible")
    else:
        ajustes.setValue("cargar/panel_visible", bool(visible))


def leer_panel() -> bool | None:
    valor = _settings().value("cargar/panel_visible")
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor.lower() == "true"
    return bool(valor)


def guardar_columnas(clave: str, anchos: list[int]) -> None:
    if not anchos:
        return
    _settings().setValue(f"datos/columnas/{clave}", ",".join(str(a) for a in anchos))


def leer_columnas(clave: str) -> list[int]:
    valor = _settings().value(f"datos/columnas/{clave}")
    if not valor:
        return []
    try:
        return [int(parte) for parte in str(valor).split(",") if parte]
    except ValueError:
        return []


def guardar_tamano_dialogo(ancho: int, alto: int) -> None:
    ajustes = _settings()
    ajustes.setValue("datos/ancho", int(ancho))
    ajustes.setValue("datos/alto", int(alto))


def leer_tamano_dialogo() -> tuple[int, int] | None:
    ajustes = _settings()
    ancho = ajustes.value("datos/ancho")
    alto = ajustes.value("datos/alto")
    if ancho is None or alto is None:
        return None
    try:
        return int(ancho), int(alto)
    except (TypeError, ValueError):
        return None


def guardar_ultima_vista(ruta: str) -> None:
    _settings().setValue("ventana/ultima_vista", ruta)


def leer_ultima_vista() -> str:
    valor = _settings().value("ventana/ultima_vista")
    return str(valor) if valor else ""
