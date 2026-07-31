"""
Design system "Corporate Minimalist" traducido a Qt.

Los tokens son los mismos del frontend Next.js (primary #006386, Inter, radios
de 4 y 8 px, densidad de tabla de 13 px). Se declaran UNA vez aquí y de ahí sale
todo el QSS: cambiar el azul corporativo es cambiar una línea.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase

# ─────────────────────────────── Tokens ────────────────────────────────────

SURFACE = "#faf8ff"
SURFACE_CONTAINER_LOWEST = "#ffffff"
SURFACE_CONTAINER_LOW = "#f2f3ff"
SURFACE_CONTAINER = "#eaedff"
SURFACE_CONTAINER_HIGH = "#e2e7ff"

ON_SURFACE = "#131b2e"
ON_SURFACE_VARIANT = "#3e484f"
OUTLINE = "#6e7880"
OUTLINE_VARIANT = "#bdc8d0"

PRIMARY = "#006386"
PRIMARY_HOVER = "#007da8"
ON_PRIMARY = "#ffffff"

SECONDARY = "#006d38"          # estados "cargado" / completo
SECONDARY_SOFT = "#e7f8ee"
TERTIARY = "#964400"           # advertencias / pendientes
TERTIARY_SOFT = "#fff1e6"
ERROR = "#ba1a1a"
ERROR_SOFT = "#ffdad6"

SIDEBAR_BG = "#283044"
SIDEBAR_FG = "#eef0ff"
SIDEBAR_MUTED = "#98a2bd"
SIDEBAR_WIDTH = 260

RADIO_SM = 4
RADIO_LG = 8

FUENTE = "Inter"
FUENTE_RESPALDO = "Segoe UI"


def cargar_fuentes() -> str:
    """
    Registra Inter si está empaquetada en app/ui/fonts/.

    En la red corporativa no hay salida a CDN (el mismo motivo por el que en
    Next se auto-hospeda con next/font/local), así que la fuente viaja con la
    aplicación. Si no está, se cae a Segoe UI, que existe en todo Windows.
    """
    carpeta = Path(__file__).parent / "fonts"
    if carpeta.is_dir():
        for archivo in sorted(carpeta.glob("*.ttf")) + sorted(carpeta.glob("*.otf")):
            if QFontDatabase.addApplicationFont(str(archivo)) != -1:
                return FUENTE
    disponibles = set(QFontDatabase.families())
    return FUENTE if FUENTE in disponibles else FUENTE_RESPALDO


def qss(familia: str = FUENTE) -> str:
    return f"""
* {{
    font-family: "{familia}", "{FUENTE_RESPALDO}", sans-serif;
    font-size: 14px;
    color: {ON_SURFACE};
}}

QMainWindow, QWidget#Canvas {{ background: {SURFACE}; }}

/* ─────────────────────── Barra de navegación superior ───────────────── */
/* Sustituye al antiguo sidebar oscuro: el frontend de Next.js no tenía uno,
   y la barra horizontal deja todo el ancho disponible para las cards.        */
QWidget#NavBar {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-bottom: 1px solid {OUTLINE_VARIANT};
}}
QLabel#Marca {{ font-size: 15px; font-weight: 700; color: {PRIMARY}; }}
QLabel#Submarca {{
    color: {ON_SURFACE_VARIANT}; font-size: 10px; font-weight: 600;
    letter-spacing: 1.2px;
}}
QPushButton#NavTab {{
    background: transparent; color: {ON_SURFACE_VARIANT}; border: none;
    border-bottom: 2px solid transparent;
    padding: 10px 14px; font-size: 13px; font-weight: 600;
}}
QPushButton#NavTab:hover {{ color: {PRIMARY}; background: {SURFACE_CONTAINER_LOW}; }}
QPushButton#NavTab:checked {{
    color: {PRIMARY}; border-bottom: 2px solid {PRIMARY};
}}

/* ───────────────────────────── Top bar ──────────────────────────────── */
QWidget#TopBar {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-bottom: 1px solid {OUTLINE_VARIANT};
}}
QLabel#Titulo {{ font-size: 24px; font-weight: 600; }}
QLabel#Breadcrumb {{ color: {ON_SURFACE_VARIANT}; font-size: 12px; }}

