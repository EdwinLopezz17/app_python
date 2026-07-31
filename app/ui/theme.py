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

/* ───────────────────────────── Sidebar ──────────────────────────────── */
QWidget#Sidebar {{ background: {SIDEBAR_BG}; }}
QWidget#Sidebar QLabel {{ color: {SIDEBAR_FG}; }}
QLabel#SidebarMarca {{
    color: {SIDEBAR_FG}; font-size: 16px; font-weight: 700;
    padding: 20px 20px 4px 20px;
}}
QLabel#SidebarSubmarca {{
    color: {SIDEBAR_MUTED}; font-size: 11px; font-weight: 600;
    letter-spacing: 1px; padding: 0 20px 16px 20px;
}}
QLabel#SidebarGrupo {{
    color: {SIDEBAR_MUTED}; font-size: 11px; font-weight: 700;
    letter-spacing: 1px; padding: 16px 20px 6px 20px;
}}
QPushButton#NavItem {{
    color: {SIDEBAR_FG}; background: transparent; border: none;
    text-align: left; padding: 9px 20px; font-size: 13px;
    border-left: 3px solid transparent;
}}
QPushButton#NavItem:hover {{ background: rgba(255,255,255,0.07); }}
QPushButton#NavItem:checked {{
    background: rgba(255,255,255,0.12);
    border-left: 3px solid {PRIMARY_HOVER};
    font-weight: 600;
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

QToolTip {{
    background: {SIDEBAR_BG}; color: {SIDEBAR_FG};
    border: none; border-radius: {RADIO_SM}px; padding: 6px 8px;
}}
"""
