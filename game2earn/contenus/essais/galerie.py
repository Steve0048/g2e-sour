"""Game2Earn : une salle « galerie » avec des modèles posés face au départ, pour les photographier.
    python3 -I galerie.py <racine> <angle du départ> <modèle1,modèle2,...>
"""
import gzip, struct, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import carte_essai as c

def grille():
    g = {}
    sol = (c.MUR, c.MUR, c.MUR, c.MUR, c.PLAFOND, c.SOL)
    for x in range(c.N):
        for y in range(c.N):
            for z in range(4):
                g[(x, y, z)] = sol
    for (x1, y1, x2, y2) in [(18, 18, 46, 20), (18, 44, 46, 46), (18, 20, 20, 44), (44, 20, 46, 44)]:
        for x in range(x1, x2):
            for y in range(y1, y2):
                for z in range(4, 12):
                    g[(x, y, z)] = (c.MUR,) * 4 + (c.PLAFOND, c.MUR2)
    return g

def ents(modeles):
    e = []
    def ent(x, y, z, t, a1=0, a2=0, a3=0, a4=0, a5=0):
        e.append(struct.pack("<3f5h2B", x, y, z, a1, a2, a3, a4, a5, t, 0))
    sol = 64
    ent(32 * 16, 23 * 16, sol + 2, c.PLAYERSTART, int(sys.argv[2]) if len(sys.argv) > 2 else 0)
    for i in range(len(modeles)):
        ent(32 * 16 + (i - (len(modeles) - 1) / 2) * 14, 23 * 16 + 34, sol, 2, 180, i)
    for x, y in [(24, 24), (40, 24), (32, 38)]:
        ent(x * 16, y * 16, 140, c.LIGHT, 300, 255, 255, 255)
    return e

modeles = sys.argv[3].split(",")
e = ents(modeles)
out = bytearray(b"OCTA" + struct.pack("<9i", 33, 40, c.TAILLE, len(e), 0, 0, 0, 1, 0))
out += struct.pack("<BH", 0, 7) + b"ambient" + struct.pack("<i", 0x707070)
out += bytes([3]) + b"fps\0" + struct.pack("<HHH", 0, 0, 0)
for x in e: out += x
out += c.octree(grille())
r = Path(sys.argv[1])
(r / "packages/base/galerie.ogz").write_bytes(gzip.compress(bytes(out), mtime=0))
(r / "packages/base/galerie.cfg").write_text("mapmodelreset\n" + "".join(f'mmodel "{m}"\n' for m in modeles))