/* ───────────────────────────── Botones ──────────────────────────────── */
QPushButton {{
    background: {PRIMARY}; color: {ON_PRIMARY}; border: none;
    border-radius: {RADIO_SM}px; padding: 8px 16px; font-weight: 600; font-size: 13px;
}}
QPushButton:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton:disabled {{ background: {OUTLINE_VARIANT}; color: #ffffff; }}

QPushButton[variante="ghost"] {{
    background: transparent; color: {ON_SURFACE_VARIANT};
    border: 1px solid {OUTLINE_VARIANT};
}}
QPushButton[variante="ghost"]:hover {{
    border-color: {PRIMARY}; color: {PRIMARY}; background: {SURFACE_CONTAINER_LOW};
}}
QPushButton[variante="peligro"] {{ background: {ERROR}; }}
QPushButton[variante="peligro"]:hover {{ background: #93000a; }}

/* ────────────────────────────── Cards ───────────────────────────────── */
QFrame#Card {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QFrame#Card[estado="cargado"] {{ border-color: {SECONDARY}; }}
QFrame#Card[estado="error"] {{ border-color: {ERROR}; }}
QLabel#CardTitulo {{ font-size: 15px; font-weight: 600; }}

/* Zona activa mientras se arrastra un archivo encima */
QWidget[soltar="activa"] {{
    background: {SECONDARY_SOFT};
    border: 2px dashed {PRIMARY};
    border-radius: {RADIO_SM}px;
}}

/* ─────────────────────── Cards del lanzador ─────────────────────────── */
QFrame#CardCert {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QFrame#CardCert:hover {{ border: 1px solid {PRIMARY}; }}
QLabel#CardCertTitulo {{ font-size: 17px; font-weight: 700; }}
QLabel#CardCertDesc {{ color: {ON_SURFACE_VARIANT}; font-size: 12px; }}

QFrame#CardHallazgo {{
    background: {SURFACE_CONTAINER_LOW};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
}}
QFrame#CardHallazgo:hover {{
    background: {SURFACE_CONTAINER}; border-color: {PRIMARY};
}}
QLabel#HallazgoTitulo {{ font-size: 14px; font-weight: 600; }}
QLabel#HallazgoMeta {{ color: {ON_SURFACE_VARIANT}; font-size: 11px; }}

QPushButton[variante="mini"] {{
    padding: 5px 10px; font-size: 12px; font-weight: 600;
}}
QLabel#Kpi {{ font-size: 26px; font-weight: 700; color: {PRIMARY}; }}
QLabel#KpiEtiqueta {{
    color: {ON_SURFACE_VARIANT}; font-size: 11px; font-weight: 600;
    letter-spacing: 0.5px;
}}
QFrame#KpiCard {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}

QLabel#CardMeta {{ color: {ON_SURFACE_VARIANT}; font-size: 12px; }}

QLabel#Badge {{
    border-radius: {RADIO_SM}px; padding: 3px 9px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.4px;
}}
QLabel#Badge[tono="pendiente"] {{ background: {SURFACE_CONTAINER}; color: {ON_SURFACE_VARIANT}; }}
QLabel#Badge[tono="ok"]        {{ background: {SECONDARY_SOFT}; color: {SECONDARY}; }}
QLabel#Badge[tono="aviso"]     {{ background: {TERTIARY_SOFT}; color: {TERTIARY}; }}
QLabel#Badge[tono="error"]     {{ background: {ERROR_SOFT}; color: {ERROR}; }}

QLabel#Seccion {{
    color: {ON_SURFACE_VARIANT}; font-size: 12px; font-weight: 600;
    letter-spacing: 1px;
}}

/* ────────────────────────────── Tablas ──────────────────────────────── */
QTableView {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
    gridline-color: {SURFACE_CONTAINER};
    font-size: 13px;
    selection-background-color: {SURFACE_CONTAINER_HIGH};
    selection-color: {ON_SURFACE};
}}
QHeaderView::section {{
    background: {SURFACE_CONTAINER_LOW};
    color: {ON_SURFACE_VARIANT};
    border: none;
    border-bottom: 1px solid {OUTLINE_VARIANT};
    border-right: 1px solid {SURFACE_CONTAINER};
    padding: 8px 12px;
    font-size: 11px; font-weight: 700; letter-spacing: 0.5px;
}}

/* ───────────────────────── Inputs y varios ──────────────────────────── */
QLineEdit {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px; padding: 7px 10px;
}}
QLineEdit:focus {{ border: 2px solid {PRIMARY}; }}

QProgressBar {{
    background: {SURFACE_CONTAINER};
    border: none; border-radius: 2px; height: 4px; text-align: center;
}}
QProgressBar::chunk {{ background: {PRIMARY}; border-radius: 2px; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 0; }}
QScrollBar::handle:vertical {{
    background: {OUTLINE_VARIANT}; border-radius: 5px; min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{ background: {OUTLINE}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}

/* ─────────────────────────── Menús desplegables ─────────────────────── */
/* Sin esta regla, QMenu hereda el tema del sistema (fondo oscuro) y el
   texto azul corporativo queda ilegible encima.                          */
QMenu {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
    padding: 6px 0;
}}
QMenu::item {{
    background: transparent;
    color: {ON_SURFACE};
    padding: 8px 28px 8px 18px;
    font-size: 13px;
    font-weight: 600;
}}
QMenu::item:selected {{
    background: {SURFACE_CONTAINER_HIGH};
    color: {PRIMARY};
}}
QMenu::item:disabled {{ color: {OUTLINE_VARIANT}; }}
QMenu::separator {{
    height: 1px;
    background: {OUTLINE_VARIANT};
    margin: 4px 10px;
}}

QToolTip {{
    background: {SIDEBAR_BG}; color: {SIDEBAR_FG};
    border: none; border-radius: {RADIO_SM}px; padding: 6px 8px;
}}


/* ─────────────────────────── Selector de fecha ──────────────────────── */
QDateEdit {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
    padding: 7px 10px;
    min-width: 130px;
    font-weight: 600;
}}
QDateEdit:hover {{ border-color: {PRIMARY}; }}
QDateEdit:focus {{ border: 2px solid {PRIMARY}; padding: 6px 9px; }}
QDateEdit::drop-down {{
    subcontrol-origin: padding; subcontrol-position: center right;
    width: 30px; border: none;
    border-left: 1px solid {OUTLINE_VARIANT};
    background: {SURFACE_CONTAINER_LOW};
    border-top-right-radius: {RADIO_SM}px;
    border-bottom-right-radius: {RADIO_SM}px;
}}
QDateEdit::drop-down:hover {{ background: {SURFACE_CONTAINER_HIGH}; }}
/* El indicador por defecto de Qt se ve como una flecha desalineada; se
   sustituye por un glifo de calendario dibujado con el propio widget.        */
