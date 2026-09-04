#!/usr/bin/env python3
"""
make_version.py - Derive les fichiers de version depuis crypto_tool.py.

Une seule source de verite pour le numero de version : `__version__` dans
crypto_tool.py. La barre de titre, l'onglet des proprietes du fichier .exe
dans l'Explorateur et le nom de l'installateur ne peuvent donc pas se
contredire.

Produit :
    version_info.txt   ressource de version de l'executable, lue par
                       PyInstaller via la directive `version=` du .spec
    version.iss        `#define AppVersion` et `#define AppVersionFull`,
                       inclus par installer.iss

Les deux fichiers sont generes, jamais edites a la main, et exclus du
controle de version.

On n'utilise pas GetVersionNumbersString() du cote d'Inno Setup pour lire la
version dans l'executable : cette fonction renvoie quatre nombres, et
l'installateur se serait appele CryptoTool-1.0.0.0-setup.exe.

Lancer avant PyInstaller ; build_windows.ps1 le fait automatiquement.
"""

from __future__ import annotations

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))

NAME = "CryptoTool"
PRODUCT = "Crypto Tool"
PUBLISHER = "F4JTV"
DESCRIPTION = "Chiffrement symetrique et coffre a cles"
COPYRIGHT = "Copyright (C) 2026 F4JTV. GPL-3.0 ou ulterieure."

# 040C04B0 : francais (1036), jeu de caracteres Unicode (1200). Le couple
# doit correspondre a VarStruct('Translation', ...) plus bas, sinon
# l'Explorateur n'affiche aucune des chaines.
VERSION_INFO = '''\
# UTF-8
# Ressource de version Windows, generee par make_version.py - ne pas editer.
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=({a}, {b}, {c}, 0),
    prodvers=({a}, {b}, {c}, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        '040C04B0',
        [StringStruct('CompanyName', '{publisher}'),
         StringStruct('FileDescription', '{description}'),
         StringStruct('FileVersion', '{version}'),
         StringStruct('InternalName', '{name}'),
         StringStruct('LegalCopyright', '{copyright}'),
         StringStruct('OriginalFilename', '{name}.exe'),
         StringStruct('ProductName', '{product}'),
         StringStruct('ProductVersion', '{version}')])
    ]),
    VarFileInfo([VarStruct('Translation', [1036, 1200])])
  ]
)
'''


def read_version() -> str:
    path = os.path.join(HERE, "crypto_tool.py")
    if not os.path.isfile(path):
        sys.exit(f"crypto_tool.py est introuvable dans {HERE}")
    with open(path, encoding="utf-8") as handle:
        match = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']',
                          handle.read(), re.M)
    if not match:
        sys.exit(f"__version__ est introuvable dans {path}")
    return match.group(1)


def main() -> int:
    version = read_version()

    # Windows veut quatre entiers ; une version comme « 1.2 » ou « 1.2.0-rc1 »
    # est completee et nettoyee plutot que rejetee.
    parts = [int(p) for p in re.findall(r"\d+", version)][:3]
    while len(parts) < 3:
        parts.append(0)
    a, b, c = parts

    info = os.path.join(HERE, "version_info.txt")
    with open(info, "w", encoding="utf-8", newline="") as handle:
        handle.write(VERSION_INFO.format(
            a=a, b=b, c=c, version=version, name=NAME, product=PRODUCT,
            publisher=PUBLISHER, description=DESCRIPTION, copyright=COPYRIGHT))

    iss = os.path.join(HERE, "version.iss")
    with open(iss, "w", encoding="utf-8", newline="") as handle:
        handle.write("; Genere par make_version.py - ne pas editer.\n")
        # AppVersion sert a l'affichage et au nom du fichier ; il garde la
        # forme lisible. AppVersionFull alimente VersionInfoVersion, que le
        # compilateur exige sous forme purement numerique a quatre nombres :
        # un « 1.0.0-rc1 » y provoquerait une erreur de compilation.
        handle.write(f'#define AppVersion "{version}"\n')
        handle.write(f'#define AppVersionFull "{a}.{b}.{c}.0"\n')

    print(f"version : {version}  ->  {a}.{b}.{c}.0")
    print(f"ecrit   : {info}")
    print(f"ecrit   : {iss}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
