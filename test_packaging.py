#!/usr/bin/env python3
"""
test_packaging.py - Verifie la chaine d'empaquetage Windows.

Deux choses ne peuvent pas etre validees par la simple lecture du code :

  1. installer.iss n'est compile que par ISCC, sous Windows. Les erreurs qu'on
     y fait (section inconnue, GUID mal forme, fichier reference absent, bloc
     Pascal desequilibre) ne se voient qu'a la compilation, souvent des mois
     apres. Ce module les cherche statiquement.

  2. Le mode gele de PyInstaller change la resolution des chemins. Une icone
     trouvee depuis les sources peut disparaitre une fois empaquetee. On
     reproduit donc l'arborescence « un dossier » et les attributs
     `sys.frozen` / `sys._MEIPASS` pour verifier avant de construire.

    python3 test_packaging.py
"""

from __future__ import annotations

import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
results: list[bool] = []


def check(label: str, ok: bool) -> bool:
    print(f"[{'OK   ' if ok else 'ECHEC'}] {label}")
    results.append(bool(ok))
    return bool(ok)


# --------------------------------------------------------------- installer

def installer_tests() -> None:
    print("\n--- installer.iss ---")
    iss = ROOT / "installer.iss"
    if not check("installer.iss present", iss.is_file()):
        return
    text = iss.read_text(encoding="utf-8")

    sections = re.findall(r"^\[(\w+)\]", text, re.M)
    known = {"Setup", "Languages", "Tasks", "Files", "Icons", "Run",
             "UninstallDelete", "Code", "Dirs", "Registry", "INI", "Messages",
             "CustomMessages", "Types", "Components", "UninstallRun",
             "InstallDelete", "LangOptions"}
    check(f"sections toutes connues ({len(sections)})", not set(sections) - known)
    check("[Setup] declare une seule fois", sections.count("Setup") == 1)

    check("AppId au format GUID",
          bool(re.search(r"^AppId=\{\{[0-9A-Fa-f-]{36}\}", text, re.M)))

    n_if = len(re.findall(r"^\s*#if\b", text, re.M))
    n_end = len(re.findall(r"^\s*#endif\b", text, re.M))
    check("directives #if / #endif equilibrees", n_if == n_end)

    # --- metadonnees de version du setup.exe ------------------------------
    for directive in ("VersionInfoVersion", "VersionInfoProductVersion",
                      "VersionInfoCompany", "VersionInfoProductName",
                      "VersionInfoDescription", "VersionInfoCopyright",
                      "VersionInfoOriginalFileName"):
        check(f"metadonnee presente : {directive}",
              bool(re.search(rf"^{directive}=", text, re.M)))

    # VersionInfoVersion doit etre purement numerique : c'est exactement ce
    # qu'un « 1.0.0-rc1 » casserait, et seulement au moment de compiler.
    m = re.search(r"^VersionInfoVersion=(.+)$", text, re.M)
    if m:
        value = m.group(1).strip()
        if value.startswith("{#"):
            define = value.strip("{#}").strip()
            viss = (ROOT / "version.iss")
            resolved = ""
            if viss.is_file():
                mm = re.search(rf'#define\s+{define}\s+"([^"]+)"',
                               viss.read_text(encoding="utf-8"))
                resolved = mm.group(1) if mm else ""
            check(f"{define} defini dans version.iss", bool(resolved))
            check(f"VersionInfoVersion numerique a 4 nombres ({resolved})",
                  bool(re.fullmatch(r"\d+(\.\d+){3}", resolved)))

    check("version.iss inclus", '#include "version.iss"' in text)
    check("nom de sortie derive de la version",
          "OutputBaseFilename=" in text and "{#AppVersion}" in text)

    # --- mise a jour proprement -------------------------------------------
    check("_internal efface avant reinstallation",
          "[InstallDelete]" in text and r'Name: "{app}\_internal"' in text)
    check("_internal efface a la desinstallation",
          r'Name: "{app}\_internal"' in text.split("[UninstallDelete]")[-1])

    # --- coffre a cles -----------------------------------------------------
    check("le coffre n'est jamais supprime sans confirmation",
          "MB_DEFBUTTON2" in text and "RegDeleteKeyIncludingSubkeys" in text)
    check("aucune entree [Registry] n'ecrase le coffre",
          "[Registry]" not in sections)

    # --- bloc Pascal -------------------------------------------------------
    if "[Code]" in text:
        code = text[text.index("[Code]"):]
        begins = len(re.findall(r"\bbegin\b", code))
        ends = len(re.findall(r"\bend[;.]", code))
        check(f"bloc [Code] equilibre (begin={begins}, end={ends})",
              begins == ends)
        # Piege classique : en Pascal les commentaires { } ne s'imbriquent
        # pas, donc une accolade citee dans un commentaire le referme.
        check("pas de commentaire Pascal entre accolades",
              not re.search(r"^\s*\{[^$]", code, re.M))

    # --- fichiers references ----------------------------------------------
    for src in re.findall(r'^Source:\s*"([^"*]+)";', text, re.M):
        if src.startswith("{#"):
            continue
        check(f"fichier reference present : {src}",
              (ROOT / src.replace("\\", os.sep)).exists())
    for directive in ("SetupIconFile", "LicenseFile", "InfoBeforeFile"):
        m = re.search(rf"^{directive}=(.+)$", text, re.M)
        if m:
            path = m.group(1).strip().replace("\\", os.sep)
            check(f"{directive} pointe sur un fichier existant",
                  (ROOT / path).exists())


