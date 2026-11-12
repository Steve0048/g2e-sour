"""Game2Earn : assemble les fichiers du jeu (le dossier « racine », comme l'installation d'un jeu Cube 2) sans aucun
contenu non commercial.

    python3 -I fabriquer.py <racine> [--cache <dossier>]

Provenance de chaque fichier (détail des licences : credits.md) :
  - réglages du moteur (data/*.cfg) : Sauerbraten r6481, licence zlib ; menus de Sour (MIT) ; nos propres réglages
    (sons, textures des cartes, objets des cartes) ;
  - images de l'interface, icônes, effets, ciel, eau : dessinées par images.py (à nous) ;
  - textures des cartes : packs libres de Sauerbraten (trak5 MIT, cloward libre, drakker domaine public, tomek CC BY) ;
  - police : DejaVu (licence Bitstream Vera) ;
  - sons, personnages, armes : Red Eclipse (CC BY-SA 4.0), adaptés par sons.py et modeles.py.
Les sources sont téléchargées à des versions fixées (SAUER, RE_SONS) et gardées dans le cache.
"""
import argparse
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import modeles  # noqa: E402
import objets  # noqa: E402
import sons  # noqa: E402

DEPOT = ICI.parent.parent  # le dépôt g2e-sour
SAUER = "https://svn.code.sf.net/p/sauerbraten/code/!svn/bc/6481/"
RE_SONS = ("https://github.com/redeclipse/sounds.git", "3355267a26960b44777d1fb884777bde223ac526")

# Réglages du moteur repris tels quels (licence zlib)
CFG_SAUER = ["stdlib.cfg", "defaults.cfg", "font.cfg", "game_fps.cfg", "glsl.cfg", "keymap.cfg", "stdedit.cfg",
             "blendbrush.cfg", "heightmap.cfg"]
# Packs libres de Sauerbraten : dossier -> fichier de licence à garder à côté
PACKS = {"trak5": "readme.txt", "cloward": "readme.txt", "drakker": "license.txt", "tomek": "license.txt"}
POLICE = ["default.cfg", "default0.png", "default1.png", "default2.png", "default.txt"]


def telecharger(url, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and dest.stat().st_size > 0:
        return dest
    for essai in range(4):
        try:
            with urllib.request.urlopen(url, timeout=120) as r:
                dest.write_bytes(r.read())
            return dest
        except Exception as e:  # réseau capricieux : on réessaie
            if essai == 3:
                raise SystemExit(f"téléchargement impossible : {url} ({e})")


def lister_svn(chemin):
    import re
    with urllib.request.urlopen(SAUER + chemin, timeout=120) as r:
        html = r.read().decode("utf-8", "replace")
    return [x for x in re.findall(r'href="([^"]+)"', html) if x != "../" and not x.startswith("http")]


def sauer(chemin, cache):
    return telecharger(SAUER + chemin, cache / "sauer" / chemin)


def sons_re(cache):
    dossier = cache / "re-sounds"
    if not (dossier / ".git").exists():
        dossier.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(dossier)], check=True)
        subprocess.run(["git", "-C", str(dossier), "remote", "add", "origin", RE_SONS[0]], check=True)
    subprocess.run(["git", "-C", str(dossier), "fetch", "-q", "--depth", "1", "origin", RE_SONS[1]], check=True)
    subprocess.run(["git", "-C", str(dossier), "checkout", "-q", "FETCH_HEAD"], check=True)
    return dossier


def ecrire(racine, chemin, texte):
    f = racine / chemin
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(texte, encoding="utf-8")


def copier(src, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)


def textures_des_cartes():
    """data/default_map_settings.cfg : les textures proposées dans l'éditeur, uniquement les nôtres et les libres."""
    return """// Game2Earn : réglages de chaque carte (généré par game2earn/contenus/fabriquer.py).
// Seules les textures libres (usage commercial permis) sont proposées. Ne retirer aucune ligne : les cartes
// enregistrent le numéro des textures, ajouter les nouvelles à la fin.

exec "data/default_map_models.cfg"

if (strcmp $skybox "") [
    skybox "skyboxes/g2e/ciel"
]

materialreset
texture water "textures/eau.jpg"
texture 1 "textures/waterfall.jpg"
texture 1 "textures/watern.jpg"
texture 1 "textures/waterdudv.jpg"
texture 1 "textures/waterfalln.jpg"
texture 1 "textures/waterfalldudv.jpg"

texture lava "textures/lave.jpg" 0 0 0 2
texture 1 "textures/lave.jpg" 0 0 0 2

texturereset
    setshader stdworld
        texture 0 "textures/sky.png"
        texture 0 "textures/default.png"

    exec "packages/trak5/package.cfg"

    setshader bumpworld
        texture 0 "cloward/bricksDiffuse.jpg"
        texture n "cloward/bricksNormal.jpg"
        texture 0 "cloward/cobblestonesDiffuse.jpg"
        texture n "cloward/cobblestonesNormal.jpg"
        texture 0 "cloward/metalSheetDiffuse.jpg"
        texture n "cloward/metalSheetNormal.jpg"
        texture 0 "cloward/stonewallDiffuse.jpg"
        texture n "cloward/stonewallNormal.jpg"

    exec "packages/tomek/package.cfg"

    setshader stdworld
        texture 0 "drakker/no_diving.jpg"

    setshader stdworld
"""


