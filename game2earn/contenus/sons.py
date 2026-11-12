"""Game2Earn : les sons du jeu, pris dans Red Eclipse (CC BY-SA 4.0, voir credits).

L'ordre des sons est imposé par le moteur (fpsgame/game.h, S_JUMP...S_FLAGFAIL) : chaque ligne de SONS est un son du
jeu, avec son volume (0 = normal) et les fichiers de Red Eclipse (le premier, puis les variantes tirées au hasard).
Les chemins sont relatifs au dépôt redeclipse/sounds, sans « .ogg » ; ils sont copiés sous packages/sounds/re/.
"""

SONS = [
    ("S_JUMP", 0, ["player/jump", "player/jump2", "player/jump3"]),
    ("S_LAND", 0, ["player/land", "player/land2", "player/land3"]),
    ("S_RIFLE", 80, ["weapons/rifle/primary", "weapons/rifle/primary2", "weapons/rifle/primary3"]),
    ("S_PUNCH1", 0, ["weapons/sword/primary", "weapons/sword/primary2"]),
    ("S_SG", 110, ["weapons/shotgun/primary", "weapons/shotgun/primary2", "weapons/shotgun/primary3"]),
    ("S_CG", 70, ["weapons/smg/primary", "weapons/smg/primary2", "weapons/smg/primary3"]),
    ("S_RLFIRE", 0, ["weapons/rocket/primary", "weapons/rocket/primary2", "weapons/rocket/primary3"]),
    ("S_RLHIT", 200, ["weapons/explode", "weapons/explode2", "weapons/explode3"]),
    ("S_WEAPLOAD", 0, ["weapons/reload"]),
    ("S_ITEMAMMO", 0, ["sfx/catch"]),
    ("S_ITEMHEALTH", 0, ["sfx/regen_boost"]),
    ("S_ITEMARMOUR", 0, ["sfx/itemuse"]),
    ("S_ITEMPUP", 0, ["sfx/openprize"]),
    ("S_ITEMSPAWN", 0, ["sfx/itemspawn"]),
    ("S_TELEPORT", 255, ["weapons/plasma/transit"]),
    ("S_NOAMMO", 0, ["weapons/tink"]),
    ("S_PUPOUT", 0, ["sfx/regen_decay"]),
    ("S_PAIN1", 0, ["player/pain"]),
    ("S_PAIN2", 0, ["player/pain2"]),
    ("S_PAIN3", 0, ["player/pain3"]),
    ("S_PAIN4", 0, ["player/pain4"]),
    ("S_PAIN5", 0, ["player/pain5"]),
    ("S_PAIN6", 0, ["player/pain6"]),
    ("S_DIE1", 0, ["player/death", "player/death3", "player/death5"]),
    ("S_DIE2", 0, ["player/death2", "player/death4"]),
    ("S_FLAUNCH", 0, ["weapons/grenade/primary"]),
    ("S_FEXPLODE", 200, ["weapons/smallblast", "weapons/smallblast2", "weapons/smallblast3"]),
    ("S_SPLASH1", 0, ["sfx/splashin", "sfx/splashin2", "sfx/splashin3"]),
    ("S_SPLASH2", 0, ["sfx/splashout", "sfx/splashout2", "sfx/splashout3"]),
    ("S_GRUNT1", 0, ["player/impulse"]),
    ("S_GRUNT2", 0, ["player/impulse2"]),
    ("S_RUMBLE", 0, ["weapons/bigblast"]),
    # sons des monstres du mode solo (non utilisé par Game2Earn) : des sons neutres
    ("S_PAINO", 0, ["sfx/damage"]),
    ("S_PAINR", 0, ["sfx/damage2"]),
    ("S_DEATHR", 0, ["sfx/debris"]),
    ("S_PAINE", 0, ["sfx/damage3"]),
    ("S_DEATHE", 0, ["sfx/debris2"]),
    ("S_PAINS", 0, ["sfx/damage4"]),
    ("S_DEATHS", 0, ["sfx/debris3"]),
    ("S_PAINB", 0, ["sfx/damage5"]),
    ("S_DEATHB", 0, ["sfx/debris"]),
    ("S_PAINP", 0, ["sfx/damage6"]),
    ("S_PIGGR2", 0, ["sfx/damage7"]),
    ("S_PAINH", 0, ["sfx/damage8"]),
    ("S_DEATHH", 0, ["sfx/debris2"]),
    ("S_PAIND", 0, ["sfx/damage"]),
    ("S_DEATHD", 0, ["sfx/debris3"]),
    ("S_PIGR1", 0, ["sfx/damage2"]),
    ("S_ICEBALL", 0, ["weapons/plasma/primary"]),
    ("S_SLIMEBALL", 0, ["weapons/corroder/primary"]),
    ("S_JUMPPAD", 255, ["player/impulse_action"]),
    ("S_PISTOL", 80, ["weapons/pistol/primary", "weapons/pistol/primary2", "weapons/pistol/primary3"]),
    # annonces (voix de Red Eclipse)
    ("S_V_BASECAP", 150, ["announcer/female/pointtaken"]),
    ("S_V_BASELOST", 150, ["announcer/female/pointlost"]),
    ("S_V_FIGHT", 150, ["announcer/female/fight"]),
    ("S_V_BOOST", 150, ["sfx/regen_boost"]),
    ("S_V_BOOST10", 150, ["announcer/female/attention"]),
    ("S_V_QUAD", 150, ["sfx/openprize"]),
    ("S_V_QUAD10", 150, ["announcer/female/attention"]),
    ("S_V_RESPAWNPOINT", 150, ["announcer/female/checkpoint"]),
    ("S_FLAGPICKUP", 0, ["interface/affinity_take"]),
    ("S_FLAGDROP", 0, ["interface/affinity_drop"]),
    ("S_FLAGRETURN", 0, ["interface/affinity_hold"]),
    ("S_FLAGSCORE", 0, ["interface/affinity_deliver"]),
    ("S_FLAGRESET", 0, ["interface/affinity_hold"]),
    ("S_BURN", 0, ["sfx/burning"]),
    ("S_CHAINSAW_ATTACK", 150, ["weapons/sword/secondary"]),
    ("S_CHAINSAW_IDLE", 230, ["weapons/sword/power"]),
    ("S_HIT", 60, ["sfx/damage_tick"]),
    ("S_FLAGFAIL", 200, ["sfx/error"]),
]


def fichiers():
    return sorted({f for _, _, liste in SONS for f in liste})


def cfg():
    lignes = [
        "// Game2Earn : sons de Red Eclipse (CC BY-SA 4.0), généré par game2earn/contenus/sons.py.",
        "// L'ordre est imposé par le moteur (fpsgame/game.h) : ne pas le changer.",
        "",
    ]
    for nom, volume, liste in SONS:
        v = f" {volume}" if volume else ""
        lignes.append(f'registersound "re/{liste[0]}"{v} // {nom}')
        for alt in liste[1:]:
            lignes.append(f'altsound "re/{alt}"{v}')
    return "\n".join(lignes) + "\n"
