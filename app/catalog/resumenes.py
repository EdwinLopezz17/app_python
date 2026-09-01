from __future__ import annotations

from app.catalog import resumen_base_datos, resumen_perfiles, resumen_usuarios
from app.resumen.engine import ConfigResumen


COLUMNAS_EDITABLES = resumen_usuarios.COLUMNAS_EDITABLES

_FUENTES = (
    resumen_usuarios.CONFIGS,
    resumen_base_datos.CONFIGS,
    resumen_perfiles.CONFIGS,
)

CONFIGS: dict[str, ConfigResumen] = {}
for _fuente in _FUENTES:
    CONFIGS.update(_fuente)


def disponible(hallazgo_id: str) -> bool:
    return hallazgo_id in CONFIGS


def get(hallazgo_id: str) -> ConfigResumen:
    try:
        return CONFIGS[hallazgo_id]
    except KeyError:
        raise KeyError(f"Hallazgo sin resumen configurado: {hallazgo_id!r}") from None
