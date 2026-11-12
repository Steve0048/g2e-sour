"""Game2Earn : personnages, armes et objets du jeu, pris dans Red Eclipse (CC BY-SA 4.0) et adaptés au moteur Cube 2.

Red Eclipse vient du même moteur, plus récent : ses réglages de modèles se lisent presque tels quels. Ce fichier :
  - copie les modèles (maillages, animations, textures PNG) sous packages/models/g2e/ ;
  - réécrit leurs réglages pour notre moteur : noms d'animations de Cube 2 (« gun idle », « vwep shoot »...),
    commandes que notre moteur n'a pas retirées (couleur du joueur, niveaux de détail, matériaux...) ;
  - colore le personnage (neutre, bleu, rouge) : Red Eclipse le colore en direct, notre moteur a besoin d'une texture
    par couleur.
Les noms attendus par le moteur (fpsgame) : armes en main « g2e/hud/<arme> », armes portées « vwep/<arme> »,
objets « ammo/... », projectiles « projectiles/grenade » et « projectiles/rocket ».
"""
import re
import shutil
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

RE_ACTEURS = ("https://github.com/redeclipse/actors.git", "2fde7dc82db150add31da2bde7b3679ddc6667b4")
RE_ARMES = ("https://github.com/redeclipse/weapons.git", "be45e9342b846ee75e2c8bbb71f8b9bcb5f94213")

# arme de Cube 2 (fpsgame/game.h, guns[].file) -> arme de Red Eclipse
ARMES = {"fist": "jetsaw", "shotg": "shotgun", "chaing": "smg", "rocket": "rocket", "rifle": "rifle", "gl": "grenade",
         "pistol": "pistol"}
# objets ramassés -> arme de Red Eclipse dont le modèle « item » sert de munitions
MUNITIONS = {"shells": "shotgun", "bullets": "smg", "rockets": "rocket", "rrounds": "rifle", "grenades": "grenade",
             "cartridges": "pistol"}

# commandes de Red Eclipse que notre moteur n'a pas
IGNOREES = re.compile(r"^(mdlcolor|mdlmaterial|mdllodpixels|mdlgloss|mdlmixer|(md5|iqm|obj)(color|material|"
                      r"gloss|envmap|mixertex|hitzone))\b|^objpitch\b")


def depot(url, commit, dossier):
    """Un dépôt de Red Eclipse à une version fixée, sans les gros fichiers des sources (Blender)."""
    if not (dossier / ".git").exists():
        dossier.mkdir(parents=True, exist_ok=True)
        subprocess.run(["git", "init", "-q", str(dossier)], check=True)
        subprocess.run(["git", "-C", str(dossier), "remote", "add", "origin", url], check=True)
    subprocess.run(["git", "-C", str(dossier), "fetch", "-q", "--depth", "1", "origin", commit], check=True)
    subprocess.run(["git", "-C", str(dossier), "checkout", "-q", "FETCH_HEAD"], check=True)
    return dossier


def copier_dossier(src: Path, dest: Path, garder=lambda p: True):
    for f in src.rglob("*"):
        if f.is_file() and f.suffix.lower() in {".iqm", ".md5mesh", ".md5anim", ".png", ".jpg", ".obj", ".mtl"} \
                and garder(f):
            cible = dest / f.relative_to(src)
            cible.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(f, cible)


