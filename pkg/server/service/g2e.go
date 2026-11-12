package service

// Game2Earn : un match de défi. Le serveur est lancé pour un seul match (sur Edgegap), réglé par la variable
// d'environnement G2E_MATCH (JSON, posée par le Worker g2e-sour de la plateforme) :
//
//	{"places": [{"jeton": "…", "nom": "Ama", "equipe": "good"}, …], "mode": "ffa", "carte": "g2e_essai",
//	 "duree": 600, "attente": 600, "retour": 90, "resultat": "https://…"}
//
//   - une clé par place : seul le joueur qui a la clé de sa place se connecte (?jeton= sur /ws/) ;
//   - nom et équipe imposés, rien ne se change en jeu (pkg/gameserver/g2e.go) ;
//   - échauffement jusqu'à ce que tout le monde soit là, puis le match commence ; après « attente » secondes, les
//     absents perdent leur place ;
//   - un joueur parti a « retour » secondes pour revenir, sinon il abandonne ; s'il ne reste qu'un camp, il gagne ;
//   - à la fin du temps (Intermission), le résultat est envoyé à « resultat » (le Worker g2e-sour).

import (
	"bytes"
	"context"
	"crypto/subtle"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/cfoust/sour/pkg/game/constants"
	"github.com/cfoust/sour/pkg/gameserver"
	"github.com/cfoust/sour/pkg/gameserver/protocol/gamemode"
	"github.com/cfoust/sour/pkg/server/ingress"
	"github.com/cfoust/sour/pkg/server/servers"
	opt "github.com/repeale/fp-go/option"

	"github.com/rs/zerolog/log"
)

type G2EPlace struct {
	Jeton  string `json:"jeton"`
	Nom    string `json:"nom"`
	Equipe string `json:"equipe"`

	user    *User
	present bool
	forfait bool
	depart  *time.Timer
}

type G2EMatch struct {
	Places   []*G2EPlace `json:"places"`
	Mode     string      `json:"mode"`
	Carte    string      `json:"carte"`
	Duree    int         `json:"duree"`
	Attente  int         `json:"attente"`
	Retour   int         `json:"retour"`
	Resultat string      `json:"resultat"`

	mutex   sync.Mutex
	mode    int32
	serveur *servers.GameServer
	lance   bool
	fini    bool
}

// Ce que le Worker reçoit à la fin.
type G2ERapport struct {
	Raison  string            `json:"raison"` // « temps » ou « abandon »
	Mode    string            `json:"mode"`
	Carte   string            `json:"carte"`
	Places  []G2ERapportLigne `json:"places"`
	Equipes map[string]int32  `json:"equipes"`
}

type G2ERapportLigne struct {
	Place   int    `json:"place"`
	Frags   int32  `json:"frags"`
	Morts   int32  `json:"morts"`
	Equipe  string `json:"equipe"`
	Present bool   `json:"present"`
	Forfait bool   `json:"forfait"`
}

// Lit G2E_MATCH ; nil hors d'un match Game2Earn.
func LireG2EMatch() (*G2EMatch, error) {
	brut := os.Getenv("G2E_MATCH")
	if brut == "" {
		return nil, nil
	}
	var m G2EMatch
	if err := json.Unmarshal([]byte(brut), &m); err != nil {
		return nil, fmt.Errorf("G2E_MATCH illisible : %w", err)
	}
	if len(m.Places) < 1 || len(m.Places) > 8 {
		return nil, fmt.Errorf("G2E_MATCH : de 1 à 8 places")
	}
	for _, p := range m.Places {
		if len(p.Jeton) < 16 || p.Nom == "" {
			return nil, fmt.Errorf("G2E_MATCH : chaque place a une clé (16 caractères au moins) et un nom")
		}
	}
	mode := constants.GetModeNumber(m.Mode)
	if opt.IsNone(mode) || !gamemode.Valid(gamemode.ID(mode.Value)) || gamemode.ID(mode.Value) == gamemode.CoopEdit {
		return nil, fmt.Errorf("G2E_MATCH : mode inconnu %q", m.Mode)
	}
	m.mode = int32(mode.Value)
	if m.Duree <= 0 {
		m.Duree = 600
	}
	if m.Attente <= 0 {
		m.Attente = 600
	}
	if m.Retour <= 0 {
		m.Retour = 90
	}
	return &m, nil
}

