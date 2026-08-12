from __future__ import annotations

from pathlib import Path

from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QTextCharFormat

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
PRIMARY_SOFT = "#dceffa"
ON_PRIMARY = "#ffffff"

SECONDARY = "#006d38"
SECONDARY_SOFT = "#e7f8ee"
TERTIARY = "#964400"
TERTIARY_SOFT = "#fff1e6"
ERROR = "#ba1a1a"
ERROR_SOFT = "#ffdad6"

SIDEBAR_BG = "#283044"
SIDEBAR_FG = "#eef0ff"
SIDEBAR_MUTED = "#98a2bd"
SIDEBAR_MUTED_FUERTE = "#c8d0e4"
SIDEBAR_ELEVADO = "#333d55"
SIDEBAR_ELEVADO_HOVER = "#3f4a66"
SIDEBAR_BORDE = "#454f6b"
SIDEBAR_ACENTO = "#78d1ff"
SIDEBAR_WIDTH = 260
SIDEBAR_WIDTH_COMPACTO = 216

TOPBAR_ALTO = 56

RADIO_SM = 4
RADIO_MD = 6
RADIO_LG = 8

TEXTO_XS = 11
TEXTO_SM = 12
TEXTO_MD = 13
TEXTO_LG = 14

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

/* Acción destructiva secundaria: fantasma con acento rojo, para que no
   compita visualmente con el botón primario de la pantalla. */
QPushButton[variante="ghost"][tono="peligro"] {{
    color: {ERROR}; border: 1px solid {ERROR_SOFT};
}}
QPushButton[variante="ghost"][tono="peligro"]:hover {{
    border-color: {ERROR}; color: {ERROR}; background: {ERROR_SOFT};
}}

QFrame#EstadoVacio {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QLabel#EstadoVacioTitulo {{ font-size: 16px; font-weight: 600; }}
QLabel#EstadoVacioDetalle {{ font-size: 13px; color: {ON_SURFACE_VARIANT}; }}

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

QLabel#CardMeta {{ color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_SM}px; }}

/* Título de cada slot dentro de una card con varios archivos. Antes era un
   setStyleSheet inline en fuente_card.py. */
QLabel#SlotTitulo {{ font-size: {TEXTO_MD}px; font-weight: 600; }}

/* Separador entre slots de una misma card. */
QFrame#SeparadorSlot {{
    border: none; border-top: 1px solid {SURFACE_CONTAINER_HIGH};
    max-height: 1px;
}}

QLabel#Badge {{
    border-radius: {RADIO_SM}px; padding: 3px 9px;
    font-size: 11px; font-weight: 600; letter-spacing: 0.4px;
}}
QLabel#Badge[tono="pendiente"] {{ background: {SURFACE_CONTAINER}; color: {ON_SURFACE_VARIANT}; }}
QLabel#Badge[tono="ok"]        {{ background: {SECONDARY_SOFT}; color: {SECONDARY}; }}
QLabel#Badge[tono="aviso"]     {{ background: {TERTIARY_SOFT}; color: {TERTIARY}; }}
QLabel#Badge[tono="error"]     {{ background: {ERROR_SOFT}; color: {ERROR}; }}

/* Chips de filtro: fantasma cuando están apagados, sólidos suaves cuando el
   filtro está activo. No usan el primario para no competir con el botón de
   acción principal de la pantalla. */
