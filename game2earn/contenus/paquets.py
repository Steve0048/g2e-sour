"""Game2Earn : fait les paquets du jeu pour le navigateur et le serveur, à partir du dossier « racine ».

    python3 -I paquets.py <racine> <sortie>

Même format que les recettes de Sour (assets/package.py), sans Emscripten : chaque fichier est rangé sous le nom de son
empreinte (sha256), chaque paquet est un fichier « <id>.sour », et l'index « .index.source » (CBOR) les décrit :
  - le mod « base » : tout ce que le jeu charge au démarrage (réglages, interface, textures, sons, police) ;
  - le mod « fps » : les personnages, armes et objets (packages/models) ;
  - une carte par fichier packages/base/<nom>.ogz (avec <nom>.cfg et son image, s'il y en a).
"""
import hashlib
import json
import sys
from pathlib import Path

import cbor2

AUDIO = {".ogg", ".wav", ".mp3"}


def empreinte(donnees: bytes) -> str:
    return hashlib.sha256(donnees).hexdigest()


class Paquets:
    def __init__(self, racine: Path, sortie: Path):
        self.racine = racine
        self.sortie = sortie
        self.assets = []  # ids, dans l'ordre
        self.bundles = []
        self.mods = []
        self.maps = []
        sortie.mkdir(parents=True, exist_ok=True)

    def asset(self, chemin: str):
        donnees = (self.racine / chemin).read_bytes()
        id_ = empreinte(donnees)
        cible = self.sortie / id_
        if not cible.exists():
            cible.write_bytes(donnees)
        if id_ not in self.assets:
            self.assets.append(id_)
        return [id_, chemin], donnees

    def bundle(self, chemins):
        assets, blocs = [], []
        for c in sorted(chemins):
            a, donnees = self.asset(c)
            assets.append(a)
            blocs.append((c, donnees))
        id_ = empreinte("".join(sorted(a[0] for a in assets)).encode())

        dossiers, vus = [], set()
        fichiers, debut = [], 0
        for c, donnees in blocs:
            parties = c.split("/")[:-1]
            for i in range(len(parties)):
                parent = "/" + "/".join(parties[:i])
                if (parent, parties[i]) not in vus:
                    vus.add((parent, parties[i]))
                    dossiers.append([parent if parent != "/" else "/", parties[i]])
            f = {"filename": "/" + c, "start": debut, "end": debut + len(donnees)}
            if Path(c).suffix in AUDIO:
                f["audio"] = 1
            fichiers.append(f)
            debut += len(donnees)
        meta = json.dumps({"files": fichiers, "remote_package_size": debut}).encode()
        dirs = json.dumps(dossiers).encode()
        with open(self.sortie / f"{id_}.sour", "wb") as out:
            out.write(len(dirs).to_bytes(4, "big"))
            out.write(dirs)
            out.write(len(meta).to_bytes(4, "big"))
            out.write(meta)
            for _, donnees in blocs:
                out.write(donnees)
        self.bundles.append({"id": id_, "assets": assets, "desktop": False, "web": True})
        return id_, assets

    def mod(self, nom, description, chemins):
        id_, _ = self.bundle(chemins)
        self.mods.append({"id": id_, "name": nom, "image": None, "description": description})

    def carte(self, ogz: str):
        base = ogz[:-4]
        chemins = [ogz] + [base + ext for ext in (".cfg", ".jpg", ".png", ".wpt") if (self.racine / (base + ext)).exists()]
        id_, assets = self.bundle(chemins)
        ogz_id = next(a[0] for a in assets if a[1] == ogz)
        cfg = (self.racine / (base + ".cfg")).read_bytes() if (self.racine / (base + ".cfg")).exists() else b""
        self.maps.append({
            "id": empreinte((self.racine / ogz).read_bytes() + cfg),
            "name": Path(base).name,
            "bundle": id_,
            "ogz": ogz_id,
            "assets": assets,
            "image": None,
            "description": "Carte de Game2Earn",
        })

    def index(self, prefixe=""):
        with open(self.sortie / f"{prefixe}.index.source", "wb") as f:
            cbor2.dump({
                "assets": self.assets,
                "textures": [],
                "refs": [],
                "bundles": self.bundles,
                "models": [],
                "maps": self.maps,
                "mods": self.mods,
            }, f)


def faire(racine: Path, sortie: Path):
    p = Paquets(racine, sortie)
    tous = sorted(str(f.relative_to(racine)) for f in racine.rglob("*") if f.is_file())
    cartes = [c for c in tous if c.startswith("packages/base/") and c.endswith(".ogz")]
    fichiers_cartes = {c[:-4] + ext for c in cartes for ext in (".ogz", ".cfg", ".jpg", ".png", ".wpt")}
    modeles = [c for c in tous if c.startswith("packages/models/")]
    base = [c for c in tous if c not in fichiers_cartes and c not in modeles]

    p.mod("base", "Tout ce que le jeu charge au démarrage (Game2Earn).", base)
    p.mod("fps", "Personnages, armes et objets (Game2Earn).", modeles or ["credits.md"])
    for c in cartes:
        p.carte(c)
    p.index()
    taille = sum(f.stat().st_size for f in sortie.glob("*.sour"))
    print(f"paquets : {len(p.bundles)} ({taille / 1e6:.1f} Mo), cartes : {[m['name'] for m in p.maps]}")


if __name__ == "__main__":
    faire(Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve())
