"""Game2Earn : une carte d'essai faite par programme (packages/base/g2e_essai.ogz), avec nos seules textures.

Elle sert à vérifier le paquet de base et à lancer le serveur avant que l'admin dessine les vraies cartes dans
l'éditeur (étape 4). Les textes de la carte sont en ASCII (le moteur n'affiche pas l'UTF-8). Format des cartes de Cube 2 version 33 (engine/worldio.cpp, save_world), sans éclairage précalculé :
l'éclairage se calcule dans l'éditeur (calclight) puis la carte est réenregistrée.
    python3 -I carte_essai.py <racine>
"""
import gzip
import struct
import sys
from pathlib import Path

TAILLE = 1024          # taille du monde
CASE = 16              # taille d'une case de la grille
N = TAILLE // CASE     # 64 cases de côté

# numéros des textures (ordre de data/default_map_settings.cfg : 0 ciel, 1 par défaut, puis trak5 à partir de 2)
CIEL, DEFAUT = 0, 1
SOL, SOL2, MUR, MUR2, PLAFOND, CAISSE, PANNEAU = 32, 34, 18, 19, 20, 13, 23

# entités (shared/ents.h et fpsgame/game.h)
LIGHT, PLAYERSTART = 1, 3
I_SHELLS, I_BULLETS, I_ROCKETS, I_ROUNDS, I_GRENADES, I_CARTRIDGES, I_HEALTH, I_BOOST, I_GREENARMOUR, \
    I_YELLOWARMOUR, I_QUAD = range(8, 19)
JUMPPAD = 23
FLAG = 31


def grille():
    """La carte en cases : None = vide, sinon les 6 textures (gauche, droite, arrière, avant, dessous, dessus)."""
    g = {}

    def plein(x1, y1, z1, x2, y2, z2, tex):
        for x in range(x1, x2):
            for y in range(y1, y2):
                for z in range(z1, z2):
                    g[(x, y, z)] = tex

    sol = (MUR, MUR, MUR, MUR, PLAFOND, SOL)
    mur = (MUR, MUR, MUR, MUR, PLAFOND, MUR2)
    caisse = (CAISSE,) * 6
    # sol : 4 cases d'épaisseur ; arène de 8 à 56
    plein(0, 0, 0, N, N, 4, sol)
    # murs extérieurs (hauteur 16 cases)
    for (x1, y1, x2, y2) in [(6, 6, 58, 8), (6, 56, 58, 58), (6, 8, 8, 56), (56, 8, 58, 56)]:
        plein(x1, y1, 4, x2, y2, 20, mur)
    # quatre piliers
    for px, py in [(16, 16), (44, 16), (16, 44), (44, 44)]:
        plein(px, py, 4, px + 4, py + 4, 20, (PANNEAU,) * 4 + (PLAFOND, MUR2))
    # plateforme centrale (3 cases de haut), sol différent
    plein(26, 26, 4, 38, 38, 7, (MUR, MUR, MUR, MUR, PLAFOND, SOL2))
    # caisses pour se couvrir
    for cx, cy in [(12, 30), (50, 30), (30, 12), (30, 50)]:
        plein(cx, cy, 4, cx + 3, cy + 3, 7, caisse)
    return g


def octree(g):
    """Le monde en arbre de cubes (8 enfants par cube), comme engine/worldio.cpp savec()."""
    out = bytearray()

    def contenu(x, y, z, n):
        """Toutes les cases de ce cube, si elles sont identiques ; sinon None."""
        premier = g.get((x, y, z))
        for i in range(x, x + n):
            for j in range(y, y + n):
                for k in range(z, z + n):
                    if g.get((i, j, k)) != premier:
                        return "mixte"
        return premier

    def ecrire(x, y, z, n):
        # n : taille du cube en cases ; ses 8 enfants ont la taille n // 2, ordre : x, puis y, puis z
        h = n // 2
        for i in range(8):
            cx, cy, cz = x + (i & 1) * h, y + ((i >> 1) & 1) * h, z + ((i >> 2) & 1) * h
            c = contenu(cx, cy, cz, h) if h > 1 else g.get((cx, cy, cz))
            if c == "mixte":
                out.append(0)  # OCTSAV_CHILDREN
                ecrire(cx, cy, cz, h)
            elif c is None:
                out.append(1)  # OCTSAV_EMPTY
                out.extend(struct.pack("<6H", *([DEFAUT] * 6)))
            else:
                out.append(2)  # OCTSAV_SOLID
                out.extend(struct.pack("<6H", *c))

    ecrire(0, 0, 0, N)
    return bytes(out)