# -------------------------------------------------------------------- spec

def spec_tests() -> None:
    print("\n--- CryptoTool.spec ---")
    spec_file = ROOT / "CryptoTool.spec"
    if not check("CryptoTool.spec present", spec_file.is_file()):
        return
    spec = spec_file.read_text(encoding="utf-8")

    import ast
    try:
        ast.parse(spec)
        check("le .spec s'analyse comme du Python", True)
    except SyntaxError as exc:
        check(f"le .spec s'analyse comme du Python ({exc})", False)

    check("build en un dossier (COLLECT present)", "COLLECT(" in spec)
    check("UPX desactive (compresser les DLL Qt fait planter)",
          "upx=False" in spec and "upx=True" not in spec)
    check("application graphique, sans console", "console=False" in spec)
    check("icone cablee", "cryptotool.ico" in spec)
    check("ressource de version cablee", "version_info.txt" in spec)
    check("backend natif de cryptography declare",
          "cryptography.hazmat.bindings" in spec)
    check("assets embarques", "'assets'" in spec)


# ----------------------------------------------------------------- version

def version_tests() -> None:
    print("\n--- version a source unique ---")
    src = (ROOT / "crypto_tool.py").read_text(encoding="utf-8")
    m = re.search(r'^__version__\s*=\s*["\']([^"\']+)["\']', src, re.M)
    if not check("__version__ present dans crypto_tool.py", bool(m)):
        return
    version = m.group(1)

    info = ROOT / "version_info.txt"
    iss = ROOT / "version.iss"
    if not check("version_info.txt genere", info.is_file()):
        return
    if not check("version.iss genere", iss.is_file()):
        return

    info_text = info.read_text(encoding="utf-8")
    iss_text = iss.read_text(encoding="utf-8")

    import ast
    try:
        ast.parse(info_text)
        check("version_info.txt s'analyse comme du Python", True)
    except SyntaxError:
        check("version_info.txt s'analyse comme du Python", False)

    check(f"la ressource de l'exe annonce {version}",
          f"'FileVersion', '{version}'" in info_text)
    check(f"l'installateur annonce {version}",
          f'#define AppVersion "{version}"' in iss_text)

    # La table de chaines et la table de traduction doivent s'accorder, sinon
    # l'Explorateur n'affiche aucune des chaines : 040C = 1036 = francais.
    lang = re.search(r"StringTable\(\s*'([0-9A-F]{4})([0-9A-F]{4})'", info_text)
    var = re.search(r"VarStruct\('Translation',\s*\[(\d+),\s*(\d+)\]", info_text)
    if lang and var:
        check("StringTable et Translation concordent",
              int(lang.group(1), 16) == int(var.group(1)) and
              int(lang.group(2), 16) == int(var.group(2)))


# ------------------------------------------------------------- icone

