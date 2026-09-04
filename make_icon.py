#!/usr/bin/env python3
"""
make_icon.py - Dessine assets/cryptotool.ico et assets/cryptotool.png.

Motif : quatre lignes de texte. Les deux du haut sont pleines et claires,
c'est le texte en clair. Les deux du bas sont brisees en fragments de
largeurs irregulieres et teintees de vert, c'est le texte chiffre. Un cadenas
ambre occupe l'angle inferieur droit.

TOUT EST POSE SUR UNE SEULE GRILLE
----------------------------------
Une premiere version placait le cadenas par-dessus les lignes, avec un
detourage pour les separer. Rien n'etait aligne : le cadenas flottait, il
mordait dans la derniere ligne, et le bloc de texte etait decale vers le
haut pour lui faire de la place.

Ici, une seule fonction calcule la grille, et chaque forme s'y accroche :

    L                                              R
    +--------------------------------------------+  T
    |  ################################           |  ligne 1, en clair
    |  ##########################                 |  ligne 2, en clair
    |  ####  ######  ####      |  cadenas         |  ligne 3, chiffree
    |  ##  ##########  ##      |                  |  ligne 4, chiffree
    +--------------------------------------------+  B

Le cadenas occupe exactement la hauteur des lignes 3 et 4 : son bas est sur
la ligne de base de la ligne 4, sa droite sur la marge droite. Les lignes
chiffrees s'arretent avant lui. Aucun chevauchement, donc aucun detourage a
bricoler, et aucune des deux formes ne peut deriver par rapport a l'autre.

Chaque taille du .ico est rendue a sa propre resolution puis
suréchantillonnée, au lieu d'etre reduite depuis un seul bitmap : reduire une
image de 256 px vers 16 px donne de la bouillie.

Le detail disparait quand la place manque :
    - le cadenas sous 24 px, il ne serait plus qu'une tache. Les lignes
      chiffrees reprennent alors toute la largeur.
    - la quatrieme ligne sous 24 px, l'interligne tomberait sous un pixel.
    - le trou de serrure sous 48 px.

Lancer avant PyInstaller ; build_windows.ps1 le fait automatiquement.
"""

from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageDraw
except ImportError:
    sys.exit("Pillow est requis :  pip install pillow")

CHASSIS = (22, 30, 43, 255)        # bleu ardoise du fond
PLAIN = (233, 236, 239, 255)       # texte en clair, blanc casse
CIPHER = (61, 214, 140, 255)       # texte chiffre, vert terminal
LOCK = (243, 179, 63, 255)         # cadenas, ambre

SIZES = [16, 20, 24, 32, 48, 64, 128, 256]
SS = 8                              # facteur de suréchantillonnage

MARGIN = 0.145                      # marge interieure, en fraction du cote
# Part de la hauteur d'une rangee occupee par la barre ; le reste est
# l'interligne. Une barre epaisse rend les fragments chiffres plus courts que
# hauts, et ils se dessinent alors en pastilles au lieu de mots.
ROW_RATIO = 0.46

# Longueur minimale d'un fragment, en multiples de la hauteur de barre. En
# dessous, la forme lit comme un point et non comme un morceau de texte.
MIN_FRAGMENT = 1.7

# Anse du cadenas. Le rayon est exprime en fraction de la hauteur laissee
# libre au-dessus du corps ; l'epaisseur, en fraction de ce rayon. Ces deux
# valeurs decident de la silhouette : un rayon trop grand ne laisse plus de
# montants et l'anse devient un demi-cercle pose sur le corps.
SHACKLE_RADIUS = 0.44
SHACKLE_STROKE = 0.62

# Longueur des lignes en clair, en fraction de la largeur disponible. Une
# ligne pleine largeur ne ressemble pas a du texte : un paragraphe a un bord
# droit irregulier.
PLAIN_ROWS = [1.00, 0.82]