QPushButton[variante="chip"] {{
    background: transparent; color: {ON_SURFACE_VARIANT};
    border: 1px solid {OUTLINE_VARIANT}; border-radius: 14px;
    padding: 5px 13px; font-size: 12px; font-weight: 600;
}}
QPushButton[variante="chip"]:hover {{
    border-color: {PRIMARY}; color: {PRIMARY};
}}
QPushButton[variante="chip"][activo="si"] {{
    background: {PRIMARY}; color: {ON_PRIMARY}; border-color: {PRIMARY};
}}
QPushButton[variante="chip"][activo="si"]:hover {{ background: {PRIMARY_HOVER}; }}
QPushButton[variante="chip"]:disabled {{
    background: transparent; color: {OUTLINE_VARIANT};
    border-color: {OUTLINE_VARIANT};
}}
QPushButton[variante="chip"][tono="error"] {{
    color: {ERROR}; border-color: {ERROR_SOFT};
}}
QPushButton[variante="chip"][tono="error"][activo="si"] {{
    background: {ERROR}; color: {ON_PRIMARY}; border-color: {ERROR};
}}
QPushButton[variante="chip"][tono="error"]:disabled {{
    color: {OUTLINE_VARIANT}; border-color: {OUTLINE_VARIANT};
}}

QLabel#SinResultados {{
    color: {ON_SURFACE_VARIANT}; font-size: 13px;
    padding: 28px 0;
}}

/* ── Barra superior de navegación (equivalente al TopBar.tsx) ───────────────
   OJO: el objectName es "BarraNav", NO "TopBar". Las cuatro vistas usan ya
   "TopBar" para su cabecera clara de control panel; reutilizar ese nombre
   pintaba de navy la franja del título y ambas se fundían en un solo bloque
   oscuro. */
QWidget#BarraNav {{
    background: {SIDEBAR_BG};
    border-bottom: 1px solid {SIDEBAR_BORDE};
}}
QWidget#BarraNav QLabel {{ color: {SIDEBAR_FG}; }}
QFrame#TopBarSep {{ background: {SIDEBAR_BORDE}; border: none; }}
QScrollArea#TopBarScroll {{ background: transparent; border: none; }}
QScrollArea#TopBarScroll > QWidget > QWidget {{ background: transparent; }}
QScrollArea#TopBarScroll QScrollBar:horizontal {{
    height: 4px; background: transparent; margin: 0;
}}
QScrollArea#TopBarScroll QScrollBar::handle:horizontal {{
    background: rgba(255,255,255,0.25); border-radius: 2px; min-width: 30px;
}}
QScrollArea#TopBarScroll QScrollBar::add-line:horizontal,
QScrollArea#TopBarScroll QScrollBar::sub-line:horizontal {{ width: 0; }}

/* Switcher: fondo propio y borde tenue para que se lea como un control y no
   como texto suelto sobre el navy. */
QFrame#CertSwitcher {{
    background: {SIDEBAR_ELEVADO}; border: 1px solid {SIDEBAR_BORDE};
    border-radius: {RADIO_MD}px;
}}
QFrame#CertSwitcher:hover {{ background: {SIDEBAR_ELEVADO_HOVER}; }}
QLabel#CertMarca {{
    background: {PRIMARY_HOVER}; color: {ON_PRIMARY};
    border-radius: {RADIO_MD}px; font-size: {TEXTO_SM}px; font-weight: 700;
}}
QLabel#CertEyebrow {{
    color: {SIDEBAR_MUTED_FUERTE}; font-size: 9px; font-weight: 700;
    letter-spacing: 1.1px;
}}
QLabel#CertNombre {{
    color: {SIDEBAR_FG}; font-size: {TEXTO_MD}px; font-weight: 600;
}}
QLabel#CertChevron {{ color: {SIDEBAR_MUTED_FUERTE}; font-size: {TEXTO_LG}px; }}

/* Menús: el texto al 75% de opacidad no llegaba a contrastar con el navy.
   Se sube a color pleno atenuado y el activo lleva además una línea inferior
   en el primario, que se distingue aunque el fondo apenas cambie. */
/* Botón «Certificar»: es el único control de navegación de la barra, así que
   tiene que leerse como un desplegable a primera vista y no como una etiqueta.
   Por eso lleva fondo y borde propios en reposo (no fantasma), un chevron en
   el texto, y estados de hover/pressed/abierto claramente distintos. */