def icon_tests() -> None:
    print("\n--- icone ---")
    ico = ROOT / "assets" / "cryptotool.ico"
    if not check("assets/cryptotool.ico genere", ico.is_file()):
        return
    try:
        from PIL import Image
    except ImportError:
        print("       (Pillow absent, controle des tailles ignore)")
        return
    with Image.open(ico) as im:
        sizes = sorted(im.info.get("sizes", []))
    present = [s[0] for s in sizes]
    # Les tailles que Windows demande reellement selon le contexte : barre des
    # taches, Alt-Tab, listes de l'Explorateur, grandes icones, mosaiques.
    for want in (16, 20, 24, 32, 48, 64, 128, 256):
        check(f"taille {want}x{want} presente dans le .ico", want in present)

    sys.path.insert(0, str(ROOT))
    import make_icon  # noqa: E402
    g = make_icon.layout(1000, 4, True)
    lock = g["lock"]

    # Le cadenas doit s'accrocher a la meme grille que les lignes, sinon il
    # flotte : c'est exactement le defaut qu'avait la premiere version.
    check("le haut du cadenas est sur la 3e ligne",
          abs(lock["y0"] - g["bar_y"][2]) < 0.5)
    check("le bas du cadenas est sur la 4e ligne",
          abs(lock["y1"] - (g["bar_y"][3] + g["bar_h"])) < 0.5)
    check("la droite du cadenas est sur la marge droite",
          abs(lock["x1"] - g["right"]) < 0.5)
    check("les lignes chiffrees s'arretent avant le cadenas",
          g["text_right"] < lock["x0"])

    # Un fragment plus court que MIN_FRAGMENT fois sa hauteur se dessine en
    # pastille et ne lit plus comme du texte.
    span = g["text_right"] - g["left"]
    worst = min((b - a) * span / g["bar_h"]
                for row in make_icon.CIPHER_ROWS for a, b in row)
    check(f"fragments assez longs pour lire comme du texte "
          f"(le plus court : {worst:.1f}x, minimum {make_icon.MIN_FRAGMENT})",
          worst >= make_icon.MIN_FRAGMENT)

    # --- raccord de l'anse du cadenas ---------------------------------
    # Pillow applique l'epaisseur vers l'interieur pour arc() et de part et
    # d'autre pour line(). Donner le meme rayon aux deux produit une anse
    # dont le sommet est plus etroit que ses montants. Le defaut ne se voit
    # pas dans le source, seulement dans les pixels : on mesure.
    from PIL import Image, ImageDraw

    PX = 2000
    probe = Image.new("RGB", (PX, PX), (0, 0, 0))
    d = ImageDraw.Draw(probe)
    box = {"x0": PX * 0.18, "x1": PX * 0.82, "y0": PX * 0.10,
           "y1": PX * 0.90, "h": PX * 0.80, "w": PX * 0.64}
    geo = make_icon.draw_lock(d, box, PX, 0)   # size=0 : sans trou de serrure
    cx, cy = geo["cx"], geo["cy"]
    r, w = geo["radius"], geo["stroke"]

    def first_run(pixels):
        start = None
        for i, p in enumerate(pixels):
            on = p[0] > 100
            if on and start is None:
                start = i
            elif not on and start is not None:
                return start, i - 1
        return (start, len(pixels) - 1) if start is not None else (0, -1)

    # Epaisseur sur le montant gauche
    y = int((cy + geo["body_y0"]) / 2)
    a, b = first_run([probe.getpixel((x, y)) for x in range(PX)])
    leg_axis, leg_w = cx - (a + b) / 2, b - a + 1

    # Epaisseur au sommet de l'anse
    top = int(cy - r - w)
    a, b = first_run([probe.getpixel((int(cx), yy))
                      for yy in range(top, int(cy))])
    crown_axis, crown_w = cy - (top + (a + b) / 2), b - a + 1

    check(f"epaisseur identique au sommet et aux montants "
          f"({crown_w} contre {leg_w})", abs(crown_w - leg_w) <= 2)
    check(f"axe de l'anse au meme rayon partout "
          f"({crown_axis:.0f} contre {leg_axis:.0f})",
          abs(crown_axis - leg_axis) <= 2)
    check(f"axe conforme au rayon calcule ({r:.0f})",
          abs(leg_axis - r) <= 2 and abs(crown_axis - r) <= 2)



# ------------------------------------------------- installation gelee

def frozen_tests() -> None:
    print("\n--- installation gelee simulee ---")
    root = Path(tempfile.mkdtemp(prefix="cryptotool-install-"))
    internal = root / "_internal"
    internal.mkdir()
    shutil.copy(ROOT / "crypto_tool.py", internal / "crypto_tool.py")
    shutil.copytree(ROOT / "assets", internal / "assets")
    (root / "CryptoTool.exe").write_text("")

    # On reproduit exactement ce que PyInstaller pose en mode « un dossier » :
    #     CryptoTool\
    #     +-- CryptoTool.exe     <- sys.executable
    #     +-- _internal\         <- sys._MEIPASS, et les assets sont dedans
    saved = (getattr(sys, "frozen", None), getattr(sys, "_MEIPASS", None),
             sys.executable, list(sys.path))
    try:
        sys.frozen = True                     # type: ignore[attr-defined]
        sys._MEIPASS = str(internal)          # type: ignore[attr-defined]
        sys.executable = str(root / "CryptoTool.exe")
        sys.path.insert(0, str(internal))
        for name in list(sys.modules):
            if name == "crypto_tool":
                del sys.modules[name]

        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        import crypto_tool  # noqa: E402

        check("resource_root suit _internal et non le dossier de l'exe",
              crypto_tool.resource_root() == str(internal))
        icon = crypto_tool.icon_path()
        check("icone resolue en mode gele", bool(icon))
        check("icone resolue depuis _internal",
              bool(icon) and icon.startswith(str(internal)))
    finally:
        frozen, meipass, executable, path = saved
        if frozen is None:
            delattr(sys, "frozen")
        if meipass is None and hasattr(sys, "_MEIPASS"):
            delattr(sys, "_MEIPASS")
        sys.executable = executable
        sys.path[:] = path
        shutil.rmtree(root, ignore_errors=True)

    # Et le contraire : depuis les sources, la racine doit etre le dossier du
    # script. Une confusion entre les deux ne se verrait qu'apres le gel.
    for name in list(sys.modules):
        if name == "crypto_tool":
            del sys.modules[name]
    sys.path.insert(0, str(ROOT))
    import crypto_tool as fresh  # noqa: E402
    check("resource_root suit le script depuis les sources",
          fresh.resource_root() == str(ROOT))


