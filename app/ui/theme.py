from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QFontDatabase

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

SECONDARY = "#006d38"
SECONDARY_SOFT = "#e7f8ee"
TERTIARY = "#964400"
TERTIARY_SOFT = "#fff1e6"
ERROR = "#ba1a1a"
ERROR_SOFT = "#ffdad6"

TABLA_CABECERA_BG = "#dae2fd"
TABLA_CABECERA_FG = "#131b2e"
TABLA_CABECERA_BORDE = "#8f9bb3"
TABLA_ZEBRA = "#f4f6ff"
TABLA_SELECCION_BG = "#bfe3f2"
TABLA_GRID = "#cfd6e4"

SIDEBAR_BG = "#283044"
SIDEBAR_FG = "#eef0ff"
SIDEBAR_MUTED = "#98a2bd"
SIDEBAR_WIDTH = 260

RADIO_SM = 4
RADIO_LG = 8

FUENTE = "Inter"
FUENTE_RESPALDO = "Segoe UI"


def cargar_fuentes() -> str:
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

QWidget#TopBar {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-bottom: 1px solid {OUTLINE_VARIANT};
}}
QLabel#Titulo {{ font-size: 24px; font-weight: 600; }}
QLabel#Breadcrumb {{ color: {ON_SURFACE_VARIANT}; font-size: 12px; }}

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

QFrame#Card {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QFrame#Card[estado="cargado"] {{ border-color: {SECONDARY}; }}
QFrame#Card[estado="error"] {{ border-color: {ERROR}; }}
QLabel#CardTitulo {{ font-size: 15px; font-weight: 600; }}

QWidget[soltar="activa"] {{
    background: {SECONDARY_SOFT};
    border: 2px dashed {PRIMARY};
    border-radius: {RADIO_SM}px;
}}

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

QDialog {{ background: {SURFACE}; }}
QDialog QLabel {{ color: {ON_SURFACE}; }}

QTableView {{
    background: {SURFACE_CONTAINER_LOWEST};
    alternate-background-color: {TABLA_ZEBRA};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
    gridline-color: {TABLA_GRID};
    font-size: 13px;
    color: {ON_SURFACE};
    selection-background-color: {TABLA_SELECCION_BG};
    selection-color: {ON_SURFACE};
}}
QTableView::item {{ padding: 4px 8px; }}
QTableView::item:selected {{
    background: {TABLA_SELECCION_BG};
    color: {ON_SURFACE};
}}

QHeaderView {{
    background: {TABLA_CABECERA_BG};
    border: none;
}}
QHeaderView::section {{
    background: {TABLA_CABECERA_BG};
    color: {TABLA_CABECERA_FG};
    border: none;
    border-bottom: 2px solid {TABLA_CABECERA_BORDE};
    border-right: 1px solid {TABLA_CABECERA_BORDE};
    padding: 9px 12px;
    font-size: 12px; font-weight: 700; letter-spacing: 0.3px;
}}
QHeaderView::section:last {{ border-right: none; }}
QHeaderView::section:hover {{ background: {SURFACE_CONTAINER_HIGH}; }}
QHeaderView::section:vertical {{
    border-right: 2px solid {TABLA_CABECERA_BORDE};
    border-bottom: 1px solid {TABLA_CABECERA_BORDE};
}}
QTableCornerButton::section {{
    background: {TABLA_CABECERA_BG};
    border: none;
    border-bottom: 2px solid {TABLA_CABECERA_BORDE};
    border-right: 2px solid {TABLA_CABECERA_BORDE};
}}

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

QFrame#Alerta {{ border-radius: {RADIO_SM}px; border: 1px solid transparent; }}
QFrame#Alerta[tono="error"] {{ background: {ERROR_SOFT}; border-color: {ERROR}; }}
QFrame#Alerta[tono="info"]  {{ background: {TERTIARY_SOFT}; border-color: {TERTIARY}; }}
QLabel#AlertaTitulo {{ font-size: 12px; font-weight: 700; }}
QFrame#Alerta[tono="error"] QLabel#AlertaTitulo {{ color: {ERROR}; }}
QFrame#Alerta[tono="info"]  QLabel#AlertaTitulo {{ color: {TERTIARY}; }}
QLabel#AlertaDetalle {{ font-size: 11px; color: {ON_SURFACE_VARIANT}; }}

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
