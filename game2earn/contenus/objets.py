"""Game2Earn : les objets du jeu que Red Eclipse n'a pas, modelés par programme (OBJ et textures, à nous, CC0).

Soins, armures, bonus, téléporteur, drapeaux, débris. Formes simples et lisibles (une boîte avec une croix pour les
soins, un bouclier pour l'armure...), aux noms attendus par le moteur (fpsgame/entities.cpp, ctf.h, weapon.cpp).
"""
import math
from pathlib import Path

from PIL import Image, ImageDraw

BLANC = (235, 238, 245)
ROUGE = (220, 50, 50)
BLEU = (60, 120, 255)
VERT = (60, 200, 110)
JAUNE = (250, 200, 50)
VIOLET = (170, 90, 255)
GRIS = (120, 128, 140)
ACCENT = (255, 176, 32)


class Maillage:
    def __init__(self):
        self.v, self.t, self.f = [], [], []

    def quad(self, a, b, c, d, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        i = len(self.v)
        self.v += [a, b, c, d]
        j = len(self.t)
        self.t += list(uv)
        self.f.append([(i + k, j + k) for k in range(4)])

    def tri(self, a, b, c, uv=((0, 0), (1, 0), (0.5, 1))):
        i = len(self.v)
        self.v += [a, b, c]
        j = len(self.t)
        self.t += list(uv)
        self.f.append([(i + k, j + k) for k in range(3)])

    def boite(self, x1, y1, z1, x2, y2, z2, uv=((0, 0), (1, 0), (1, 1), (0, 1))):
        P = lambda x, y, z: (x, y, z)  # noqa: E731
        self.quad(P(x1, y1, z2), P(x2, y1, z2), P(x2, y2, z2), P(x1, y2, z2), uv)  # dessus
        self.quad(P(x1, y2, z1), P(x2, y2, z1), P(x2, y1, z1), P(x1, y1, z1), uv)  # dessous
        self.quad(P(x1, y1, z1), P(x2, y1, z1), P(x2, y1, z2), P(x1, y1, z2), uv)
        self.quad(P(x2, y2, z1), P(x1, y2, z1), P(x1, y2, z2), P(x2, y2, z2), uv)
        self.quad(P(x1, y2, z1), P(x1, y1, z1), P(x1, y1, z2), P(x1, y2, z2), uv)
        self.quad(P(x2, y1, z1), P(x2, y2, z1), P(x2, y2, z2), P(x2, y1, z2), uv)

    def prisme(self, profil, z1, z2):
        """Un prisme vertical sur un profil (liste de points x, y dans le sens trigonométrique)."""
        n = len(profil)
        for k in range(n):
            (ax, ay), (bx, by) = profil[k], profil[(k + 1) % n]
            self.quad((ax, ay, z1), (bx, by, z1), (bx, by, z2), (ax, ay, z2), ((0, 1), (1, 1), (1, 0), (0, 0)))
        cx = sum(p[0] for p in profil) / n
        cy = sum(p[1] for p in profil) / n
        for k in range(n):
            (ax, ay), (bx, by) = profil[k], profil[(k + 1) % n]
            self.tri((cx, cy, z2), (ax, ay, z2), (bx, by, z2), ((0.5, 0.5), (0, 0), (1, 0)))
            self.tri((cx, cy, z1), (bx, by, z1), (ax, ay, z1), ((0.5, 0.5), (1, 0), (0, 0)))

    def ecrire(self, chemin: Path):
        # axes de l'OBJ : notre moteur lit (x, y, z) comme (z, -x, y) (engine/obj.h)
        lignes = [f"v {-y:.4f} {z:.4f} {x:.4f}" for x, y, z in self.v]
        lignes += [f"vt {u:.4f} {v:.4f}" for u, v in self.t]
        lignes += ["f " + " ".join(f"{a + 1}/{b + 1}" for a, b in f) for f in self.f]
        chemin.write_text("\n".join(lignes) + "\n")


def texture(chemin: Path, fond, motif=None, couleur=BLANC):
    img = Image.new("RGB", (128, 128), fond)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, 127, 127], outline=tuple(int(c * 0.6) for c in fond), width=6)
    if motif == "croix":
        d.rectangle([50, 20, 78, 108], fill=couleur)
        d.rectangle([20, 50, 108, 78], fill=couleur)
    elif motif == "bandes":
        for y in range(16, 128, 32):
            d.rectangle([0, y, 127, y + 10], fill=couleur)
    img.save(chemin, optimize=True)


