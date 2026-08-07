"""Preferencias de interfaz que sobreviven al cierre de la app.

Usa `QSettings`, que en Windows escribe en el registro bajo
`HKCU\\Software\\Pacífico Seguros\\Certificación de Accesos`. No requiere
permisos de administrador ni una ruta de disco: es la vía estándar de Qt y
funciona igual desde el ejecutable empaquetado con PyInstaller.

Aquí solo van preferencias de presentación. Nada de datos de negocio ni de
rutas de archivos cargados: eso vive en `DATA_PATH` y no debe mezclarse.
"""

from __future__ import annotations

from PySide6.QtCore import QByteArray, QSettings


def _settings() -> QSettings:
    # El nombre de organización y de aplicación los fija `main.py` sobre el
    # QApplication, así que este constructor los toma solo.
    return QSettings()


# ---------------------------------------------------------------------------
# Geometría de la ventana
# ---------------------------------------------------------------------------


def guardar_geometria(datos: QByteArray) -> None:
    _settings().setValue("ventana/geometria", datos)


def leer_geometria() -> QByteArray | None:
    valor = _settings().value("ventana/geometria")
    return valor if isinstance(valor, QByteArray) and not valor.isEmpty() else None


# ---------------------------------------------------------------------------
# Panel lateral de estado de archivos
# ---------------------------------------------------------------------------


def guardar_panel(visible: bool | None) -> None:
    """`None` = modo automático según el ancho (no hay decisión del usuario)."""
    ajustes = _settings()
    if visible is None:
        ajustes.remove("cargar/panel_visible")
    else:
        ajustes.setValue("cargar/panel_visible", bool(visible))


def leer_panel() -> bool | None:
    valor = _settings().value("cargar/panel_visible")
    if valor is None:
        return None
    # QSettings devuelve "true"/"false" como texto en algunas plataformas.
    if isinstance(valor, str):
        return valor.lower() == "true"
    return bool(valor)


# ---------------------------------------------------------------------------
# Anchos de columna del diálogo de datos, por fuente
# ---------------------------------------------------------------------------


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
        # Preferencia corrupta: se ignora y se recalculan los anchos.
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


# ---------------------------------------------------------------------------
# Última vista abierta
# ---------------------------------------------------------------------------


def guardar_ultima_vista(ruta: str) -> None:
    _settings().setValue("ventana/ultima_vista", ruta)


def leer_ultima_vista() -> str:
    valor = _settings().value("ventana/ultima_vista")
    return str(valor) if valor else ""
