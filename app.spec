# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# logic/share, logic/base_datos y logic/generals NO tienen __init__.py, así que
# el análisis estático de PyInstaller no los descubre solo. Se recogen a mano.
ocultos = []
ocultos += collect_submodules('logic')
ocultos += collect_submodules('models')
ocultos += ['pandas', 'openpyxl', 'xlsxwriter', 'xlrd']

datos = [
    # Icono de la ventana (config.ruta_icono lo resuelve vía sys._MEIPASS).
    ('app/ui/assets', 'app/ui/assets'),
    # Fuentes Inter, si existen (config.carpeta_fuentes las busca aquí)
    # ('app/ui/fonts', 'app/ui/fonts'),
]

a = Analysis(
    ['app/main.py'],
    pathex=['.'],
    binaries=[],
    datas=datos,
    hiddenimports=ocultos,
    hookspath=[],
    runtime_hooks=[],
    # Recorta peso: son dependencias que arrastra pandas pero la app no usa.
    excludes=['tkinter', 'matplotlib', 'PyQt5', 'PyQt6', 'IPython', 'notebook'],
    noarchive=False,
)

pyz = PYZ(a.pure)

# ONEFILE: a.binaries y a.datas van DENTRO de EXE(), no en un COLLECT aparte.
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='CertificacionAccesos',
    debug=False,
    strip=False,
    upx=False,                      # UPX rompe DLLs de Qt: dejar en False
    runtime_tmpdir=None,            # extrae en %TEMP%
    console=False,                  # True para ver traceback en consola
    icon='app/ui/assets/logo.ico',
)