def modele(racine: Path, nom: str, m: Maillage, fond, motif=None, couleur=BLANC, reglages=""):
    d = racine / "packages/models" / nom
    d.mkdir(parents=True, exist_ok=True)
    m.ecrire(d / "objet.obj")
    texture(d / "skin.png", fond, motif, couleur)
    (d / "obj.cfg").write_text(f'// Game2Earn : objet modelé par programme (game2earn/contenus/objets.py), CC0.\n'
                               f'objload "objet.obj"\nobjskin * "skin.png"\n{reglages}', encoding="utf-8")


def bouclier(r=4.0, h=1.4):
    pts = [(r * math.cos(a), r * 1.15 * math.sin(a)) for a in [math.radians(90 + k * 45) for k in range(8)]]
    m = Maillage()
    m.prisme(pts, -h / 2, h / 2)
    m.v = [(x, z, y + r * 1.2) for x, y, z in m.v]  # debout, posé au sol
    return m


def octaedre(r=3.5):
    m = Maillage()
    p = [(r, 0, 0), (0, r, 0), (-r, 0, 0), (0, -r, 0)]
    for k in range(4):
        a, b = p[k], p[(k + 1) % 4]
        m.tri((0, 0, r), a, b)
        m.tri((0, 0, -r), b, a)
    return m


def anneau(r1=7, r2=9, h=1.0, n=16):
    m = Maillage()
    for k in range(n):
        a, b = 2 * math.pi * k / n, 2 * math.pi * (k + 1) / n
        ca, sa, cb, sb = math.cos(a), math.sin(a), math.cos(b), math.sin(b)
        m.quad((r2 * ca, r2 * sa, -h), (r2 * cb, r2 * sb, -h), (r2 * cb, r2 * sb, h), (r2 * ca, r2 * sa, h))
        m.quad((r1 * cb, r1 * sb, -h), (r1 * ca, r1 * sa, -h), (r1 * ca, r1 * sa, h), (r1 * cb, r1 * sb, h))
        m.quad((r1 * ca, r1 * sa, h), (r2 * ca, r2 * sa, h), (r2 * cb, r2 * sb, h), (r1 * cb, r1 * sb, h))
        m.quad((r1 * cb, r1 * sb, -h), (r2 * cb, r2 * sb, -h), (r2 * ca, r2 * sa, -h), (r1 * ca, r1 * sa, -h))
    return m


def drapeau():
    m = Maillage()
    m.boite(-0.4, -0.4, 0, 0.4, 0.4, 22, ((0, 0), (0.05, 0), (0.05, 0.05), (0, 0.05)))  # hampe
    m.boite(0.4, -0.25, 13, 11, 0.25, 21)  # tissu
    return m


def eclat(graine, taille=1.6):
    m = Maillage()
    s = taille * (0.7 + 0.15 * graine)
    m.boite(-s, -s * 0.7, -s * 0.5, s, s * 0.7, s * 0.5)
    return m


def objets(racine: Path):
    tourne = ""
    # soins : boîte blanche à croix rouge ; bonus de santé : plus grande, croix dorée
    m = Maillage()
    m.boite(-3, -3, 0, 3, 3, 5)
    modele(racine, "health", m, BLANC, "croix", ROUGE, tourne)
    m = Maillage()
    m.boite(-4, -4, 0, 4, 4, 6.5)
    modele(racine, "boost", m, (40, 44, 56), "croix", JAUNE, tourne)
    # armures : boucliers
    modele(racine, "armor/green", bouclier(), VERT, "bandes", (30, 120, 60))
    modele(racine, "armor/yellow", bouclier(), JAUNE, "bandes", (160, 120, 20))
    # dégâts quadruplés : octaèdre violet
    modele(racine, "quad", octaedre(), VIOLET, "bandes", (110, 50, 200), "mdltrans 0 0 4\nmdlspin 90\n")
    # téléporteur : anneau
    modele(racine, "teleporter", anneau(), (40, 44, 56), "bandes", ACCENT, "mdltrans 0 0 1\n")
    # drapeaux
    for nom, c in (("red", ROUGE), ("blue", BLEU), ("neutral", BLANC)):
        modele(racine, f"flags/{nom}", drapeau(), c)
    # débris et morceaux (explosions)
    for i in range(1, 5):
        modele(racine, f"debris/debris0{i}", eclat(i), GRIS)
        modele(racine, f"barreldebris/debris0{i}", eclat(i), (110, 80, 50))
    for i in range(1, 4):
        modele(racine, f"gibs/gib0{i}", eclat(i, 1.0), (140, 30, 30))