QToolButton#BotonCertificar {{
    background: {SIDEBAR_ELEVADO}; color: {SIDEBAR_FG};
    border: 1px solid {SIDEBAR_BORDE}; border-radius: {RADIO_MD}px;
    padding: 8px 15px; font-size: {TEXTO_MD}px; font-weight: 600;
    text-align: left;
}}
QToolButton#BotonCertificar:hover {{
    background: {SIDEBAR_ELEVADO_HOVER}; border-color: {SIDEBAR_ACENTO};
}}
QToolButton#BotonCertificar:pressed {{ background: {SIDEBAR_BORDE}; }}
/* Menú abierto: Qt marca el botón como "checked" mientras el popup está
   desplegado. Se invierte el color para dejar clarísimo que está activo. */
QToolButton#BotonCertificar:checked {{
    background: {PRIMARY_HOVER}; color: {ON_PRIMARY};
    border-color: {PRIMARY_HOVER};
}}
QToolButton#BotonCertificar[activo="si"] {{
    border-color: {SIDEBAR_ACENTO};
    border-bottom: 2px solid {SIDEBAR_ACENTO};
}}
/* El chevron va en el texto, así que se oculta el indicador nativo, que en
   Windows dibuja una segunda flecha pegada al borde. */
QToolButton#BotonCertificar::menu-indicator {{ image: none; width: 0; }}

QToolButton#TopBarMenu {{
    background: transparent; border: none;
    border-bottom: 2px solid transparent; border-radius: 0;
    color: {SIDEBAR_MUTED_FUERTE}; padding: 8px 24px 6px 11px;
    font-size: {TEXTO_MD}px; font-weight: 500; text-align: left;
}}
QToolButton#TopBarMenu:hover {{
    background: {SIDEBAR_ELEVADO}; color: {SIDEBAR_FG};
}}
QToolButton#TopBarMenu[activo="si"] {{
    background: {SIDEBAR_ELEVADO_HOVER}; color: #ffffff;
    border-bottom-color: {SIDEBAR_ACENTO};
}}
QToolButton#TopBarMenu::menu-indicator {{
    subcontrol-position: right center; right: 8px; width: 10px;
}}

/* Deshabilitado pero legible: el gris por defecto de Qt sobre navy es
   invisible. */
QPushButton#BuscarGlobal {{
    background: {SIDEBAR_ELEVADO}; color: {SIDEBAR_FG};
    border: 1px solid {SIDEBAR_BORDE}; border-radius: {RADIO_MD}px;
    padding: 0 14px; font-size: {TEXTO_MD}px; text-align: left;
}}
QPushButton#BuscarGlobal:hover {{
    background: {SIDEBAR_ELEVADO_HOVER}; border-color: {SIDEBAR_MUTED};
}}
QPushButton#BuscarGlobal:disabled {{
    background: {SIDEBAR_ELEVADO}; color: {SIDEBAR_MUTED_FUERTE};
    border-color: {SIDEBAR_BORDE};
}}

/* Desplegables del toolbar. Sin esto Qt usa el menú nativo de Windows, que
   choca con el resto de la app. */
QMenu {{
    background: {SURFACE_CONTAINER_LOWEST}; color: {ON_SURFACE};
    border: 1px solid {OUTLINE_VARIANT}; border-radius: {RADIO_MD}px;
    padding: 5px;
}}
QMenu::item {{
    padding: 7px 22px 7px 14px; border-radius: {RADIO_SM}px;
    font-size: {TEXTO_MD}px;
}}
QMenu::item:selected {{ background: {SURFACE_CONTAINER}; color: {PRIMARY}; }}
QMenu::right-arrow {{ width: 10px; margin-right: 6px; }}
QMenu::item {{ min-width: 190px; }}
QMenu::separator {{
    height: 1px; background: {OUTLINE_VARIANT}; margin: 5px 8px;
}}
QMenu[objectName=""] QLabel {{ color: {ON_SURFACE_VARIANT}; }}

