# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_submodules

# logic/share, logic/base_datos y logic/generals NO tienen __init__.py, así que
# el análisis estático de PyInstaller no los descubre solo. Se recogen a mano.
ocultos = []
ocultos += collect_submodules('logic')
ocultos += collect_submodules('models')
ocultos += ['pandas', 'openpyxl', 'xlsxwriter', 'xlrd']
ocultos += ['app.update', 'app.update.checker', 'app.update.downloader', 'app.update.installer']

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

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Certificacion',
    debug=False,
    strip=False,
    upx=False,
    console=False,
    icon='app/ui/assets/logo.ico',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name='Certificacion',
)