QDateEdit::down-arrow {{ image: none; width: 0; height: 0; }}
QLabel#IconoCalendario {{
    color: {ON_SURFACE_VARIANT}; font-size: 14px;
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: {PRIMARY}; border-top-left-radius: {RADIO_LG}px;
    border-top-right-radius: {RADIO_LG}px; min-height: 36px;
}}
QCalendarWidget QToolButton {{
    color: {ON_PRIMARY}; background: transparent; border: none;
    font-size: 13px; font-weight: 600; padding: 4px 10px;
}}
QCalendarWidget QToolButton:hover {{ background: rgba(255,255,255,0.18); border-radius: {RADIO_SM}px; }}
QCalendarWidget QMenu {{ background: {SURFACE_CONTAINER_LOWEST}; }}
QCalendarWidget QAbstractItemView:enabled {{
    background: {SURFACE_CONTAINER_LOWEST};
    color: {ON_SURFACE};
    selection-background-color: {PRIMARY};
    selection-color: {ON_PRIMARY};
    outline: none;
    font-size: 12px;
}}
QCalendarWidget QAbstractItemView:disabled {{ color: {OUTLINE_VARIANT}; }}
QCalendarWidget QWidget {{ alternate-background-color: {SURFACE_CONTAINER_LOW}; }}

/* ───────────────────── Alertas dentro de las cards ──────────────────── */
QFrame#Alerta {{ border-radius: {RADIO_SM}px; border: 1px solid transparent; }}
QFrame#Alerta[tono="error"] {{ background: {ERROR_SOFT}; border-color: {ERROR}; }}
QFrame#Alerta[tono="info"]  {{ background: {TERTIARY_SOFT}; border-color: {TERTIARY}; }}
QLabel#AlertaTitulo {{ font-size: 12px; font-weight: 700; }}
QFrame#Alerta[tono="error"] QLabel#AlertaTitulo {{ color: {ERROR}; }}
QFrame#Alerta[tono="info"]  QLabel#AlertaTitulo {{ color: {TERTIARY}; }}
QLabel#AlertaDetalle {{ font-size: 11px; color: {ON_SURFACE_VARIANT}; }}

/* ────────────────────── Panel lateral de estado ─────────────────────── */
QWidget#PanelEstado {{
    background: {SURFACE_CONTAINER_LOW};
    border-left: 1px solid {OUTLINE_VARIANT};
}}
QWidget#PanelEstadoCabecera {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-bottom: 1px solid {OUTLINE_VARIANT};
    border-left: 1px solid {OUTLINE_VARIANT};
}}
QLabel#PanelTitulo {{ font-size: 14px; font-weight: 700; }}
QLabel#PanelResumen {{ font-size: 12px; }}
QLabel#PanelResumen[tono="ok"] {{ color: {SECONDARY}; font-weight: 600; }}
QLabel#PanelResumen[tono="aviso"] {{ color: {TERTIARY}; font-weight: 600; }}
QPushButton#BotonCerrarPanel {{
    background: transparent; color: {ON_SURFACE_VARIANT};
    border: none; font-size: 13px; padding: 0;
}}
QPushButton#BotonCerrarPanel:hover {{
    background: {SURFACE_CONTAINER}; border-radius: {RADIO_SM}px; color: {ON_SURFACE};
}}
QFrame#FilaEstado {{ background: transparent; border-radius: {RADIO_SM}px; }}
QFrame#FilaEstado:hover {{ background: {SURFACE_CONTAINER_HIGH}; }}
QLabel#FilaEstadoTitulo {{ font-size: 12px; font-weight: 600; }}
QLabel#FilaEstadoMeta {{ font-size: 11px; color: {ON_SURFACE_VARIANT}; }}
QLabel#PuntoEstado {{ font-size: 15px; }}
QLabel#PuntoEstado[tono="ok"] {{ color: {SECONDARY}; }}
QLabel#PuntoEstado[tono="falta"] {{ color: {OUTLINE_VARIANT}; }}
"""