/* ── Paleta de comandos (Ctrl+K) ─────────────────────────────────────────── */
QFrame#PaletaMarco {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT}; border-radius: {RADIO_LG}px;
}}
QWidget#PaletaEntrada {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-bottom: 1px solid {OUTLINE_VARIANT};
    border-top-left-radius: {RADIO_LG}px; border-top-right-radius: {RADIO_LG}px;
}}
QLineEdit#PaletaInput {{
    background: transparent; border: none; padding: 11px 0;
    font-size: 16px; color: {ON_SURFACE};
}}
QLabel#PaletaLupa {{ color: {ON_SURFACE_VARIANT}; font-size: 17px; }}
QLabel#PaletaTecla {{
    color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_XS}px; font-weight: 600;
    border: 1px solid {OUTLINE_VARIANT}; border-radius: {RADIO_SM}px;
    padding: 2px 6px;
}}

QListWidget#PaletaLista {{
    background: {SURFACE_CONTAINER_LOWEST}; border: none; padding: 4px;
    outline: none;
}}
QListWidget#PaletaLista::item {{ border-radius: {RADIO_MD}px; }}
/* El resultado activo se marca con fondo tintado, no solo con el azul de
   selección del sistema, que en Windows tapa el texto. */
QListWidget#PaletaLista::item:selected {{ background: {PRIMARY_SOFT}; }}
QListWidget#PaletaLista::item:hover {{ background: {SURFACE_CONTAINER_LOW}; }}

QLabel#PaletaRuta {{
    color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_XS}px; font-weight: 600;
    letter-spacing: 0.4px;
}}
QLabel#PaletaHoja {{
    color: {ON_SURFACE}; font-size: {TEXTO_LG}px; font-weight: 600;
}}
QLabel#PaletaVacio {{
    color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_MD}px; padding: 26px 12px;
}}

QWidget#PaletaPie {{
    background: {SURFACE_CONTAINER_LOW};
    border-top: 1px solid {OUTLINE_VARIANT};
    border-bottom-left-radius: {RADIO_LG}px;
    border-bottom-right-radius: {RADIO_LG}px;
}}
QLabel#PaletaPieTexto {{
    color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_XS}px; font-weight: 600;
    letter-spacing: 0.5px;
}}

QLabel#PieDatos {{
    color: {ON_SURFACE_VARIANT}; font-size: {TEXTO_XS}px;
    padding: 5px 16px; background: {SURFACE_CONTAINER_LOWEST};
    border-top: 1px solid {OUTLINE_VARIANT};
}}

QLabel#Seccion {{
    color: {ON_SURFACE_VARIANT}; font-size: 12px; font-weight: 600;
    letter-spacing: 1px;
}}

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
QMenu::right-arrow {{ width: 10px; margin-right: 6px; }}
QMenu::item {{ min-width: 190px; }}
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
    min-width: 150px;
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
QDateEdit::down-arrow {{
    image: none;
    width: 0; height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 5px solid {ON_SURFACE_VARIANT};
}}
QDateEdit::down-arrow:hover {{ border-top-color: {PRIMARY}; }}
QLabel#IconoCalendario {{
    color: {ON_SURFACE_VARIANT}; font-size: 14px;
}}

QCalendarWidget {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QCalendarWidget QWidget {{
    alternate-background-color: {SURFACE_CONTAINER_LOWEST};
}}

QCalendarWidget QWidget#qt_calendar_navigationbar {{
    background: {PRIMARY};
    border-top-left-radius: {RADIO_LG}px;
    border-top-right-radius: {RADIO_LG}px;
    min-height: 42px;
}}
QCalendarWidget QToolButton {{
    color: {ON_PRIMARY};
    background: transparent;
    border: none;
    border-radius: {RADIO_SM}px;
    font-size: 13px;
    font-weight: 600;
    padding: 5px 12px;
    margin: 4px 2px;
}}
QCalendarWidget QToolButton:hover {{ background: rgba(255, 255, 255, 0.20); }}
QCalendarWidget QToolButton:pressed {{ background: rgba(0, 0, 0, 0.12); }}
QCalendarWidget QToolButton::menu-indicator {{ image: none; width: 0; }}
QCalendarWidget QToolButton#qt_calendar_prevmonth,
QCalendarWidget QToolButton#qt_calendar_nextmonth {{
    font-size: 16px;
    font-weight: 700;
    padding: 0;
    margin: 6px 4px;
    min-width: 30px;
    max-width: 30px;
    min-height: 30px;
    max-height: 30px;
}}