def entites():
    sol = 4 * CASE
    e = []

    def ent(x, y, z, type_, a1=0, a2=0, a3=0, a4=0, a5=0):
        e.append(struct.pack("<3f5h2B", x * CASE, y * CASE, z, a1, a2, a3, a4, a5, type_, 0))

    # départs des joueurs (angle vers le centre)
    for x, y, angle in [(10, 10, 315), (54, 10, 45), (10, 54, 225), (54, 54, 135), (32, 10, 0), (32, 54, 180),
                        (10, 32, 270), (54, 32, 90)]:
        ent(x, y, sol + 2, PLAYERSTART, angle)
    # objets
    for x, y, t in [(22, 22, I_SHELLS), (42, 22, I_BULLETS), (22, 42, I_ROCKETS), (42, 42, I_ROUNDS),
                    (32, 20, I_GRENADES), (32, 44, I_CARTRIDGES), (20, 32, I_HEALTH), (44, 32, I_HEALTH),
                    (12, 12, I_GREENARMOUR), (52, 52, I_GREENARMOUR)]:
        ent(x, y, sol + 8, t)
    ent(32, 32, 7 * CASE + 8, I_YELLOWARMOUR)
    ent(30, 30, 7 * CASE + 8, I_BOOST)
    # tremplins vers la plateforme (poussée verticale, puis horizontale vers le centre)
    for x, y, py, px in [(32, 23, 25, 0), (32, 41, -25, 0), (23, 32, 0, 25), (41, 32, 0, -25)]:
        ent(x, y, sol + 1, JUMPPAD, 40, py, px)
    # drapeaux (capture du drapeau) : équipe 1 et 2
    ent(32, 10, sol + 2, FLAG, 0, 1)
    ent(32, 54, sol + 2, FLAG, 180, 2)
    # lumières (rayon, rouge, vert, bleu)
    for x, y in [(18, 18), (46, 18), (18, 46), (46, 46), (32, 32)]:
        ent(x, y, 14 * CASE, LIGHT, 480, 255, 245, 230)
    return e


def variables():
    """Variables de la carte : (type, nom, valeur). Types : 0 entier, 1 réel, 2 texte."""
    v = [(2, "maptitle", "Game2Earn : arene d'essai"), (0, "skylight", 0x8090a0), (0, "ambient", 0x484c54)]
    out = bytearray()
    for t, nom, val in v:
        out += struct.pack("<BH", t, len(nom)) + nom.encode()
        if t == 0:
            out += struct.pack("<i", val)
        elif t == 1:
            out += struct.pack("<f", val)
        else:
            b = val.encode("utf-8")
            out += struct.pack("<H", len(b)) + b
    return len(v), bytes(out)


def carte():
    e = entites()
    nvars, vars_ = variables()
    out = bytearray()
    # en-tête : OCTA, version 33, taille de l'en-tête 40, monde, entités, pvs, lightmaps, blendmap, variables, vslots
    out += b"OCTA" + struct.pack("<9i", 33, 40, TAILLE, len(e), 0, 0, 0, nvars, 0)
    out += vars_
    out += bytes([3]) + b"fps\0"
    out += struct.pack("<HHH", 0, 0, 0)  # infos d'entités en plus, données du jeu, textures récentes
    for x in e:
        out += x
    out += octree(grille())
    return gzip.compress(bytes(out), mtime=0)


if __name__ == "__main__":
    racine = Path(sys.argv[1])
    f = racine / "packages/base/g2e_essai.ogz"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(carte())
    print(f, f.stat().st_size, "octets")