def objets_des_cartes():
    """data/default_map_models.cfg : les objets décoratifs des cartes (aucun pour l'instant : ceux de Sauerbraten sont
    non commerciaux ; les nôtres viendront avec l'éditeur des cartes)."""
    return "// Game2Earn : objets décoratifs des cartes (aucun pour l'instant).\nmapmodelreset\n"


def menus():
    """data/menus.cfg : les menus de Sour, sans les icônes des personnages de Sauerbraten."""
    texte = (DEPOT / "assets/sour/data/menus.cfg").read_text(encoding="utf-8", errors="replace")
    return texte


def fabriquer(racine, cache):
    if racine.exists():
        shutil.rmtree(racine)
    racine.mkdir(parents=True)

    # 1. images (à nous)
    subprocess.run([sys.executable, "-I", str(ICI / "images.py"), str(racine)], check=True)

    # 2. réglages du moteur
    for nom in CFG_SAUER:
        copier(sauer(f"data/{nom}", cache), racine / "data" / nom)
    # pas de musique (celles de Sauerbraten ne sont pas libres ; celles de Red Eclipse pèsent plusieurs Mo chacune)
    jeu = racine / "data/game_fps.cfg"
    texte = jeu.read_text(encoding="latin-1")
    ancien = 'playsong = [ music (concatword "fanatic/" (+ 1 (rnd 8)) ".ogg") playsong ]'
    if ancien not in texte:
        raise SystemExit("game_fps.cfg : ligne de la musique introuvable")
    jeu.write_text(texte.replace(ancien, "playsong = []"), encoding="latin-1")
    ecrire(racine, "data/menus.cfg", menus())
    ecrire(racine, "data/sounds.cfg", sons.cfg())
    ecrire(racine, "data/default_map_settings.cfg", textures_des_cartes())
    ecrire(racine, "data/default_map_models.cfg", objets_des_cartes())
    copier(sauer("packages/hud/digit_font.cfg", cache), racine / "packages/hud/digit_font.cfg")

    # 3. police et textures libres
    for nom in POLICE:
        copier(sauer(f"packages/fonts/{nom}", cache), racine / "packages/fonts" / nom)
    for pack in PACKS:
        for nom in lister_svn(f"packages/{pack}/"):
            if nom.endswith("/"):
                continue
            copier(sauer(f"packages/{pack}/{nom}", cache), racine / "packages" / pack / nom)

    # 4. sons de Red Eclipse
    re_sons = sons_re(cache)
    for f in sons.fichiers():
        copier(re_sons / f"{f}.ogg", racine / f"packages/sounds/re/{f}.ogg")
    copier(re_sons / "readme.txt", racine / "packages/sounds/re/readme.txt")
    copier(re_sons / "cc-by-sa.txt", racine / "packages/sounds/re/cc-by-sa.txt")

    # 5. personnages, armes, objets (Red Eclipse, adaptés)
    modeles.modeles(racine, cache)
    objets.objets(racine)

    # 6. cartes (cartes/ : faites dans l'éditeur ou par carte_essai.py, éclairage calculé)
    for carte in sorted((ICI / "cartes").glob("*")):
        copier(carte, racine / "packages/base" / carte.name)

    # 7. crédits
    copier(ICI / "credits.md", racine / "credits.md")

    n = sum(1 for f in racine.rglob("*") if f.is_file())
    taille = sum(f.stat().st_size for f in racine.rglob("*") if f.is_file())
    print(f"racine : {n} fichiers, {taille / 1e6:.1f} Mo")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("racine", type=Path)
    p.add_argument("--cache", type=Path, default=Path("cache"))
    a = p.parse_args()
    fabriquer(a.racine.resolve(), a.cache.resolve())