QCalendarWidget QSpinBox {{
    background: {SURFACE_CONTAINER_LOWEST};
    color: {ON_SURFACE};
    border: none;
    border-radius: {RADIO_SM}px;
    padding: 2px 6px;
    margin: 6px 2px;
    font-weight: 600;
    selection-background-color: {PRIMARY};
    selection-color: {ON_PRIMARY};
}}
QCalendarWidget QSpinBox::up-button, QCalendarWidget QSpinBox::down-button {{
    width: 14px;
    background: {SURFACE_CONTAINER_LOW};
    border: none;
}}
QCalendarWidget QSpinBox QLineEdit {{
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    min-height: 0;
    color: {ON_SURFACE};
}}

QCalendarWidget QMenu {{
    background: {SURFACE_CONTAINER_LOWEST};
    color: {ON_SURFACE};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
    padding: 4px 0;
}}
QCalendarWidget QMenu::item {{
    padding: 6px 22px;
    background: transparent;
    color: {ON_SURFACE};
}}
QCalendarWidget QMenu::item:selected {{
    background: {PRIMARY};
    color: {ON_PRIMARY};
}}

QCalendarWidget QAbstractItemView#qt_calendar_calendarview {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: none;
    border-bottom-left-radius: {RADIO_LG}px;
    border-bottom-right-radius: {RADIO_LG}px;
    padding: 6px;
}}
QCalendarWidget QAbstractItemView:enabled {{
    background: {SURFACE_CONTAINER_LOWEST};
    color: {ON_SURFACE};
    selection-background-color: {PRIMARY};
    selection-color: {ON_PRIMARY};
    outline: none;
    font-size: 13px;
}}
QCalendarWidget QAbstractItemView:disabled {{ color: {OUTLINE_VARIANT}; }}

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

QPushButton#Desplegable {{
    background: transparent;
    color: {ON_SURFACE_VARIANT};
    border: none;
    padding: 2px 0;
    font-size: 11px;
    font-weight: 600;
    text-align: left;
}}
QPushButton#Desplegable:hover {{ color: {PRIMARY}; }}
QPushButton#Desplegable[tono="error"] {{ color: {ERROR}; }}
/* Caja de columnas requeridas: chips en horizontal que saltan de línea
   solos (ChipsFlow), en vez de una lista vertical larga. */
QFrame#ListaColumnas {{
    background: {SURFACE_CONTAINER_LOW};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
}}
QFrame#ListaColumnas[tono="error"] {{
    background: {ERROR_SOFT};
    border-color: {ERROR};
}}
QLabel#ChipColumna {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 1px solid {OUTLINE_VARIANT};
    border-radius: {RADIO_SM}px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.3px;
    color: {ON_SURFACE_VARIANT};
}}
QLabel#ChipColumna[tono="error"] {{
    background: {SURFACE_CONTAINER_LOWEST};
    border-color: {ERROR};
    color: {ERROR};
}}