# Fragments des lignes chiffrees, en fraction de la largeur disponible.
# Les longueurs sont irregulieres a dessein : un decoupage regulier
# ressemblerait a un code a barres, pas a du texte.
# Deux fragments par ligne et non trois : la place restant a gauche du
# cadenas ne permet pas trois morceaux qui lisent encore comme du texte.
CIPHER_ROWS = [
    [(0.00, 0.44), (0.54, 1.00)],
    [(0.00, 0.34), (0.44, 1.00)],
]


def layout(px: int, rows: int, with_lock: bool) -> dict:
    """Calcule la grille commune aux lignes et au cadenas.

    Une seule source pour toutes les coordonnees : c'est ce qui garantit que
    le cadenas et les lignes ne peuvent pas se decaler l'un par rapport a
    l'autre quand on retouche une valeur.
    """
    left = px * MARGIN
    right = px * (1.0 - MARGIN)
    top = px * MARGIN
    bottom = px * (1.0 - MARGIN)

    row_h = (bottom - top) / rows           # hauteur d'une rangee, interligne inclus
    bar_h = row_h * ROW_RATIO
    grid = {
        "left": left, "right": right, "top": top, "bottom": bottom,
        "row_h": row_h, "bar_h": bar_h,
        "bar_y": [top + i * row_h + (row_h - bar_h) / 2.0 for i in range(rows)],
        "text_right": right,
    }

    if with_lock:
        # Le cadenas couvre exactement les deux dernieres rangees : du haut
        # de la barre 3 au bas de la barre 4.
        lock_top = grid["bar_y"][2]
        lock_bottom = grid["bar_y"][3] + bar_h
        lock_h = lock_bottom - lock_top
        body_w = lock_h * 0.78
        grid["lock"] = {
            "x1": right, "x0": right - body_w,
            "y1": lock_bottom, "y0": lock_top,
            "h": lock_h, "w": body_w,
        }
        # Les lignes chiffrees s'arretent avant le cadenas, avec une
        # gouttiere pour que les deux ne se touchent pas.
        grid["text_right"] = grid["lock"]["x0"] - bar_h * 0.9

    return grid


def draw_lock(d: ImageDraw.ImageDraw, box: dict, px: int, size: int) -> dict:
    """Trace le cadenas dans la case que la grille lui a reservee.

    Renvoie la geometrie de l'anse, pour que les controles puissent la
    verifier sans avoir a la recalculer de leur cote.

    RACCORD DE L'ANSE
    -----------------
    Pillow n'applique pas l'epaisseur de la meme facon a arc() et a line() :

        arc(boite de rayon R, width=W)   -> axe du trait au rayon R - W/2
        line(a la distance R, width=W)   -> axe du trait au rayon R

    Passer le meme R aux deux donne donc une anse dont le sommet est plus
    etroit que ses montants de W au total, et le raccord se voit comme un
    ressaut. C'est le defaut qu'avait la version precedente.

    On compense en donnant a l'arc une boite de rayon R + W/2, de sorte que
    son axe retombe exactement sur R, celui des montants.
    """
    # Repartition verticale : l'anse occupe le haut, le corps le bas. Un
    # cadenas dont le corps fait environ 60 % de la hauteur est celui qu'on
    # reconnait le plus vite.
    body_h = box["h"] * 0.60
    body_y0 = box["y1"] - body_h
    shackle_zone = body_y0 - box["y0"]

    radius = shackle_zone * SHACKLE_RADIUS          # axe de l'anse
    stroke = max(SS, int(round(radius * SHACKLE_STROKE)))
    # Le sommet exterieur de l'anse se pose sur le haut de la case.
    arc_cy = box["y0"] + radius + stroke / 2.0
    cx = (box["x0"] + box["x1"]) / 2.0

    # Boite elargie de stroke/2 : voyez l'explication ci-dessus.
    outer = radius + stroke / 2.0
    d.arc([cx - outer, arc_cy - outer, cx + outer, arc_cy + outer],
          start=180, end=360, fill=LOCK, width=stroke)

    # Les montants descendent de la fin de l'arc jusque dans le corps, avec
    # un leger recouvrement : s'arreter pile sur body_y0 laisse une encoche
    # d'un pixel a l'anticrenelage.
    for side in (-1, 1):
        x = cx + side * radius
        d.line([(x, arc_cy), (x, body_y0 + stroke * 0.5)],
               fill=LOCK, width=stroke)

    d.rounded_rectangle([box["x0"], body_y0, box["x1"], box["y1"]],
                        radius=body_h * 0.22, fill=LOCK)

    # Trou de serrure : trace seulement quand il ferait plus d'un pixel.
    if size >= 48:
        kr = box["w"] * 0.13
        ky = body_y0 + body_h * 0.38
        d.ellipse([cx - kr, ky - kr, cx + kr, ky + kr], fill=CHASSIS)
        d.polygon([(cx - kr * 0.62, ky), (cx + kr * 0.62, ky),
                   (cx + kr * 0.34, box["y1"] - body_h * 0.18),
                   (cx - kr * 0.34, box["y1"] - body_h * 0.18)], fill=CHASSIS)

    return {"cx": cx, "cy": arc_cy, "radius": radius, "stroke": stroke,
            "body_y0": body_y0, "outer": outer}


