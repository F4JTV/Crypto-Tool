# -*- mode: python ; coding: utf-8 -*-
"""
Recette PyInstaller pour Crypto Tool.

    python make_icon.py
    python make_version.py
    pyinstaller --noconfirm --clean CryptoTool.spec

Le build est en « un dossier » et non en fichier unique, deliberement : un
onefile se decompresse dans un dossier temporaire a chaque lancement, ce qui
coute plusieurs secondes avec Qt et declenche regulierement les heuristiques
des antivirus, un binaire qui s'auto-extrait ressemblant beaucoup a un
paquet malveillant. Pour un outil de chiffrement, deja plus expose que la
moyenne aux faux positifs, cela n'aurait pas ete un bon choix.

UPX est desactive volontairement : compresser les DLL Qt est une cause
classique de plantages difficiles a diagnostiquer, et aggrave encore la
detection heuristique.
"""

import os

block_cipher = None

datas = []
if os.path.isdir('assets'):
    datas.append(('assets', 'assets'))
for extra in ('README.md', 'LICENSE.txt'):
    if os.path.isfile(extra):
        datas.append((extra, '.'))

a = Analysis(
    ['crypto_tool.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    # cryptography charge son moteur natif par un chemin que l'analyse
    # statique ne suit pas toujours ; le declarer coute une ligne et evite un
    # « backend introuvable » qui n'apparaitrait qu'apres le gel.
    hiddenimports=['cryptography.hazmat.bindings._rust'],
    hookspath=[],
    runtime_hooks=[],
    # Les modules Qt que l'application ne charge jamais. L'exclusion fait
    # passer le build d'environ 180 Mo a une petite centaine.
    excludes=[
        'tkinter', 'numpy', 'matplotlib', 'PIL', 'pytest', 'setuptools',
        'PyQt6.QtWebEngineCore', 'PyQt6.QtWebEngineWidgets',
        'PyQt6.QtWebChannel', 'PyQt6.QtWebSockets',
        'PyQt6.QtQml', 'PyQt6.QtQuick', 'PyQt6.QtQuick3D',
        'PyQt6.QtQuickWidgets',
        'PyQt6.QtMultimedia', 'PyQt6.QtMultimediaWidgets',
        'PyQt6.QtSpatialAudio',
        'PyQt6.Qt3DCore', 'PyQt6.Qt3DRender', 'PyQt6.Qt3DExtras',
        'PyQt6.Qt3DInput', 'PyQt6.Qt3DAnimation', 'PyQt6.Qt3DLogic',
        'PyQt6.QtCharts', 'PyQt6.QtDataVisualization',
        'PyQt6.QtBluetooth', 'PyQt6.QtNfc', 'PyQt6.QtPositioning',
        'PyQt6.QtSerialPort', 'PyQt6.QtSensors',
        'PyQt6.QtSql', 'PyQt6.QtTest', 'PyQt6.QtDesigner', 'PyQt6.QtHelp',
        'PyQt6.QtPdf', 'PyQt6.QtPdfWidgets',
        'PyQt6.QtOpenGL', 'PyQt6.QtOpenGLWidgets',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CryptoTool',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Application graphique : pas de console noire derriere la fenetre.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=('assets/cryptotool.ico'
          if os.path.isfile('assets/cryptotool.ico') else None),
    version=('version_info.txt'
             if os.path.isfile('version_info.txt') else None),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CryptoTool',
)