# ------------------------------------------------------- scripts de build



def script_tests() -> None:
    print("\n--- scripts de construction ---")
    ps1 = ROOT / "build_windows.ps1"
    cmd = ROOT / "build_windows.cmd"
    if check("build_windows.ps1 present", ps1.is_file()):
        text = ps1.read_text(encoding="utf-8")
        check("accolades equilibrees",
              text.count("{") == text.count("}"))
        check("parentheses equilibrees",
              text.count("(") == text.count(")"))
        for step in ("make_icon.py", "make_version.py", "PyInstaller",
                     "installer.iss"):
            check(f"etape enchainee : {step}", step in text)
        check("essai de demarrage de l'executable", "--version" in text)
        check("environnement virtuel local", ".venv-build" in text)
        check("recherche d'Inno Setup sans chemin suppose",
              "Uninstall" in text and "ISCC.exe" in text)
        check("modes de construction declares", "ValidateSet" in text)

    if check("build_windows.cmd present", cmd.is_file()):
        raw = cmd.read_bytes()
        # cmd.exe interprete mal un fichier en LF seul.
        check("fins de ligne CRLF",
              b"\r\n" in raw and raw.count(b"\n") == raw.count(b"\r\n"))
        check("contourne la strategie d'execution",
              b"ExecutionPolicy Bypass" in raw)
        check("retire la marque du web", b"Unblock-File" in raw)


def licence_tests() -> None:
    print("\n--- licence ---")
    lic = ROOT / "LICENSE.txt"
    if not check("LICENSE.txt present", lic.is_file()):
        return
    text = lic.read_text(encoding="utf-8")

    # Le texte integral, pas seulement un renvoi vers gnu.org : l'article 4
    # demande que la licence accompagne le programme.
    check("texte integral de la GPL-3.0 present",
          "GNU GENERAL PUBLIC LICENSE" in text and
          "Version 3, 29 June 2007" in text)
    for marker in ("TERMS AND CONDITIONS", "0. Definitions",
                   "15. Disclaimer of Warranty", "16. Limitation of Liability",
                   "END OF TERMS AND CONDITIONS"):
        check(f"section presente : {marker}", marker in text)

    check("composants tiers listes",
          all(name in text for name in ("PyQt6", "cryptography", "Pillow")))
    check("la raison du choix de licence est expliquee",
          "PyQt6" in text and "GPL-3.0" in text)

    # L'avis doit etre le meme partout. C'est exactement le genre de chose qui
    # se desynchronise en silence a la premiere retouche.
    src = (ROOT / "crypto_tool.py").read_text(encoding="utf-8")
    check("avis de licence en tete du source",
          "Licence Publique Générale GNU" in src or
          "Licence Publique Generale GNU" in src)
    check("avis affiche par --version", "gnu.org/licenses" in src)

    iss = (ROOT / "installer.iss").read_text(encoding="utf-8")
    check("copyright GPL dans les metadonnees de l'installateur",
          "GPL-3.0" in iss)

    mv = (ROOT / "make_version.py").read_text(encoding="utf-8")
    check("copyright GPL dans la ressource de l'exe", "GPL-3.0" in mv)

    check("aucun reste de licence MIT pour le projet",
          "licence MIT" not in (ROOT / "README.md").read_text(encoding="utf-8"))


def main() -> int:
    installer_tests()
    spec_tests()
    version_tests()
    licence_tests()
    icon_tests()
    script_tests()
    frozen_tests()

    ok = sum(1 for r in results if r)
    print(f"\n{ok}/{len(results)} controles au vert")
    if all(results):
        print("EMPAQUETAGE VALIDE")
        return 0
    print("DES CONTROLES ONT ECHOUE")
    return 1


if __name__ == "__main__":
    sys.exit(main())