def draw_icon(size: int) -> Image.Image:
    px = size * SS
    img = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, px - 1, px - 1], radius=int(px * 0.21),
                        fill=CHASSIS)

    with_lock = size >= 24
    rows = 4 if size >= 24 else 3
    g = layout(px, rows, with_lock)

    bar_h = g["bar_h"]
    radius = bar_h / 2.0

    too_short: list[float] = []

    def bar(y: float, x0: float, x1: float, colour) -> None:
        if x1 - x0 < bar_h * MIN_FRAGMENT:
            too_short.append((x1 - x0) / bar_h)
        d.rounded_rectangle([x0, y, x1, y + bar_h], radius=radius, fill=colour)

    # --- lignes en clair, sur toute la largeur ---------------------------
    plain_count = 2
    plain_span = g["right"] - g["left"]
    for i in range(plain_count):
        bar(g["bar_y"][i], g["left"],
            g["left"] + plain_span * PLAIN_ROWS[i], PLAIN)

    # --- lignes chiffrees, arretees avant le cadenas ---------------------
    cipher_span = g["text_right"] - g["left"]
    for i, fragments in enumerate(CIPHER_ROWS[:rows - plain_count]):
        y = g["bar_y"][plain_count + i]
        for a, b in fragments:
            bar(y, g["left"] + cipher_span * a, g["left"] + cipher_span * b,
                CIPHER)

    if with_lock:
        draw_lock(d, g["lock"], px, size)

    if too_short:
        worst = min(too_short)
        print(f"  attention : a {size} px, un fragment ne fait que "
              f"{worst:.1f} fois la hauteur de barre (minimum {MIN_FRAGMENT})",
              file=sys.stderr)

    return img.resize((size, size), Image.LANCZOS)


def main() -> int:
    here = os.path.dirname(os.path.abspath(__file__))
    assets = os.path.join(here, "assets")
    os.makedirs(assets, exist_ok=True)

    frames = [draw_icon(s) for s in SIZES]

    ico = os.path.join(assets, "cryptotool.ico")
    frames[-1].save(ico, format="ICO", sizes=[(s, s) for s in SIZES],
                    append_images=frames[:-1])

    png = os.path.join(assets, "cryptotool.png")
    frames[-1].save(png, format="PNG")

    print(f"ecrit   : {ico}")
    print(f"ecrit   : {png}")
    print("tailles :", ", ".join(f"{s}x{s}" for s in SIZES))
    return 0


if __name__ == "__main__":
    sys.exit(main())
