// Game2Earn : la manette (API Gamepad). Stick gauche : se déplacer ; stick droit : viser ; gâchette droite : tirer ;
// gâchette gauche : zoom ; A : sauter ; LB et RB : arme précédente, suivante ; Start : menu.
declare const BananaBread: { execute: (s: string) => void; mousemove: (dx: number, dy: number) => void }
declare const Module: any

const ZONE_MORTE = 0.2
const VITESSE_VISEE = 18

type Etat = Record<string, boolean>

export function demarrerManette() {
  if (typeof navigator.getGamepads !== 'function') return
  let avant: Etat = {}

  const executer = (c: string) => {
    try {
      BananaBread.execute(c)
    } catch (e) {
      // le moteur n'est pas encore prêt
    }
  }

  const changer = (nom: string, actif: boolean, debut: string, fin?: string) => {
    if (Boolean(avant[nom]) === actif) return
    avant[nom] = actif
    if (actif) executer(debut)
    else if (fin != null) executer(fin)
  }

  const boucle = () => {
    window.requestAnimationFrame(boucle)
    if (!Module?.running) return
    const manette = Array.from(navigator.getGamepads()).find((g) => g != null && g.connected)
    if (manette == null) return
    const [lx = 0, ly = 0, rx = 0, ry = 0] = manette.axes
    const bouton = (i: number) => Boolean(manette.buttons[i]?.pressed)

    changer('avant', ly < -0.4, '_forward 1', '_forward 0')
    changer('arriere', ly > 0.4, '_backward 1', '_backward 0')
    changer('gauche', lx < -0.4, '_left 1', '_left 0')
    changer('droite', lx > 0.4, '_right 1', '_right 0')

    const vx = Math.abs(rx) > ZONE_MORTE ? rx : 0
    const vy = Math.abs(ry) > ZONE_MORTE ? ry : 0
    if (vx !== 0 || vy !== 0) {
      // courbe douce : précis près du centre, rapide au bord
      BananaBread.mousemove(Math.sign(vx) * vx * vx * VITESSE_VISEE, Math.sign(vy) * vy * vy * VITESSE_VISEE)
    }

    changer('tir', bouton(7), '_attack 1', '_attack 0')
    changer('saut', bouton(0), '_jump 1', '_jump 0')
    changer('zoom', bouton(6), 'zoom 1', 'zoom -1')
    changer('precedente', bouton(4), 'nextweapon -1')
    changer('suivante', bouton(5), 'nextweapon 1')
    changer('menu', bouton(9), 'togglemainmenu')
  }
  window.requestAnimationFrame(boucle)
}
