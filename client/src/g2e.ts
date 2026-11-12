// Game2Earn : le jeu dans la plateforme (page game2earn/client/index.html, qui définit G2E).
//
// 1. Le moteur charge ses paquets ; on prévient la plateforme : « pret » (Jeux/README.md du dépôt g2e_official).
// 2. Au départ (« demarrer ») :
//    - sans salle ou à l'entraînement : une partie hors ligne contre des bots débutants (niveau 20 à 30 sur 101),
//      sur une carte tirée avec la graine ; les points de passage des bots sont créés depuis la carte (moteur) ;
//    - en défi : la page demande son accès au Worker g2e-sour (salle, jeton), attend que le serveur du match soit
//      prêt sur Edgegap, puis s'y connecte avec la clé de sa place (seul ce joueur entre à cette place).
// 3. Éditeur (?editeur=1, ouvert par le dashboard) : l'admin dessine une carte ; le dashboard demande
//    « exporter » et reçoit la carte (.ogz) pour la publier.
// Hors de la plateforme (essai en local), rien ne change : la page se comporte comme le client de Sour.

type Carte = { id: string; nom: string; admin?: boolean }
type Salle = { serveur: string; code: string; place: number; jeton: string; pause: boolean }
type Demarrer = { graine: number; son: boolean; niveau: number | null; langue: string; salle?: Salle }

declare const G2E: { integre: boolean; cartes: Carte[]; editeur: boolean } | undefined
declare const BananaBread: { execute: (s: string) => void }
declare const Module: any

const SOURCE_JEU = 'g2e-jeu'
const SOURCE_PLATEFORME = 'g2e-plateforme'

/** Les cartes du jeu (celles des paquets du jeu) ; les cartes de l'admin viennent de la fiche du jeu. */
const CARTES_DU_JEU = ['g2e_essai']

export const g2eActif = (): boolean => typeof G2E !== 'undefined'
export const g2eEditeur = (): boolean => g2eActif() && Boolean(G2E?.editeur)

let connecter: ((url: string) => void) | null = null
let pret = false
let depart: Demarrer | null = null
let lance = false
let horsLigne = false
let carteAttendue: string | null = null
let bots = 0

function envoyer(message: Record<string, unknown>, transfert: Transferable[] = []) {
  if (window.parent !== window) window.parent.postMessage({ source: SOURCE_JEU, ...message }, '*', transfert)
}

function message(texte: string) {
  const el = document.getElementById('g2e-message')
  if (el == null) return
  el.textContent = texte
  el.hidden = texte.length === 0
}

function executer(commande: string) {
  try {
    BananaBread.execute(commande)
  } catch (e) {
    console.error('Game2Earn : commande refusée', commande, e)
  }
}

