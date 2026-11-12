"""Game2Earn : les images du jeu dessinées par programme (interface, icônes, effets, textures techniques).

Elles remplacent celles de Sauerbraten, dont la licence interdit l'usage commercial. Tout ce que ce fichier produit
est à nous (CC0) : formes simples, dégradés et bruit, aux dimensions et emplacements attendus par le moteur.
    python3 -I images.py <dossier racine du jeu>
"""
import math
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

RACINE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("racine")
FONTE = Path(__file__).resolve().parent / "polices" / "DejaVuSans-Bold.ttf"

# Couleurs de Game2Earn
FOND = (16, 20, 30)
PANNEAU = (24, 30, 44)
BORD = (70, 84, 110)
ACCENT = (255, 176, 32)
BLEU = (64, 140, 255)
ROUGE = (240, 64, 64)
VERT = (60, 200, 110)
JAUNE = (250, 210, 60)
GRIS = (170, 176, 190)
BLANC = (240, 244, 250)

random.seed(2026)
np.random.seed(2026)


def sauver(img, chemin, mode=None):
    chemin = RACINE / chemin
    chemin.parent.mkdir(parents=True, exist_ok=True)
    if mode:
        img = img.convert(mode)
    if chemin.suffix == ".jpg":
        img.convert("RGB").save(chemin, quality=92)
    else:
        img.save(chemin, optimize=True)


def toile(w, h, couleur=(0, 0, 0, 0), ech=4):
    """Une image agrandie (ech fois) pour dessiner net, réduite à la fin par fini()."""
    img = Image.new("RGBA", (w * ech, h * ech), couleur)
    return img, ImageDraw.Draw(img), ech