func (m *G2EMatch) place(jeton string) *G2EPlace {
	for _, p := range m.Places {
		if len(p.Jeton) == len(jeton) && subtle.ConstantTimeCompare([]byte(p.Jeton), []byte(jeton)) == 1 {
			return p
		}
	}
	return nil
}

func (m *G2EMatch) placeDe(session uint32) (int, *G2EPlace) {
	for i, p := range m.Places {
		if p.user != nil && uint32(p.user.Id) == session {
			return i, p
		}
	}
	return -1, nil
}

func (m *G2EMatch) camp(i int) string {
	if m.Places[i].Equipe != "" {
		return m.Places[i].Equipe
	}
	return fmt.Sprintf("place-%d", i)
}

// Les camps encore en jeu (au moins un joueur sans abandon).
func (m *G2EMatch) campsEnJeu(presentsSeulement bool) map[string]bool {
	camps := map[string]bool{}
	for i, p := range m.Places {
		if p.forfait || (presentsSeulement && !p.present) {
			continue
		}
		camps[m.camp(i)] = true
	}
	return camps
}

// Démarre le serveur du match (échauffement) ; appelé au lancement du cluster.
func (c *Cluster) DemarrerG2E(ctx context.Context, m *G2EMatch) error {
	gs, err := c.servers.NewServer(ctx, "", true)
	if err != nil {
		return err
	}
	gs.Alias = "g2e"
	gs.KeepTeams = true
	gs.Config.MatchLength = m.Duree
	gs.G2E = &gameserver.G2EHooks{
		Place: func(session uint32) (string, string, bool) {
			m.mutex.Lock()
			defer m.mutex.Unlock()
			_, p := m.placeDe(session)
			if p == nil {
				return "", "", false
			}
			return p.Nom, p.Equipe, true
		},
	}
	m.serveur = gs
	c.g2e = m

	ingress.ValiderJeton = func(jeton string) bool {
		m.mutex.Lock()
		defer m.mutex.Unlock()
		p := m.place(jeton)
		return p != nil && !p.forfait && !m.fini
	}

	gs.ChangeMap(m.mode, m.Carte)
	log.Info().Msgf("Game2Earn : match %s sur %s, %d places", m.Mode, m.Carte, len(m.Places))

	time.AfterFunc(time.Duration(m.Attente)*time.Second, func() { c.g2eFinAttente() })
	return nil
}

// Un joueur entre (commande « join » du client) : toujours dans le match, à sa place.
func (c *Cluster) g2eRejoindre(user *User) error {
	m := c.g2e
	client, ok := user.Connection.(*ingress.WSClient)
	if !ok {
		return fmt.Errorf("connexion refusée")
	}
	m.mutex.Lock()
	p := m.place(client.Jeton)
	if p == nil || p.forfait || m.fini {
		m.mutex.Unlock()
		return fmt.Errorf("place inconnue")
	}
	ancien := p.user
	p.user = user
	if p.depart != nil {
		p.depart.Stop()
		p.depart = nil
	}
	m.mutex.Unlock()

	// La même place depuis un autre onglet ou après une coupure : l'ancienne connexion part.
	if ancien != nil && ancien != user {
		ancien.Connection.Disconnect(0, "connexion depuis un autre appareil")
	}

	connected, err := user.Connect(m.serveur)
	if err != nil {
		return err
	}
	go func() {
		if ok := <-connected; !ok {
			return
		}
		m.mutex.Lock()
		p.present = true
		tous := true
		for _, q := range m.Places {
			if !q.present && !q.forfait {
				tous = false
			}
		}
		lancer := tous && !m.lance
		m.mutex.Unlock()
		if lancer {
			c.g2eLancer()
		}
	}()
	return nil
}