def reduire(png: Path, cote=512):
    """Textures en 512 pixels au plus : le jeu tourne aussi sur des téléphones modestes."""
    img = Image.open(png)
    if max(img.size) > cote:
        img.resize((cote, cote) if img.width == img.height else (cote, cote * img.height // img.width),
                   Image.LANCZOS).save(png, optimize=True)


def convertir(texte: str, dossier: str, anims: dict) -> str:
    """Réglages d'un modèle de Red Eclipse -> réglages pour notre moteur.
    dossier : dossier du modèle (sous packages/models) ; anims : nom Red Eclipse -> nom Cube 2 (les autres sont retirées).
    """
    lignes, fmt = [], None
    for brute in texte.splitlines():
        ligne = brute.strip()
        if not ligne or ligne.startswith("//") or IGNOREES.match(ligne):
            continue
        ligne = ligne.replace("<dds>", "")
        m = re.match(r"^(md5|iqm|obj)(\w+)\s*(.*)$", ligne)
        if m:
            fmt, cmd, reste = m.groups()
            if cmd == "anim":
                a = re.match(r'^"([^"]*)"\s+(.*)$', reste)
                nom = anims.get(a.group(1)) if a else None
                if not nom:
                    continue
                ligne = f'{fmt}anim "{nom}" {a.group(2)}'
            if cmd == "tag" and len(reste.split()) == 1:
                ligne = f"{fmt}tag {reste} {reste}"  # Red Eclipse : un seul nom = l'os et l'attache
        lignes.append(ligne)
    if fmt is None:
        raise SystemExit(f"{dossier} : format du modèle inconnu")
    return f'{fmt}dir "{dossier}"\n' + "\n".join(lignes) + "\n", fmt


def ecrire_cfg(racine: Path, nom: str, texte: str, fmt: str):
    f = racine / "packages/models" / nom / f"{fmt}.cfg"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(texte, encoding="utf-8")


# Mains vues par le joueur (Red Eclipse, actors/player/hwep.cfg) : par arme de Cube 2, (repos, tir, vitesse du tir)
MAINS = {
    "fist": ("hud_sword-idle.iqm", "hud_sword-attack1.iqm", 60),
    "shotg": ("hud_shotgun-idle.iqm", "hud_shotgun-shoot1.iqm", 25),
    "chaing": ("hud_smg-idle.iqm", "hud_smg-shoot1.iqm", 60),
    "rocket": ("hud_rocket-idle.iqm", "hud_rocket-idle.iqm", 1),
    "rifle": ("hud_rifle-idle.iqm", "hud_rifle-shoot.iqm", 60),
    "gl": ("hud_grenade-idle.iqm", "hud_grenade-shoot.iqm", 22),
    "pistol": ("hud_pistol-idle.iqm", "hud_pistol-shoot.iqm", 40),
}


def mains(cube: str) -> str:
    repos, tir, vitesse = MAINS[cube]
    return f"""// Game2Earn : mains de Red Eclipse (CC BY-SA 4.0) ; l'arme s'y attache (modèle « arme », fpsgame/render.cpp).
iqmdir "g2e/joueur"
iqmload "hud_hands.iqm"
iqmtag Weapon tag_weapon
iqmtag Weapon tag_muzzle
iqmskin * "gants.png" "hudhandsmask.png" 0.25 0.0
iqmbumpmap * "hudhandsnormal.png"
iqmpitch "" 1
iqmanim "gun idle" "{repos}" 5
iqmanim "gun shoot" "{tir}" {vitesse}
mdlscale 481.95
mdltrans -0.22 0.2 -0.22
"""
# Red Eclipse tourne ce modèle de 90° (mdlyaw 90) ; notre moteur le fait déjà (fpsgame/render.cpp, d->yaw+90).


def armes(racine: Path, re_armes: Path):
    for cube, re_nom in ARMES.items():
        src = re_armes / re_nom
        copier_dossier(src, racine / f"packages/models/g2e/armes/{re_nom}")
        hwep = (src / "hwep").glob("*.cfg").__next__().read_text()
        vwep = (src / "vwep").glob("*.cfg").__next__().read_text()
        # vue du joueur : les mains (et leurs variantes d'équipe), l'arme s'y attache
        for nom in (f"g2e/hud/{cube}", f"g2e/hud/{cube}/blue", f"g2e/hud/{cube}/red"):
            ecrire_cfg(racine, nom, mains(cube), "iqm")
        texte, fmt = convertir(hwep, f"g2e/armes/{re_nom}/hwep",
                               {re_nom: "gun idle", f"{re_nom} primary": "gun shoot"})
        ecrire_cfg(racine, f"g2e/hud/{cube}/arme", texte, fmt)
        # arme portée par les autres joueurs
        texte, fmt = convertir(vwep, f"g2e/armes/{re_nom}/vwep",
                               {re_nom: "vwep idle", f"{re_nom} primary": "vwep shoot"})
        ecrire_cfg(racine, f"vwep/{cube}", texte, fmt)
    # munitions : le modèle de l'arme, qui tourne au sol
    for cube, re_nom in MUNITIONS.items():
        item = (re_armes / re_nom / "item").glob("*.cfg").__next__().read_text()
        texte, fmt = convertir(item, f"g2e/armes/{re_nom}/item", {})
        ecrire_cfg(racine, f"ammo/{cube}", texte, fmt)
    # projectiles
    for cube, re_nom in (("grenade", "grenade"), ("rocket", "rocket")):
        proj = re_armes / re_nom / "proj"
        cfg = next(proj.glob("*.cfg"))
        texte, fmt = convertir(cfg.read_text(), f"g2e/armes/{re_nom}/proj", {})
        ecrire_cfg(racine, f"projectiles/{cube}", texte, fmt)
    for png in (racine / "packages/models/g2e/armes").rglob("*.png"):
        reduire(png)
    for f in ("readme.txt", "cc-by-sa.txt"):
        shutil.copyfile(re_armes / f, racine / "packages/models/g2e/armes" / f)


# Animations du personnage : nom de Cube 2 -> (fichier de Red Eclipse, vitesse)
CORPS = {
    "dying": ("dying.iqm", 21), "dead": ("dead.iqm", 0), "idle|edit|lag": ("idle.iqm", 10),
    "forward": ("runcycle0.iqm", 35), "backward": ("runbackward0.iqm", 35), "left": ("runstepleft0.iqm", 45),
    "right": ("runstepright0.iqm", 45), "jump": ("jump0_up.iqm", 50), "sink": ("sink.iqm", 20),
    "swim": ("swim.iqm", 20), "pain": ("pain.iqm", 0), "taunt": ("emote_wave.iqm", 24), "win": ("emote_clap.iqm", 24),
    "lose": ("emote_shrug.iqm", 24),
}
# haut du corps : tenir et tirer avec chaque arme (ordre de Cube 2 : fist, shotg, chaing, rocket, rifle, gl, pistol)
HAUT = {
    "hold 1": ("sword_idle.iqm", 24), "attack 1": ("sword_primary.iqm", 60),
    "hold 2": ("shotgun_idle.iqm", 1), "attack 2": ("sg_primary.iqm", 32),
    "hold 3": ("smg-pose.iqm", 1), "attack 3": ("smg-primary.iqm", 24),
    "hold 4": ("rocket_idle.iqm", 1), "attack 4": ("rocket_shoot.iqm", 20),
    "hold 5": ("rifle_idle.iqm", 1), "attack 5": ("rifle_primary.iqm", 20),
    "hold 6": ("grenade_idle.iqm", 1), "attack 6": ("grenade_primary.iqm", 15),
    "hold 7": ("gun_pose1.iqm", 1), "attack 7": ("gun_fire.iqm", 20),
}
COULEURS = {"": (230, 150, 40), "bleu": (60, 120, 255), "rouge": (235, 60, 50)}  # neutre : orange de Game2Earn


def colorer(diffuse: Path, mixer: Path, couleur, dest: Path):
    """Colore le personnage là où Red Eclipse met la couleur du joueur (canal vert de mixer.png)."""
    d = np.asarray(Image.open(diffuse).convert("RGB"), dtype=float) / 255
    m = np.asarray(Image.open(mixer).convert("RGBA").resize(Image.open(diffuse).size), dtype=float)[..., 1:2] / 255
    c = np.array(couleur, dtype=float) / 255
    teinte = d * (1 - m) + d * c * m
    gris = d * (1 - m) * 0.55 + teinte * m  # le reste en gris sombre (le blanc pur de Red Eclipse est trop clair)
    Image.fromarray((np.clip(gris, 0, 1) * 255).astype(np.uint8)).resize((512, 512), Image.LANCZOS).save(dest)


def personnages(racine: Path, re_acteurs: Path):
    src = re_acteurs / "player"
    dest = racine / "packages/models/g2e/joueur"
    dest.mkdir(parents=True, exist_ok=True)
    fichiers = {f for f, _ in CORPS.values()} | {f for f, _ in HAUT.values()} | {"hud_hands.iqm"} \
        | {f for repos, tir, _ in MAINS.values() for f in (repos, tir)}
    for f in fichiers:
        shutil.copyfile(src / f, dest / f)
    shutil.copyfile(src / "male/RE_Player_male.iqm", dest / "homme.iqm")
    shutil.copyfile(src / "female/RE_Player_female.iqm", dest / "femme.iqm")
    for f in ("mask.png", "norm.png", "hudhandsmask.png", "hudhandsnormal.png"):
        shutil.copyfile(src / f, dest / f)
        reduire(dest / f)
    colorer(src / "hudhandsdiffuse.png", src / "hudhandsmixer.png", COULEURS[""], dest / "gants.png")
    for nom, c in COULEURS.items():
        colorer(src / "diffuse.png", src / "mixer.png", c, dest / f"peau{('_' + nom) if nom else ''}.png")
    shutil.copyfile(src / "ragdoll.cfg", dest / "ragdoll.cfg")

    def anims(table):
        return "\n".join(f'iqmanim "{n}" "{f}"' + (f" {v}" if v else "") for n, (f, v) in table.items())

    for perso in ("homme", "femme"):
        commun = f"""// Game2Earn : personnage « {perso} » de Red Eclipse (CC BY-SA 4.0), adapté au moteur Cube 2.
iqmdir "g2e/joueur"
iqmload "{perso}.iqm"
exec "packages/models/g2e/joueur/ragdoll.cfg"

iqmtag hand.R tag_weapon 0.1 -0.9 0.1 -90 0 -90
iqmtag ribs tag_powerup 0 0.4 2
iqmtag ribs tag_shield 0 0.4 2

iqmpitch spine 0.4 0 -30 30
iqmpitch ribs 0.3 0 -30 30
iqmpitch head 0.5 0 -10 10

{anims(CORPS)}
iqmanimpart ribs
{anims({k: v for k, v in CORPS.items() if k not in ("forward", "backward", "left", "right", "jump")})}
{anims(HAUT)}

iqmbumpmap * "norm.png"
iqmspec * 100
mdlscale 95
mdlspec 60
"""
        (dest / f"{perso}.cfg").write_text(commun, encoding="utf-8")
        for nom in COULEURS:
            peau = f"peau{('_' + nom) if nom else ''}.png"
            modele = f"g2e/{perso}" + (f"/{nom}" if nom else "")
            ecrire_cfg(racine, modele, f'exec "packages/models/g2e/joueur/{perso}.cfg"\niqmskin * "{peau}" "mask.png" '
                                       f'0.25 0.0\n', "iqm")
    for f in ("readme.txt", "cc-by-sa.txt"):
        shutil.copyfile(re_acteurs / f, dest / f)


def modeles(racine: Path, cache: Path):
    re_armes = depot(*RE_ARMES, cache / "re-weapons")
    re_acteurs = depot(*RE_ACTEURS, cache / "re-actors")
    armes(racine, re_armes)
    personnages(racine, re_acteurs)
