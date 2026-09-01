from __future__ import annotations

import codecs
from dataclasses import dataclass
from pathlib import Path

from app import config
from app.telemetry import uso

_BOM_UTF8 = b"\xef\xbb\xbf"
_BLOQUE = 1024 * 256

FUENTES_POR_HALLAZGO: dict[str, tuple[str, ...]] = {
    "active-directory": (
        "ad_consolidado.csv",
        "dni_vs_usuarios.csv",
        "entra_id.csv",
        "activos_gdh.csv",
        "cesados_gdh.csv",
        "tickets_ceses.csv",
    ),
    "bd-vida": (
        "db_vida.csv",
        "ad_consolidado.csv",
        "dni_vs_usuarios.csv",
        "activos_gdh.csv",
        "cesados_gdh.csv",
        "tickets_ceses.csv",
    ),
    "bd-generales": (
        "db_generales.csv",
        "ad_consolidado.csv",
        "dni_vs_usuarios.csv",
        "activos_gdh.csv",
        "cesados_gdh.csv",
        "tickets_ceses.csv",
    ),
    "activos-gdh": ("activos_gdh.csv", "cesados_gdh.csv"),
    "generales-ac": ("usuarios_autorizados.csv", "epps_ac.csv", "igwprd_ac.csv"),
    "generales-ae": ("usuarios_autorizados.csv", "epps_ae.csv", "igwprd_ae.csv"),
}


class ErrorDeCodificacion(Exception):
    pass


def revisar_env() -> Defecto | None:
    from app.config import raiz_datos

    ruta = raiz_datos() / ".env"
    if not ruta.exists():
        return None
    return revisar_archivo(ruta)


def reparar_env() -> str:
    from app.config import raiz_datos

    ruta = raiz_datos() / ".env"
    if not ruta.exists():
        return "ausente"

    crudo = ruta.read_bytes()
    if crudo.startswith(_BOM_UTF8):
        cuerpo = crudo[len(_BOM_UTF8):]
        try:
            texto = cuerpo.decode("utf-8")
        except UnicodeDecodeError:
            return "ilegible"
        ruta.write_bytes(texto.encode("utf-8"))
        uso.registrar("env_reparado", motivo="BOM eliminado", ruta=str(ruta))
        return "reparado"

    try:
        crudo.decode("utf-8")
        return "ok"
    except UnicodeDecodeError:
        pass

    for codificacion in ("cp1252", "latin-1"):
        try:
            texto = crudo.decode(codificacion)
        except UnicodeDecodeError:
            continue
        respaldo = ruta.with_name(".env.ansi.bak")
        try:
            respaldo.write_bytes(crudo)
        except OSError:
            pass
        ruta.write_bytes(texto.encode("utf-8"))
        uso.registrar(
            "env_reparado",
            motivo=f"reescrito desde {codificacion}",
            ruta=str(ruta),
            respaldo=str(respaldo),
        )
        return "reparado"

    uso.registrar("env_irreparable", ruta=str(ruta))
    return "ilegible"


@dataclass(frozen=True)
class Defecto:
    archivo: str
    ruta: Path
    posicion: int
    linea: int
    byte: int
    contexto: str


def _contexto(datos: bytes, posicion: int, radio: int = 45) -> str:
    inicio = max(0, posicion - radio)
    fin = min(len(datos), posicion + radio)
    crudo = datos[inicio:fin].decode("cp1252", errors="replace")
    return " ".join(crudo.split())


def revisar_archivo(ruta: Path) -> Defecto | None:
    decodificador = codecs.getincrementaldecoder("utf-8")()
    consumidos = 0
    lineas = 1
    anterior = b""

    try:
        with ruta.open("rb") as fuente:
            primero = True
            while True:
                bloque = fuente.read(_BLOQUE)
                if not bloque:
                    break
                if primero:
                    primero = False
                    if bloque.startswith(_BOM_UTF8):
                        bloque = bloque[len(_BOM_UTF8):]
                try:
                    decodificador.decode(bloque)
                except UnicodeDecodeError as exc:
                    posicion = consumidos + exc.start
                    lineas += bloque[: exc.start].count(b"\n")
                    muestra = anterior + bloque
                    local = len(anterior) + exc.start
                    return Defecto(
                        archivo=ruta.name,
                        ruta=ruta,
                        posicion=posicion,
                        linea=lineas,
                        byte=muestra[local],
                        contexto=_contexto(muestra, local),
                    )
                lineas += bloque.count(b"\n")
                consumidos += len(bloque)
                anterior = bloque[-256:]
            decodificador.decode(b"", final=True)
    except UnicodeDecodeError:
        return Defecto(
            archivo=ruta.name, ruta=ruta, posicion=consumidos,
            linea=lineas, byte=0, contexto="fin de archivo truncado",
        )
    except OSError:
        return None

    return None


def _archivos_de(hallazgo_id: str) -> list[Path]:
    base = config.data_path()
    nombres = FUENTES_POR_HALLAZGO.get(hallazgo_id)
    if nombres is None:
        return sorted(base.glob("*.csv"))
    return [base / n for n in nombres]


def _mensaje(defectos: list[Defecto]) -> str:
    lineas = [
        "Hay archivos que no están en UTF-8 y el motor de reportes "
        "no puede leerlos.",
        "",
    ]
    for d in defectos:
        lineas.append(f"• {d.archivo}")
        lineas.append(f"    línea {d.linea}, byte 0x{d.byte:02x} (posición {d.posicion})")
        lineas.append(f"    texto: …{d.contexto}…")
        lineas.append("")

    lineas.append("Cómo se corrige:")
    lineas.append(
        "  Si el archivo es .env: ábrelo con el Bloc de notas, usa «Guardar "
        "como» y elige codificación UTF-8."
    )
    lineas.append(
        "  1. Ve a «Cargar Información» y vuelve a subir esa fuente desde el "
        "archivo original."
    )
    lineas.append(
        "  2. Si lo abriste en Excel, guárdalo como «CSV UTF-8 (delimitado por "
        "comas)», no como «CSV»."
    )
    lineas.append(
        "  3. No copies archivos directamente a la carpeta de datos: la app los "
        "convierte sola al cargarlos."
    )
    lineas.append("")
    lineas.append(f"Detalle completo en: {uso.ruta_texto()}")
    return "\n".join(lineas)


def verificar(hallazgo_id: str) -> None:
    defectos: list[Defecto] = []
    revisados = 0

    defecto_env = revisar_env()
    if defecto_env is not None:
        if reparar_env() == "reparado":
            defecto_env = revisar_env()
        if defecto_env is not None:
            defectos.append(defecto_env)

    for ruta in _archivos_de(hallazgo_id):
        if not ruta.exists():
            continue
        revisados += 1
        defecto = revisar_archivo(ruta)
        if defecto is not None:
            defectos.append(defecto)

    if not defectos:
        uso.registrar("precheck_ok", hallazgo=hallazgo_id, archivos=revisados)
        return

    for d in defectos:
        uso.registrar(
            "precheck_encoding",
            hallazgo=hallazgo_id,
            archivo=d.archivo,
            ruta=str(d.ruta),
            linea=d.linea,
            posicion=d.posicion,
            byte=f"0x{d.byte:02x}",
            contexto=d.contexto,
        )

    raise ErrorDeCodificacion(_mensaje(defectos))
