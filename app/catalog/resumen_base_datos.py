from __future__ import annotations

from app.catalog import hallazgo_columns as cols
from app.resumen.engine import ConfigResumen, Escenario


# El resumen de BD del frontend (export-resumen-bd.ts) evalúa los flags con
# isPositive (modo "positivo"), no con coincidencia exacta de "X". Se replica
# aquí para que los conteos cuadren celda por celda con el Next.js.
CAMPO_MONITOREO = "nombre_archivo"
ETIQUETA_MONITOREO = "Escenarios de monitoreo"


def _columnas(modelo: str) -> tuple[str, ...]:
    return tuple(cols.etiquetas(modelo))


ESCENARIOS_BD_GENERALES: tuple[Escenario, ...] = (
    Escenario(
        code="H1_GENERALES",
        title="Colaboradores Cesados con cuenta activa",
        flag="is_cesado_activo",
        modo="positivo",
        reporta_responsable=True,
        columnas=_columnas("DBGeneralsRow"),
    ),
    Escenario(
        code="H2_GENERALES",
        title="Usuarios no identificados o sin sustento",
        flag="is_no_identificado",
        modo="positivo",
        reporta_responsable=True,
        columnas=_columnas("DBGeneralsRow"),
    ),
    Escenario(
        code="H3_GENERALES",
        title="Usuarios sin uso más de 90 días",
        flag="is_sin_uso_90d",
        modo="positivo",
        reporta_responsable=False,
        columnas=_columnas("DBGeneralsRow"),
    ),
    Escenario(
        code="H4_GENERALES",
        title="Usuarios que no fueron cesados oportunamente",
        flag="is_no_cesado_oportunamente",
        modo="positivo",
        reporta_responsable=False,
        columnas=_columnas("DBGeneralsRow"),
    ),
    Escenario(
        code="H5_GENERALES",
        title="Usuarios Deshabilitados mayor a 6 meses",
        flag="is_deshabilitado_180d",
        modo="positivo",
        reporta_responsable=False,
        columnas=_columnas("DBGeneralsRow"),
    ),
)


ESCENARIOS_BD_VIDA: tuple[Escenario, ...] = (
    Escenario(
        code="H1_VIDA",
        title="Colaboradores Cesados con cuenta activa",
        flag="is_cesado_activo",
        modo="positivo",
        reporta_responsable=True,
        columnas=_columnas("DBVidaRow"),
    ),
    Escenario(
        code="H2_VIDA",
        title="Usuarios no identificados o sin sustento",
        flag="is_no_identificado",
        modo="positivo",
        reporta_responsable=True,
        columnas=_columnas("DBVidaRow"),
    ),
    Escenario(
        code="H3_VIDA",
        title="Usuarios sin uso más de 90 días",
        flag="is_sin_uso_90d",
        modo="positivo",
        reporta_responsable=False,
        columnas=_columnas("DBVidaRow"),
    ),
)


CONFIGS: dict[str, ConfigResumen] = {
    "bd-generales": ConfigResumen(
        hallazgo_id="bd-generales",
        modelo="DBGeneralsRow",
        escenarios=ESCENARIOS_BD_GENERALES,
        archivo="resumen-hallazgos-bd-generales.xlsx",
        titulo="Base de Datos SOX GENERALES",
        campo_grupo=CAMPO_MONITOREO,
        etiqueta_grupo=ETIQUETA_MONITOREO,
    ),
    "bd-vida": ConfigResumen(
        hallazgo_id="bd-vida",
        modelo="DBVidaRow",
        escenarios=ESCENARIOS_BD_VIDA,
        archivo="resumen-hallazgos-bd-vida.xlsx",
        titulo="Base de Datos SOX VIDA",
        campo_grupo=CAMPO_MONITOREO,
        etiqueta_grupo=ETIQUETA_MONITOREO,
    ),
}