def fini(img, ech):
    return img.resize((img.width // ech, img.height // ech), Image.LANCZOS)


def police(taille):
    return ImageFont.truetype(str(FONTE), taille)


def radial(n, puissance=1.0, centre=0.0):
    """Disque flou : 1 au centre, 0 au bord."""
    y, x = np.mgrid[0:n, 0:n]
    d = np.sqrt((x - (n - 1) / 2) ** 2 + (y - (n - 1) / 2) ** 2) / (n / 2)
    v = np.clip(1 - np.clip((d - centre) / (1 - centre), 0, 1), 0, 1) ** puissance
    return v


def bruit(n, echelles=(4, 8, 16, 32), graine=0):
    """Bruit lisse et répétable sur les bords (pour tuiler)."""
    rng = np.random.default_rng(graine)
    total = np.zeros((n, n))
    poids = 0
    for i, e in enumerate(echelles):
        g = rng.random((e, e))
        g = np.pad(g, 1, mode="wrap")
        img = Image.fromarray((g * 255).astype(np.uint8)).resize((n + 2 * n // e, n + 2 * n // e), Image.BICUBIC)
        a = np.asarray(img, dtype=float)[n // e:n // e + n, n // e:n // e + n] / 255
        w = 1 / (i + 1)
        total += a * w
        poids += w
    total /= poids
    return (total - total.min()) / (total.max() - total.min() + 1e-9)


def gris(arr):
    return Image.fromarray((np.clip(arr, 0, 1) * 255).astype(np.uint8), "L")


def rgb_de(arr, couleur):
    a = np.clip(arr, 0, 1)[..., None]
    return Image.fromarray((a * np.array(couleur)).astype(np.uint8), "RGB")


# ---------------------------------------------------------------- interface (data/)

def habillage():
    """data/guiskin.png : le cadre des menus. Géométrie imposée par engine/3dgui.cpp (skinx, skiny, en 256x128)."""
    img, d, e = toile(512, 256)
    k = 2 * e  # unités du moteur -> pixels de la toile

    def boite(x1, y1, x2, y2, fond, bord, r=8):
        d.rounded_rectangle([x1 * k, y1 * k, x2 * k, y2 * k], radius=r * k, fill=fond + (238,), outline=bord + (255,),
                            width=int(1.5 * k))

    # onglet non choisi (à droite), plus sombre, posé sur le corps
    boite(140, 9, 226, 47, (18, 22, 32), BORD, 6)
    # corps
    boite(13, 44, 244, 116, PANNEAU, BORD, 8)
    # onglet choisi (à gauche), fondu dans le corps
    boite(25, 7, 116, 52, PANNEAU, BORD, 6)
    d.rectangle([(25 + 0.75) * k, 40 * k, (116 - 0.75) * k, 52 * k], fill=PANNEAU + (238,))
    # filet de couleur en haut de l'onglet choisi
    d.rounded_rectangle([31 * k, 9.5 * k, 110 * k, 11 * k], radius=k, fill=ACCENT + (255,))
    sauver(fini(img, e), "data/guiskin.png")


def surlignage():
    """data/guioverlay.png : le reflet sur l'élément survolé (dégradé doux)."""
    n = 256
    y = np.linspace(0, 1, n)[:, None] * np.ones((1, n))
    x = np.linspace(-1, 1, n)[None, :] * np.ones((n, 1))
    alpha = (0.55 - 0.35 * y) * (1 - x ** 8)
    img = np.zeros((n, n, 4), np.uint8)
    img[..., :3] = ACCENT
    img[..., 3] = (np.clip(alpha, 0, 1) * 255).astype(np.uint8)
    sauver(Image.fromarray(img, "RGBA"), "data/guioverlay.png")


def curseur_de_glissiere():
    img, d, e = toile(16, 64)
    d.rounded_rectangle([2 * e, 4 * e, 14 * e, 60 * e], radius=5 * e, fill=GRIS + (255,), outline=BLANC + (255,),
                        width=e)
    sauver(fini(img, e), "data/guislider.png")


def curseur():
    img, d, e = toile(64, 64, (0, 0, 0, 255))
    d.polygon([(2 * e, 2 * e), (2 * e, 44 * e), (14 * e, 33 * e), (24 * e, 54 * e), (31 * e, 51 * e),
               (21 * e, 30 * e), (37 * e, 30 * e)], fill=BLANC + (255,), outline=FOND + (255,))
    sauver(fini(img, e).convert("RGB"), "data/guicursor.png")


def viseurs():
    """Viseurs : data/crosshair.png et data/hit.png (blanc sur noir : le moteur les mélange en addition)."""
    def viseur(nom, dessin, taille=32):
        img, d, e = toile(taille, taille, (0, 0, 0, 255))
        dessin(d, e, taille)
        sauver(fini(img, e).convert("RGB"), nom)

    def croix(d, e, t, ecart=4, long=10, ep=2, point=False, rond=False):
        c = t / 2 * e
        for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            x1, y1 = c + dx * ecart * e, c + dy * ecart * e
            x2, y2 = c + dx * (ecart + long) * e, c + dy * (ecart + long) * e
            d.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 255), width=ep * e)
        if point:
            d.ellipse([c - 1.5 * e, c - 1.5 * e, c + 1.5 * e, c + 1.5 * e], fill=(255, 255, 255, 255))
        if rond:
            d.ellipse([c - 11 * e, c - 11 * e, c + 11 * e, c + 11 * e], outline=(255, 255, 255, 255), width=e * 2)

    viseur("data/crosshair.png", lambda d, e, t: croix(d, e, t, point=True))
    viseur("data/hit.png", lambda d, e, t: croix(d, e, t, ecart=2, long=11, ep=3, point=True))
    viseur("data/teammate.png", lambda d, e, t: d.polygon(
        [(6 * e, 8 * e), (26 * e, 8 * e), (16 * e, 24 * e)], fill=(255, 255, 255, 255)))
    sauver(Image.open(RACINE / "data/teammate.png").convert("L"), "data/teammate.png")

    # la liste des viseurs proposés dans les réglages (data/menus.cfg : packages/crosshairs/...)
    formes = {
        "x": dict(), "x_dot": dict(point=True), "o": dict(ecart=11, long=0, rond=True),
        "o_dot": dict(ecart=11, long=0, rond=True, point=True), "o_x": dict(rond=True),
        "dot": dict(ecart=0, long=0, point=True), "dot_wide": dict(ecart=8, long=6, point=True),
        "wide": dict(ecart=8, long=6), "star": dict(ecart=1, long=8, ep=1, point=True),
    }
    for nom, f in formes.items():
        viseur(f"packages/crosshairs/{nom}.png", lambda d, e, t, f=f: croix(d, e, t, **f))
        viseur(f"packages/crosshairs/{nom}-hit.png", lambda d, e, t, f=f: croix(d, e, t, **{**f, "ep": 3}))


def fonds():
    """Écran de chargement et fond des menus."""
    n = 256
    b = bruit(n, (2, 4, 8), 1)
    base = np.stack([FOND[i] / 255 + 0.05 * (b - 0.5) for i in range(3)], -1)
    sauver(Image.fromarray((np.clip(base, 0, 1) * 255).astype(np.uint8), "RGB"), "data/background.png")
    detail = np.zeros((n, n, 4), np.uint8)
    detail[..., :3] = 255
    detail[..., 3] = (bruit(n, (16, 32, 64), 2) * 40).astype(np.uint8)
    sauver(Image.fromarray(detail, "RGBA"), "data/background_detail.png")
    img, d, e = toile(64, 64)
    d.regular_polygon((32 * e, 32 * e, 26 * e), 6, outline=ACCENT + (90,), width=2 * e)
    sauver(fini(img, e), "data/background_decal.png")

    img, d, e = toile(512, 64)
    d.rounded_rectangle([4 * e, 18 * e, 508 * e, 46 * e], radius=12 * e, fill=PANNEAU + (255,), outline=BORD + (255,),
                        width=2 * e)
    sauver(fini(img, e).convert("RGB"), "data/loading_frame.png")
    img, d, e = toile(32, 32)
    d.rectangle([0, 6 * e, 32 * e, 26 * e], fill=ACCENT + (255,))
    sauver(fini(img, e), "data/loading_bar.png")

    img, d, e = toile(256, 256)
    d.rounded_rectangle([4 * e, 4 * e, 252 * e, 252 * e], radius=14 * e, outline=BORD + (255,), width=6 * e)
    sauver(fini(img, e), "data/mapshot_frame.png")


def logos():
    for nom, (w, h) in {"data/logo.png": (512, 256), "data/logo_1024.png": (1024, 512)}.items():
        img = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        f = police(h // 4)
        d.text((w / 2, h * 0.45), "GAME2EARN", font=f, anchor="mm", fill=BLANC + (255,), stroke_width=h // 64,
               stroke_fill=FOND + (255,))
        f2 = police(h // 9)
        d.text((w / 2, h * 0.72), "ARENA", font=f2, anchor="mm", fill=ACCENT + (255,))
        sauver(img, nom)
    img, d, e = toile(256, 256)
    d.regular_polygon((128 * e, 128 * e, 110 * e), 6, fill=PANNEAU + (255,), outline=ACCENT + (255,), width=8 * e)
    sauver(fini(img, e), "data/cube.png")
    img, d, e = toile(128, 64)
    d.rounded_rectangle([2 * e, 2 * e, 126 * e, 62 * e], radius=10 * e, fill=PANNEAU + (255,))
    sauver(fini(img, e), "data/cube2badge.png")


# ---------------------------------------------------------------- tête haute (packages/hud/)

def pictogramme(d, e, nom, x, y, t, couleur):
    """Petits dessins simples, réutilisés par les icônes de la tête haute et des menus."""
    c = couleur + (255,)
    cx, cy = x + t / 2, y + t / 2
    u = t / 16

    def P(px, py):
        return (x + px * u, y + py * u)

    if nom == "armure":
        d.polygon([P(3, 3), P(6, 2), P(8, 3.5), P(10, 2), P(13, 3), P(13, 9), P(8, 14), P(3, 9)], fill=c)
    elif nom == "soin":
        d.rectangle([P(6, 2.5), P(10, 13.5)], fill=c)
        d.rectangle([P(2.5, 6), P(13.5, 10)], fill=c)
    elif nom == "poing":
        d.rounded_rectangle([P(3, 5), P(13, 12)], radius=2 * u, fill=c)
        for i in range(4):
            d.line([P(5 + 2.2 * i, 5), P(5 + 2.2 * i, 8)], fill=(0, 0, 0, 255), width=int(u))
    elif nom == "cartouches":
        for i in range(3):
            d.rounded_rectangle([P(3 + 3.6 * i, 4), P(5.6 + 3.6 * i, 13)], radius=u, fill=c)
            d.rectangle([P(3 + 3.6 * i, 11), P(5.6 + 3.6 * i, 13)], fill=(200, 160, 60, 255))
    elif nom == "balles":
        for i in range(4):
            d.rounded_rectangle([P(2.5 + 2.9 * i, 4), P(4.5 + 2.9 * i, 13)], radius=u, fill=c)
    elif nom == "roquette":
        d.polygon([P(8, 1.5), P(10.5, 5), P(10.5, 11), P(12.5, 14), P(3.5, 14), P(5.5, 11), P(5.5, 5)], fill=c)
    elif nom == "fusil":
        d.rectangle([P(1.5, 7), P(14.5, 9)], fill=c)
        d.rectangle([P(3, 9), P(7, 12)], fill=c)
        d.rectangle([P(8, 5), P(11, 7)], fill=c)
    elif nom == "grenade":
        d.ellipse([P(3.5, 5), P(12.5, 14)], fill=c)
        d.rectangle([P(6.5, 2.5), P(9.5, 5.5)], fill=c)
    elif nom == "pistolet":
        d.polygon([P(2, 4.5), P(14, 4.5), P(14, 8), P(8, 8), P(7, 13.5), P(3.5, 13.5), P(4.5, 8), P(2, 8)], fill=c)
    elif nom == "eclair":
        d.polygon([P(9, 1.5), P(3.5, 9), P(7.5, 9), P(6, 14.5), P(12.5, 6.5), P(8.5, 6.5)], fill=c)
    elif nom == "drapeau":
        d.rectangle([P(3, 2), P(4.5, 14.5)], fill=(220, 220, 220, 255))
        d.polygon([P(4.5, 2.5), P(13.5, 5), P(4.5, 8.5)], fill=c)
    elif nom == "crane":
        d.ellipse([P(3, 2), P(13, 11)], fill=c)
        d.rectangle([P(5.5, 10), P(10.5, 14)], fill=c)
        d.ellipse([P(5, 5.5), P(7.5, 8)], fill=(0, 0, 0, 255))
        d.ellipse([P(8.5, 5.5), P(11, 8)], fill=(0, 0, 0, 255))
    elif nom == "fleche_g":
        d.polygon([P(11, 2.5), P(4, 8), P(11, 13.5)], fill=c)
    elif nom == "fleche_d":
        d.polygon([P(5, 2.5), P(12, 8), P(5, 13.5)], fill=c)
    elif nom == "info":
        d.ellipse([P(7, 2), P(9, 4)], fill=c)
        d.rectangle([P(7, 6), P(9, 14)], fill=c)
    elif nom == "menu":
        for i in range(3):
            d.rounded_rectangle([P(3, 3.5 + 4 * i), P(13, 5 + 4 * i)], radius=u * 0.7, fill=c)
    elif nom == "sortie":
        d.line([P(3.5, 3.5), P(12.5, 12.5)], fill=c, width=int(2.2 * u))
        d.line([P(12.5, 3.5), P(3.5, 12.5)], fill=c, width=int(2.2 * u))
    elif nom == "bulle":
        d.rounded_rectangle([P(2, 3), P(14, 11)], radius=2 * u, fill=c)
        d.polygon([P(4, 10), P(4, 14), P(8, 10)], fill=c)
    elif nom == "case":
        d.rounded_rectangle([P(3, 3), P(13, 13)], radius=1.5 * u, outline=c, width=int(1.4 * u))
    elif nom == "case_cochee":
        d.rounded_rectangle([P(3, 3), P(13, 13)], radius=1.5 * u, outline=c, width=int(1.4 * u))
        d.line([P(5, 8), P(7.3, 10.5), P(11.5, 5)], fill=ACCENT + (255,), width=int(1.8 * u))
    elif nom == "radio":
        d.ellipse([P(3, 3), P(13, 13)], outline=c, width=int(1.4 * u))
    elif nom == "radio_coche":
        d.ellipse([P(3, 3), P(13, 13)], outline=c, width=int(1.4 * u))
        d.ellipse([P(5.8, 5.8), P(10.2, 10.2)], fill=ACCENT + (255,))
    elif nom == "serveur":
        for i in range(3):
            d.rounded_rectangle([P(3, 2.5 + 4 * i), P(13, 5.5 + 4 * i)], radius=u * 0.7, fill=c)
    elif nom == "cadenas":
        d.arc([P(5, 2), P(11, 9)], 180, 360, fill=c, width=int(1.5 * u))
        d.rounded_rectangle([P(3.5, 7), P(12.5, 14)], radius=u, fill=c)
    elif nom == "oeil":
        d.ellipse([P(2, 5), P(14, 11)], outline=c, width=int(1.3 * u))
        d.ellipse([P(6.5, 6.5), P(9.5, 9.5)], fill=c)
    elif nom == "cube":
        d.polygon([P(8, 2), P(14, 5), P(8, 8), P(2, 5)], fill=c)
        d.polygon([P(2, 5), P(8, 8), P(8, 14.5), P(2, 11.5)], fill=tuple(int(v * 0.7) for v in couleur) + (255,))
        d.polygon([P(14, 5), P(8, 8), P(8, 14.5), P(14, 11.5)], fill=tuple(int(v * 0.5) for v in couleur) + (255,))
    elif nom == "main":
        d.rounded_rectangle([P(4, 7), P(12, 14)], radius=2 * u, fill=c)
        for i in range(4):
            d.rounded_rectangle([P(4 + 2 * i, 2.5 + (i % 3)), P(5.6 + 2 * i, 9)], radius=0.8 * u, fill=c)
    elif nom == "carte":
        d.polygon([P(2, 3.5), P(6, 2), P(10, 3.5), P(14, 2), P(14, 12.5), P(10, 14), P(6, 12.5), P(2, 14)], fill=c)
    elif nom == "piece":
        d.ellipse([P(3, 3), P(13, 13)], fill=c)
        d.ellipse([P(5.5, 5.5), P(10.5, 10.5)], outline=(0, 0, 0, 120), width=int(u))
    elif nom == "personnage":
        d.ellipse([P(5.5, 1.5), P(10.5, 6.5)], fill=c)
        d.rounded_rectangle([P(4, 7.5), P(12, 14.5)], radius=2.5 * u, fill=c)
    elif nom == "epee":
        d.line([P(3, 13), P(13, 3)], fill=c, width=int(2 * u))
        d.line([P(3.5, 9.5), P(6.5, 12.5)], fill=c, width=int(2 * u))
    else:
        d.ellipse([P(4, 4), P(12, 12)], fill=c)


def icone(nom, pictos, couleur=BLANC, fond=PANNEAU, taille=64, cadre=True):
    img, d, e = toile(taille, taille)
    if cadre:
        d.rounded_rectangle([1 * e, 1 * e, (taille - 1) * e, (taille - 1) * e], radius=taille / 7 * e,
                            fill=fond + (255,), outline=BORD + (255,), width=max(1, taille // 32) * e)
    m = taille * 0.14
    pictogramme(d, e, pictos, m * e, m * e, (taille - 2 * m) * e, couleur)
    return fini(img, e)


def tete_haute():
    # 4x4 icônes de 64 pixels (game.h, HICON_*)
    ordre = [("armure", BLEU), ("armure", VERT), ("armure", JAUNE), ("soin", ROUGE),
             ("poing", GRIS), ("cartouches", ROUGE), ("balles", GRIS), ("roquette", ACCENT),
             ("fusil", BLEU), ("grenade", VERT), ("pistolet", GRIS), ("eclair", (180, 90, 255)),
             ("drapeau", ROUGE), ("drapeau", BLEU), ("drapeau", GRIS), ("crane", BLANC)]
    planche = Image.new("RGBA", (256, 256), (0, 0, 0, 0))
    for i, (p, c) in enumerate(ordre):
        planche.paste(icone(p, p, c), ((i % 4) * 64, (i // 4) * 64))
    sauver(planche, "packages/hud/items.png")

    # radar et boussole
    img, d, e = toile(256, 256)
    d.ellipse([4 * e, 4 * e, 252 * e, 252 * e], fill=FOND + (170,), outline=BORD + (255,), width=4 * e)
    for r in (40, 80):
        d.ellipse([(128 - r) * e, (128 - r) * e, (128 + r) * e, (128 + r) * e], outline=BORD + (110,), width=e * 2)
    sauver(fini(img, e), "packages/hud/radar.png")
    img, d, e = toile(256, 256)
    d.ellipse([4 * e, 4 * e, 252 * e, 252 * e], outline=BORD + (255,), width=4 * e)
    d.polygon([(128 * e, 10 * e), (118 * e, 34 * e), (138 * e, 34 * e)], fill=ACCENT + (255,))
    sauver(fini(img, e), "packages/hud/compass.png")

    # points sur le radar
    teintes = {"blue": BLEU, "red": ROUGE, "neutral": BLANC, "grey": GRIS}
    for nom, c in teintes.items():
        def point(dessin, suffixe=""):
            img, d, e = toile(32, 32)
            dessin(d, e)
            sauver(fini(img, e), f"packages/hud/blip_{nom}{suffixe}.png")

        point(lambda d, e, c=c: d.ellipse([8 * e, 8 * e, 24 * e, 24 * e], fill=c + (255,), outline=(0, 0, 0, 255),
                                          width=2 * e))
        if nom == "grey":
            continue
        point(lambda d, e, c=c: d.polygon([(16 * e, 5 * e), (27 * e, 26 * e), (5 * e, 26 * e)], fill=c + (255,),
                                          outline=(0, 0, 0, 255)), "_alive")
        point(lambda d, e, c=c: (d.line([(8 * e, 8 * e), (24 * e, 24 * e)], fill=c + (255,), width=5 * e),
                                 d.line([(24 * e, 8 * e), (8 * e, 24 * e)], fill=c + (255,), width=5 * e)), "_dead")
        img = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        img.paste(icone("drapeau", "drapeau", c, taille=32, cadre=False), (0, 0))
        sauver(img, f"packages/hud/blip_{nom}_flag.png")
        if nom != "neutral":
            sauver(icone("crane", "crane", c, taille=32, cadre=False), f"packages/hud/blip_{nom}_skull.png")

    # voile rouge des dégâts (bords de l'écran)
    n = 256
    v = 1 - radial(n, 1.6, 0.0)
    img = np.zeros((n, n, 4), np.uint8)
    img[..., 0] = 200
    img[..., 3] = (np.clip(v, 0, 1) * 255).astype(np.uint8)
    sauver(Image.fromarray(img, "RGBA"), "packages/hud/damage.png")


def chiffres():
    """packages/hud/digit_*.png : les chiffres de la tête haute (cases de 32x32 tous les 48 pixels en hauteur, voir digit_font.cfg)."""
    f = police(28)
    for nom, c in {"digit_grey": BLANC, "digit_blue": BLEU, "digit_red": ROUGE}.items():
        img = Image.new("RGBA", (128, 128), (0, 0, 0, 0))
        d = ImageDraw.Draw(img)
        for i in range(10):
            x, y = (i % 4) * 32, (i // 4) * 48
            d.text((x + 16, y + 16), str(i), font=f, anchor="mm", fill=c + (255,), stroke_width=2,
                   stroke_fill=(0, 0, 0, 255))
        sauver(img, f"packages/hud/{nom}.png")


# ---------------------------------------------------------------- icônes des menus (packages/icons/)

def icones():
    noms = {
        "action": "eclair", "arrow_bw": "fleche_g", "arrow_fw": "fleche_d", "chat": "bulle",
        "checkbox_off": "case", "checkbox_on": "case_cochee", "radio_off": "radio", "radio_on": "radio_coche",
        "chest": "armure", "coins": "piece", "cube": "cube", "exit": "sortie", "hand": "main", "info": "info",
        "map": "carte", "menu": "menu", "sauer": "cube", "server": "serveur", "serverfull": "serveur",
        "serverlock": "cadenas", "serverpriv": "cadenas", "serverunk": "serveur", "spectator": "oeil",
        "sword": "epee",
    }
    for nom, p in noms.items():
        sauver(icone(nom, p), f"packages/icons/{nom}.jpg")
    # les icônes des personnages
    for perso, c in {"g2e_homme": GRIS, "g2e_femme": GRIS}.items():
        sauver(icone(perso, "personnage", c), f"packages/icons/{perso}.jpg")
        sauver(icone(perso, "personnage", BLEU), f"packages/icons/{perso}_blue.jpg")
        sauver(icone(perso, "personnage", ROUGE), f"packages/icons/{perso}_red.jpg")
    sauver(Image.new("RGBA", (64, 64), (0, 0, 0, 0)), "packages/icons/blank.png")
    # pinceaux de l'éditeur (stdedit.cfg)
    for nom, motif in {"brush_1c": [(0, 0)], "brush_21c": [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1)],
                       "brush_3s": [(x, y) for x in (-1, 0, 1) for y in (-1, 0, 1)],
                       "brush_421c": [(x, y) for x in range(-2, 3) for y in range(-2, 3) if abs(x) + abs(y) <= 2],
                       "brush_5s": [(x, y) for x in range(-2, 3) for y in range(-2, 3)],
                       "brush_7s": [(x, y) for x in range(-3, 4) for y in range(-3, 4)]}.items():
        img, d, e = toile(64, 64)
        for x, y in motif:
            d.rectangle([(28 + 8 * x) * e, (28 + 8 * y) * e, (35 + 8 * x) * e, (35 + 8 * y) * e], fill=BLANC + (255,))
        sauver(fini(img, e), f"packages/icons/{nom}.png")


# ---------------------------------------------------------------- effets (packages/particles/)

def particules():
    P = "packages/particles/"
    # base.png en LA : luminance = alpha
    v = gris(radial(64, 1.5))
    sauver(Image.merge("LA", (v, v)), P + "base.png")
    for nom, n, c in (("ball1", 128, (255, 150, 60)), ("ball2", 128, (255, 200, 120)), ("ball3", 64, (120, 170, 255))):
        r = radial(n, 1.2) * (0.6 + 0.4 * bruit(n, (4, 8), hash(nom) % 100))
        sauver(rgb_de(r, c), P + nom + ".png")
    v = radial(64, 2)
    sauver(Image.merge("RGBA", [gris(v * 0)] * 3 + [gris(v)]), P + "blob.png")
    # éclaboussures (4 variantes en 2x2, rgb inversé par le moteur)
    img = Image.new("L", (512, 512), 0)
    d = ImageDraw.Draw(img)
    for qx in range(2):
        for qy in range(2):
            for _ in range(14):
                r = random.uniform(8, 40)
                x = qx * 256 + 128 + random.gauss(0, 45)
                y = qy * 256 + 128 + random.gauss(0, 45)
                d.ellipse([x - r, y - r, x + r, y + r], fill=255)
    sauver(img.filter(ImageFilter.GaussianBlur(4)), P + "blood.png")
    # impact de balle
    n = 256
    sauver(rgb_de(radial(n, 2.5), (255, 255, 255)), P + "bullet.png")
    # explosion, flammes, fumée, vapeur
    sauver(rgb_de(radial(n, 1.0) * (0.5 + 0.5 * bruit(n, (4, 8, 16), 3)), (255, 170, 80)), P + "explosion.png")
    fl = Image.new("L", (256, 256), 0)
    for qx in range(2):
        for qy in range(2):
            t = radial(128, 1.4) * (0.4 + 0.6 * bruit(128, (4, 8, 16), qx * 2 + qy + 10))
            yy = np.linspace(1.2, 0.4, 128)[:, None]
            fl.paste(gris(t * yy), (qx * 128, qy * 128))
    sauver(fl, P + "flames.png")
    for nom, n, g in (("smoke", 128, 20), ("steam", 128, 21), ("snow", 128, 22)):
        t = radial(n, 1.2) * (0.5 + 0.5 * bruit(n, (4, 8, 16), g))
        if nom == "steam":
            sauver(gris(t), P + nom + ".png")
        else:
            sauver(Image.merge("RGBA", [gris(np.ones((n, n)) * 0.9)] * 3 + [gris(t)]), P + nom + ".png")
    # traînée et éclair
    x = np.linspace(-1, 1, 32)[:, None] * np.ones((1, 128))
    sauver(rgb_de(np.clip(1 - np.abs(x), 0, 1) ** 2, (255, 230, 180)), P + "flare.jpg")
    x = np.linspace(-1, 1, 64)[:, None] * np.ones((1, 256))
    sauver(rgb_de(np.clip(1 - np.abs(x), 0, 1) ** 3, (190, 210, 255)), P + "lightning.jpg")
    # éclairs de tir
    for nom, n, branches in (("muzzleflash1", 128, 4), ("muzzleflash2", 512, 6), ("muzzleflash3", 128, 5)):
        img, d, e = toile(n, n, (0, 0, 0, 255), 2)
        c = n * e / 2
        for i in range(branches):
            a = 2 * math.pi * i / branches
            d.polygon([(c + math.cos(a) * n * e * 0.48, c + math.sin(a) * n * e * 0.48),
                       (c + math.cos(a + 0.5) * n * e * 0.08, c + math.sin(a + 0.5) * n * e * 0.08),
                       (c + math.cos(a - 0.5) * n * e * 0.08, c + math.sin(a - 0.5) * n * e * 0.08)],
                      fill=(255, 200, 110, 255))
        img = fini(img, 2).filter(ImageFilter.GaussianBlur(n / 64))
        lum = Image.fromarray((np.asarray(img.convert("RGB"), float) * radial(n, 0.7)[..., None]).astype(np.uint8))
        sauver(lum, P + nom + ".jpg")
    # plasma, étincelle, brûlure
    sauver(Image.merge("RGBA", [gris(radial(256, 1.0) * k) for k in (0.6, 0.8, 1.0)] + [gris(radial(256, 1.2))]),
           P + "plasma.png")
    img, d, e = toile(64, 64)
    d.line([(32 * e, 4 * e), (32 * e, 60 * e)], fill=(255, 255, 255, 255), width=3 * e)
    d.line([(4 * e, 32 * e), (60 * e, 32 * e)], fill=(255, 255, 255, 255), width=3 * e)
    sauver(fini(img, e).filter(ImageFilter.GaussianBlur(1.5)), P + "spark.png")
    t = radial(256, 0.8) * (0.4 + 0.6 * bruit(256, (8, 16, 32), 30))
    sauver(Image.merge("RGBA", [gris(t * 0)] * 3 + [gris(t)]), P + "scorch.png")
    # reflets de l'objectif (4x4 en 512)
    lf = Image.new("L", (512, 512), 0)
    for i in range(4):
        for j in range(4):
            r = radial(128, 1 + i * 0.6, j * 0.2)
            lf.paste(gris(r), (i * 128, j * 128))
    sauver(lf, P + "lensflares.png")


# ---------------------------------------------------------------- textures techniques (packages/textures/, ...)

def textures_techniques():
    T = "packages/textures/"
    # « pas de texture » : damier visible
    img = Image.new("RGB", (128, 128), (60, 60, 70))
    d = ImageDraw.Draw(img)
    for x in range(0, 128, 32):
        for y in range(0, 128, 32):
            if (x + y) // 32 % 2 == 0:
                d.rectangle([x, y, x + 31, y + 31], fill=(200, 60, 200))
    sauver(img, T + "notexture.png")
    # texture par défaut de l'éditeur : grille claire
    img = Image.new("L", (256, 256), 150)
    d = ImageDraw.Draw(img)
    for i in range(0, 256, 32):
        d.line([(i, 0), (i, 255)], fill=110, width=2)
        d.line([(0, i), (255, i)], fill=110, width=2)
    d.rectangle([0, 0, 255, 255], outline=90, width=3)
    sauver(img, T + "default.png")
    sauver(Image.new("RGB", (128, 128), (110, 150, 200)), T + "sky.png")
    # texture en cours de téléchargement
    img, d, e = toile(128, 128, PANNEAU + (255,))
    for x, y, a in [(8, 8, 0), (120, 8, 1), (8, 120, 2), (120, 120, 3)]:
        sx, sy = (1 if a in (0, 2) else -1), (1 if a in (0, 1) else -1)
        d.line([(x * e, y * e), ((x + 18 * sx) * e, y * e)], fill=BORD + (255,), width=3 * e)
        d.line([(x * e, y * e), (x * e, (y + 18 * sy) * e)], fill=BORD + (255,), width=3 * e)
    d.text((64 * e, 64 * e), "...", font=police(28 * e), anchor="mm", fill=GRIS + (255,))
    sauver(fini(img, e), T + "downloading.png")
    # eau : normales et distorsion à partir d'un bruit
    n = 512
    h = bruit(n, (8, 16, 32, 64), 40)
    gy, gx = np.gradient(h)
    nx, ny = -gx * 40, -gy * 40
    nz = np.ones_like(nx)
    l = np.sqrt(nx ** 2 + ny ** 2 + nz ** 2)
    norm = np.stack([nx / l, ny / l, nz / l], -1) * 0.5 + 0.5
    norm_img = Image.fromarray((norm * 255).astype(np.uint8), "RGB")
    sauver(norm_img, T + "watern.jpg")
    sauver(norm_img, T + "waterfalln.jpg")
    dudv = np.stack([0.5 + 0.5 * (nx / l), 0.5 + 0.5 * (ny / l), np.zeros_like(nx)], -1)
    dudv_img = Image.fromarray((dudv * 255).astype(np.uint8), "RGB")
    sauver(dudv_img, T + "waterdudv.jpg")
    sauver(dudv_img, T + "waterfalldudv.jpg")
    sauver(rgb_de(0.6 + 0.4 * h, (90, 140, 170)), T + "waterfall.jpg")
    # herbe (lignes verticales fines, alpha)
    img = Image.new("RGBA", (512, 128), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for _ in range(500):
        x = random.uniform(0, 512)
        hgt = random.uniform(40, 125)
        d.line([(x, 127), (x + random.uniform(-6, 6), 127 - hgt)],
               fill=(70 + random.randint(0, 40), 130 + random.randint(0, 50), 50, 255), width=2)
    sauver(img, T + "grass.png")
    # surface de l'eau et lave
    sauver(rgb_de(0.55 + 0.45 * bruit(256, (4, 8, 16, 32), 41), (60, 120, 150)), T + "eau.jpg")
    b = bruit(256, (4, 8, 16, 32), 42)
    lave = np.stack([0.5 + 0.5 * b, 0.15 + 0.5 * b ** 2, 0.05 * b], -1)
    sauver(Image.fromarray((np.clip(lave, 0, 1) * 255).astype(np.uint8), "RGB"), T + "lave.jpg")
    # ciel : dégradé simple, six faces (skybox "skyboxes/g2e/ciel")
    n = 512
    haut, horizon, bas = np.array((40, 80, 150)), np.array((170, 200, 230)), np.array((60, 70, 80))
    y = np.linspace(0, 1, n)[:, None, None]
    cote = np.where(y < 0.5, haut + (horizon - haut) * (y / 0.5), horizon + (bas - horizon) * ((y - 0.5) / 0.5))
    cote = cote * np.ones((1, n, 1)) + 6 * (bruit(n, (4, 8), 43)[..., None] - 0.5)
    for f in ("bk", "ft", "lf", "rt"):
        sauver(Image.fromarray(np.clip(cote, 0, 255).astype(np.uint8), "RGB"), f"packages/skyboxes/g2e/ciel_{f}.jpg")
    sauver(Image.new("RGB", (n, n), tuple(int(v) for v in haut)), "packages/skyboxes/g2e/ciel_up.jpg")
    sauver(Image.new("RGB", (n, n), tuple(int(v) for v in bas)), "packages/skyboxes/g2e/ciel_dn.jpg")
    # caustiques (lumière sous l'eau) : 32 images d'une animation en boucle
    n = 128
    for i in range(32):
        a = 2 * math.pi * i / 32
        y, x = np.mgrid[0:n, 0:n] / n * 2 * math.pi
        v = (np.sin(x * 2 + math.sin(a) * 1.5 + np.sin(y * 3 + a)) + np.sin(y * 2 + math.cos(a) * 1.5 +
                                                                              np.sin(x * 3 - a)))
        v = np.clip(1 - np.abs(v) / 0.6, 0, 1) ** 2
        sauver(gris(v), f"packages/caustics/caust{i:02d}.png")
    # pinceaux de mélange de l'éditeur (packages/blendbrush/)
    for n in (8, 16, 32, 64, 128):
        dur = radial(n, 1, 0.85)
        sauver(gris(np.where(radial(n, 1) > 0, 1, 0)), f"packages/blendbrush/circle_{n}_solid.png")
        sauver(gris(dur), f"packages/blendbrush/circle_{n}_hard.png")
        sauver(gris(radial(n, 1)), f"packages/blendbrush/circle_{n}_soft.png")
    for n in (16, 32, 64, 128):
        sauver(gris(np.linspace(0, 1, n)[None, :] * np.ones((n, 1))), f"packages/blendbrush/gradient_{n}.png")
    for n in (64, 128):
        sauver(gris(bruit(n, (4, 8), n)), f"packages/blendbrush/noise_{n}.png")
    for n in (16, 32, 64):
        sauver(gris(np.ones((n, n))), f"packages/blendbrush/square_{n}_solid.png")
        a = np.ones((n, n))
        a[:2, :] = a[-2:, :] = a[:, :2] = a[:, -2:] = 0.5
        sauver(gris(a), f"packages/blendbrush/square_{n}_hard.png")


def client(dossier):
    """Les images du client web (client/src) : icônes des armes des commandes tactiles et fond de la page."""
    global RACINE
    RACINE = Path(dossier)
    for nom, (p, c) in {"saw": ("epee", GRIS), "shotgun": ("cartouches", ROUGE), "machinegun": ("balles", GRIS),
                        "rocket": ("roquette", ACCENT), "rifle": ("fusil", BLEU), "grenade": ("grenade", VERT),
                        "pistol": ("pistolet", GRIS)}.items():
        sauver(icone(nom, p, c), f"static/{nom}.png")
    b = bruit(256, (2, 4, 8), 5)
    fond = np.stack([np.full((256, 256), FOND[i] / 255) + 0.04 * (b - 0.5) for i in range(3)], -1)
    sauver(Image.fromarray((np.clip(fond, 0, 1) * 255).astype(np.uint8), "RGB"), "background.png")


if __name__ == "__main__" and len(sys.argv) > 2 and sys.argv[2] == "--client":
    client(sys.argv[1])
elif __name__ == "__main__":
    habillage()
    surlignage()
    curseur_de_glissiere()
    curseur()
    viseurs()
    fonds()
    logos()
    tete_haute()
    chiffres()
    icones()
    particules()
    textures_techniques()
    print("images :", sum(1 for _ in RACINE.rglob("*.*")))