QWidget#Sidebar {{
    background: {SIDEBAR_BG};
    border-right: 1px solid {SIDEBAR_BG};
}}
QWidget#Sidebar QLabel {{ color: {SIDEBAR_FG}; }}
QWidget#Sidebar QScrollArea {{ background: transparent; }}
QPushButton#CertSwitcher {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: {RADIO_SM}px;
    color: {SIDEBAR_FG};
    padding: 10px 12px;
    text-align: left;
    font-size: 13px;
    font-weight: 700;
}}
QPushButton#CertSwitcher:hover {{ background: rgba(255, 255, 255, 0.12); }}
QPushButton#CertSwitcher::menu-indicator {{ image: none; width: 0; }}
QLabel#SidebarEyebrow {{
    color: {SIDEBAR_MUTED}; font-size: 9px; font-weight: 700; letter-spacing: 1.2px;
}}
QLabel#SidebarGrupo {{
    color: {SIDEBAR_MUTED}; font-size: 10px; font-weight: 700; letter-spacing: 1.2px;
    padding: 12px 12px 4px 12px;
}}
QLabel#SidebarPie {{ color: {SIDEBAR_MUTED}; font-size: 10px; }}
QPushButton#NavItem {{
    background: transparent;
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0;
    color: rgba(238, 240, 255, 0.78);
    padding: 8px 10px;
    text-align: left;
    font-size: 13px;
    font-weight: 500;
}}
QPushButton#NavItem:hover {{
    background: rgba(255, 255, 255, 0.07);
    color: {SIDEBAR_FG};
}}
QPushButton#NavItem:checked {{
    background: rgba(0, 149, 199, 0.28);
    border-left: 3px solid {PRIMARY_HOVER};
    color: {SIDEBAR_FG};
    font-weight: 700;
}}
QPushButton#NavItem:disabled {{ color: {SIDEBAR_MUTED}; }}
QFrame#SidebarSep {{ background: rgba(255, 255, 255, 0.10); max-height: 1px; }}

QFrame#ZonaSoltar {{
    background: {SURFACE_CONTAINER_LOWEST};
    border: 2px dashed {OUTLINE_VARIANT};
    border-radius: {RADIO_LG}px;
}}
QFrame#ZonaSoltar:hover {{ border-color: {PRIMARY}; }}
QFrame#ZonaSoltar[soltar="activa"] {{
    border-color: {PRIMARY};
    background: {SECONDARY_SOFT};
}}
QLabel#ZonaSoltarTitulo {{ font-size: 15px; font-weight: 600; }}
"""

def configurar_fecha(campo) -> None:
    from PySide6.QtCore import QDate, QLocale, Qt
    from PySide6.QtWidgets import QCalendarWidget, QToolButton

    campo.setCalendarPopup(True)
    campo.setDisplayFormat("dd/MM/yyyy")
    campo.setLocale(QLocale(QLocale.Spanish, QLocale.Peru))
    campo.setDate(QDate.currentDate())
    campo.setMinimumDate(QDate(2020, 1, 1))
    campo.setMaximumDate(QDate.currentDate().addYears(1))

    calendario = campo.calendarWidget()
    if calendario is None:
        return

    calendario.setGridVisible(False)
    calendario.setFirstDayOfWeek(Qt.Monday)
    calendario.setLocale(QLocale(QLocale.Spanish, QLocale.Peru))
    calendario.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
    calendario.setHorizontalHeaderFormat(QCalendarWidget.SingleLetterDayNames)
    calendario.setNavigationBarVisible(True)
    calendario.setMinimumSize(320, 280)
    calendario.setWindowFlags(calendario.windowFlags() | Qt.FramelessWindowHint)

    for nombre, texto in (("qt_calendar_prevmonth", "‹"), ("qt_calendar_nextmonth", "›")):
        boton = calendario.findChild(QToolButton, nombre)
        if boton is not None:
            boton.setIcon(QIcon())
            boton.setText(texto)
            boton.setToolButtonStyle(Qt.ToolButtonTextOnly)

    for nombre in ("qt_calendar_monthbutton", "qt_calendar_yearbutton"):
        boton = calendario.findChild(QToolButton, nombre)
        if boton is not None:
            boton.setToolButtonStyle(Qt.ToolButtonTextOnly)

    formato_cabecera = QTextCharFormat()
    formato_cabecera.setForeground(QColor(ON_SURFACE_VARIANT))
    formato_cabecera.setFontWeight(QFont.DemiBold)
    calendario.setHeaderTextFormat(formato_cabecera)

    formato_dia = QTextCharFormat()
    formato_dia.setForeground(QColor(ON_SURFACE))
    for dia in (Qt.Saturday, Qt.Sunday):
        calendario.setWeekdayTextFormat(dia, formato_dia)