// Le match commence (carte relancée, scores à zéro, horloge du match).
func (c *Cluster) g2eLancer() {
	m := c.g2e
	m.mutex.Lock()
	if m.lance || m.fini {
		m.mutex.Unlock()
		return
	}
	m.lance = true
	m.mutex.Unlock()
	m.serveur.G2E.Fin = func(r gameserver.G2EResultat) { c.g2eFinir("temps", &r) }
	m.serveur.ChangeMap(m.mode, m.Carte)
	m.serveur.Message("Le match commence !")
	log.Info().Msg("Game2Earn : le match commence")
}

// Fin de l'attente : les absents perdent leur place ; le match commence s'il reste au moins deux camps.
func (c *Cluster) g2eFinAttente() {
	m := c.g2e
	m.mutex.Lock()
	if m.lance || m.fini {
		m.mutex.Unlock()
		return
	}
	for _, p := range m.Places {
		if !p.present {
			p.forfait = true
		}
	}
	camps := len(m.campsEnJeu(true))
	m.mutex.Unlock()
	if camps >= 2 {
		c.g2eLancer()
		return
	}
	c.g2eFinir("abandon", nil)
}

// Un joueur quitte le serveur (onglet fermé, réseau coupé) : il a « retour » secondes pour revenir.
func (c *Cluster) g2eDepart(user *User) {
	m := c.g2e
	if m == nil {
		return
	}
	m.mutex.Lock()
	defer m.mutex.Unlock()
	for _, p := range m.Places {
		if p.user != user {
			continue
		}
		p.user = nil
		if !m.lance || m.fini {
			return
		}
		place := p
		p.depart = time.AfterFunc(time.Duration(m.Retour)*time.Second, func() {
			m.mutex.Lock()
			if place.user != nil || m.fini {
				m.mutex.Unlock()
				return
			}
			place.forfait = true
			reste := len(m.campsEnJeu(false))
			m.mutex.Unlock()
			log.Info().Msgf("Game2Earn : %s abandonne (absent)", place.Nom)
			if reste <= 1 {
				c.g2eFinir("abandon", nil)
			}
		})
	}
}

// Le résultat part au Worker (plusieurs essais), une seule fois.
func (c *Cluster) g2eFinir(raison string, r *gameserver.G2EResultat) {
	m := c.g2e
	m.mutex.Lock()
	if m.fini {
		m.mutex.Unlock()
		return
	}
	m.fini = true
	rapport := G2ERapport{Raison: raison, Mode: m.Mode, Carte: m.Carte, Equipes: map[string]int32{}}
	for i, p := range m.Places {
		ligne := G2ERapportLigne{Place: i, Equipe: p.Equipe, Present: p.user != nil, Forfait: p.forfait}
		if r != nil && p.user != nil {
			for _, j := range r.Joueurs {
				if j.Session == uint32(p.user.Id) {
					ligne.Frags, ligne.Morts = j.Frags, j.Morts
					if j.Equipe != "" {
						ligne.Equipe = j.Equipe
					}
				}
			}
		}
		rapport.Places = append(rapport.Places, ligne)
	}
	if r != nil {
		rapport.Equipes = r.Equipes
	}
	url := m.Resultat
	m.mutex.Unlock()

	m.serveur.Message("Fin du match : le résultat part sur Game2Earn.")
	log.Info().Msgf("Game2Earn : fin du match (%s)", raison)
	if url == "" {
		return
	}
	corps, _ := json.Marshal(rapport)
	go func() {
		for essai := 0; essai < 8; essai++ {
			ctx, cancel := context.WithTimeout(context.Background(), 15*time.Second)
			req, _ := http.NewRequestWithContext(ctx, http.MethodPost, url, bytes.NewReader(corps))
			req.Header.Set("content-type", "application/json")
			rep, err := http.DefaultClient.Do(req)
			cancel()
			if err == nil {
				rep.Body.Close()
				if rep.StatusCode < 300 {
					log.Info().Msg("Game2Earn : résultat envoyé")
					return
				}
				err = fmt.Errorf("statut %d", rep.StatusCode)
			}
			log.Warn().Err(err).Msg("Game2Earn : résultat non envoyé, nouvel essai")
			time.Sleep(time.Duration(5*(essai+1)) * time.Second)
		}
	}()
}