/** Générateur déterministe (mulberry32, comme le SDK) : même graine, même carte et mêmes bots. */
function hasard(graine: number) {
  let a = graine >>> 0 || 1
  return () => {
    a = (a + 0x6d2b79f5) >>> 0
    let t = a
    t = Math.imul(t ^ (t >>> 15), t | 1)
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61)
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

/** Index.tsx donne sa fonction de connexion au serveur (le WebSocket ne s'ouvre qu'au départ d'un défi). */
export function g2eSurConnecteur(f: (url: string) => void) {
  connecter = f
}

/** Les menus du jeu, en français et réduits : Reprendre, Réglages (et l'édition pour l'admin). */
export function g2eMenus(): string {
  return `
    g2e_qualite = [
      if $g2e_qualite_basse [
        shadowmap 0; glare 0; waterreflect 0; waterrefract 0; caustics 0; grass 0; maxdynlights 0
      ] [
        shadowmap 1; glare 1; waterreflect 1; waterrefract 1; caustics 1; grass 1; maxdynlights 3
      ]
    ]
    newgui g2e_reglages [
      guilist [
        guitext (concatword "Sensibilité : " (div (*f $sensitivity 10) 10))
        guistrut 1
        guibutton " - " [sensitivity (max 1 (-f $sensitivity 1))]
        guibutton " + " [sensitivity (min 30 (+f $sensitivity 1))]
      ]
      guicheckbox "Inverser la souris (haut, bas)" invmouse
      guibar
      guitext "Volume du son"
      guislider soundvol
      guitext "Champ de vision"
      guislider fov
      guibar
      guicheckbox "Qualité réduite (plus fluide)" g2e_qualite_basse 1 0 [g2e_qualite]
      guicheckbox "Plein écran" fullscreen
      guibar
      guibutton "Retour" [cleargui 1]
    ] "Réglages"
    injectedmenu = [
      guibutton "Reprendre" [cleargui]
      guibutton "Réglages" [showgui g2e_reglages]
      if $editing [ guibutton "Édition de la carte" [showgui editing] ]
    ]
  `
}

if (typeof G2E !== 'undefined') {
  window.addEventListener('message', (e) => {
    if (e.source !== window.parent) return
    const m = e.data
    if (m == null || typeof m !== 'object') return
    if (m.source === SOURCE_PLATEFORME) {
      if (m.type === 'demarrer') surDemarrer(m as Demarrer)
      else if (m.type === 'son') regler(Boolean(m.actif))
      else if (m.type === 'arreter') arreter()
      else if (m.type === 'reinitialiser') reinitialiser()
    } else if (m.source === 'g2e-editeur' && g2eEditeur()) {
      surEditeur(m)
    }
  })
  // Le son ne joue qu'après un geste du joueur dans la page qui le joue.
  const reprendre = () => {
    const audio = (window as any).AL?.currentCtx?.audioCtx ?? Module?.SDL2?.audioContext
    if (audio != null && audio.state !== 'running') audio.resume().catch(() => {})
  }
  for (const type of ['pointerdown', 'keydown', 'touchstart']) window.addEventListener(type, reprendre, true)
}

/** Le moteur est prêt (paquets chargés, menus posés). */
export function g2eSurPret() {
  if (!g2eActif()) return
  pret = true
  executer(g2eMenus())
  if (/Android|iPhone|iPad|Mobile/i.test(navigator.userAgent)) executer('g2e_qualite_basse = 1; g2e_qualite')
  if (g2eEditeur()) {
    ouvrirEditeur()
    return
  }
  envoyer({ type: 'pret' })
  if (depart != null) lancer(depart)
}

/** Une carte vient d'être chargée par le moteur. */
export function g2eSurCarte(nom: string) {
  if (!g2eActif() || !horsLigne || nom !== carteAttendue) return
  // Entraînement : les bots arrivent sur la carte (les points de passage sont créés depuis la carte).
  const r = hasard((depart?.graine ?? 1) ^ 0x5eed)
  for (let i = 0; i < bots; i++) {
    const niveau = 20 + Math.floor(r() * 11)
    setTimeout(() => executer(`addbot ${niveau}`), 500 + i * 300)
  }
  message('')
}

function surDemarrer(d: Demarrer) {
  depart = d
  if (pret) lancer(d)
}

function lancer(d: Demarrer) {
  if (lance) return
  lance = true
  regler(d.son)
  if (d.salle == null) {
    entrainement(d.graine)
    return
  }
  rejoindre(d.salle)
}

function regler(actif: boolean) {
  executer(actif ? 'soundvol 255' : 'soundvol 0')
}

function cartes(): string[] {
  const admin = (G2E?.cartes ?? []).map((c) => c.id)
  const toutes = [...CARTES_DU_JEU, ...admin.filter((c) => !CARTES_DU_JEU.includes(c))]
  return toutes
}

function entrainement(graine: number) {
  horsLigne = true
  const liste = cartes()
  const r = hasard(graine)
  carteAttendue = liste[Math.floor(r() * liste.length)] ?? 'g2e_essai'
  bots = 3
  message('Entraînement : trois bots débutants arrivent.')
  executer(`mode 0; map ${carteAttendue}`)
}

async function rejoindre(salle: Salle) {
  message('Préparation du serveur du match…')
  const url = `${salle.serveur.replace(/\/+$/, '')}/salles/${encodeURIComponent(salle.code)}/acces?jeton=${encodeURIComponent(salle.jeton)}`
  for (let essai = 0; essai < 400; essai++) {
    try {
      const r = await fetch(url, { cache: 'no-store' })
      const a = await r.json()
      if (a.etat === 'entrainement') {
        entrainement(Number(a.graine ?? depart?.graine ?? 1))
        return
      }
      if (a.etat === 'termine') {
        message('Ce match est terminé.')
        return
      }
      if (a.etat === 'erreur') {
        message(a.message ?? "Le serveur du match ne répond pas.")
        return
      }
      if (a.etat === 'pret' && typeof a.ws === 'string' && connecter != null) {
        message(a.ville ? `Connexion au serveur du match (${a.ville})…` : 'Connexion au serveur du match…')
        if (typeof a.pseudo === 'string' && /^[A-Za-z0-9_]{1,15}$/.test(a.pseudo)) executer(`name ${a.pseudo}`)
        connecter(`${a.ws}${a.ws.includes('?') ? '&' : '?'}jeton=${encodeURIComponent(a.cle)}`)
        setTimeout(() => {
          executer('join g2e')
          message('')
        }, 800)
        return
      }
    } catch (e) {
      console.warn('Game2Earn : accès au match illisible', e)
    }
    await new Promise((f) => setTimeout(f, 3000))
  }
  message("Le serveur du match ne répond pas. Réessaie dans un instant.")
}

function arreter() {
  if (horsLigne) executer('disconnect')
  envoyer({ type: 'fin', score: 0 })
}

function reinitialiser() {
  executer('disconnect')
  lance = false
  horsLigne = false
  depart = null
}

// ---- Éditeur des cartes (dashboard) ----

function ouvrirEditeur() {
  const carte = new URLSearchParams(location.search).get('carte')
  if (carte != null && /^[a-z0-9_]{2,40}$/.test(carte)) executer(`map ${carte}`)
  else executer('newmap 10')
  setTimeout(() => executer('if (! $editing) [edittoggle]'), 1500)
  envoyer({ type: 'editeur-pret' })
}

function lireFichier(chemins: string[]): Uint8Array | null {
  for (const c of chemins) {
    try {
      const d = Module.FS.readFile(c) as Uint8Array
      if (d != null && d.length > 0) return d
    } catch (e) {
      // essai suivant
    }
  }
  return null
}

function surEditeur(m: { type?: string; nom?: string }) {
  if (m.type !== 'exporter' || typeof m.nom !== 'string' || !/^[a-z0-9_]{2,40}$/.test(m.nom)) return
  const nom = m.nom
  // L'éclairage est calculé, puis la carte enregistrée dans le système de fichiers du moteur.
  executer(`calclight; savemap ${nom}`)
  let essais = 0
  const lire = () => {
    const donnees = lireFichier([`/packages/base/${nom}.ogz`, `packages/base/${nom}.ogz`, `/${nom}.ogz`])
    if (donnees == null) {
      if (++essais < 40) setTimeout(lire, 500)
      else envoyer({ type: 'carte-erreur', nom, message: "La carte n'a pas pu être enregistrée." })
      return
    }
    const copie = donnees.slice().buffer
    envoyer({ type: 'carte', nom, ogz: copie }, [copie])
  }
  setTimeout(lire, 1000)
}
