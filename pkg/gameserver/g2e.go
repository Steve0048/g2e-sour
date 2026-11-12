package gameserver

// Game2Earn : un match à places réservées. Le serveur du match (pkg/server/service/g2e.go) donne à chaque
// joueur son nom et son équipe, reçoit le résultat à la fin du temps (Intermission) et vérifie les tirs
// (dans Cube 2, le joueur annonce lui-même ses tirs réussis).

import (
	"time"

	"github.com/cfoust/sour/pkg/gameserver/game"
	"github.com/cfoust/sour/pkg/gameserver/geom"
	"github.com/cfoust/sour/pkg/gameserver/protocol/weapon"
)

// Une ligne du résultat : un joueur présent à la fin.
type G2ELigne struct {
	Session uint32
	Frags   int32
	Morts   int32
	Equipe  string
}

type G2EResultat struct {
	Joueurs []G2ELigne
	// Le score de chaque équipe (drapeaux en capture du drapeau, sinon éliminations).
	Equipes map[string]int32
}

type G2EHooks struct {
	// Le nom et l'équipe imposés à une session (ok : la session a une place).
	Place func(session uint32) (nom string, equipe string, ok bool)
	// Appelé à la fin du temps d'un match lancé ; sans lui (échauffement), la carte recommence.
	Fin func(r G2EResultat)
}

// Les projectiles en vol d'un joueur (roquettes, grenades) : une explosion n'est acceptée que pour un tir réel.
type projectile struct {
	arme weapon.ID
	tire time.Time
}

const (
	// Marge pour la gigue du réseau : des tirs peuvent arriver un peu groupés.
	margeCadence = 250 * time.Millisecond
	// Distance au plus entre le joueur et le départ de son tir.
	margeDepart = 24.0
	// Distance au plus entre une cible touchée et la ligne de tir (taille du joueur et retard du réseau).
	margeLigne = 48.0
	// Durée de vie au plus d'un projectile.
	vieProjectile = 8 * time.Second
)

// Le résultat du match, à la fin du temps.
func (s *Server) g2eResultat() G2EResultat {
	r := G2EResultat{Equipes: map[string]int32{}}
	s.Clients.ForEach(func(c *Client) {
		if !c.Joined {
			return
		}
		equipe := ""
		if c.Team != nil && c.Team != game.NoTeam {
			equipe = c.Team.Name
		}
		r.Joueurs = append(r.Joueurs, G2ELigne{Session: c.SessionID, Frags: c.Frags, Morts: c.Deaths, Equipe: equipe})
	})
	if teamMode, ok := s.GameMode.(game.TeamMode); ok {
		for nom, t := range teamMode.Teams() {
			if t.Score != 0 {
				r.Equipes[nom] = t.Score
			} else {
				r.Equipes[nom] = t.Frags
			}
		}
	}
	return r
}

// Le tir est-il possible : arme en main, munitions, cadence, départ près du joueur ?
func (s *Server) g2eTirPossible(c *Client, wpn weapon.Weapon, id int32, from *geom.Vector) bool {
	if s.G2E == nil {
		return true
	}
	now := time.Now()
	if c.SelectedWeapon.ID != wpn.ID {
		return false
	}
	if now.Before(c.g2eProchainTir.Add(-margeCadence)) {
		return false
	}
	if c.Position != nil && geom.Distance(c.Position, from) > margeDepart {
		return false
	}
	base := c.g2eProchainTir
	if base.Before(now) {
		base = now
	}
	c.g2eProchainTir = base.Add(time.Duration(wpn.ReloadTime) * time.Millisecond)
	if wpn.ID == weapon.RocketLauncher || wpn.ID == weapon.GrenadeLauncher {
		c.g2eProjectiles[id] = projectile{arme: wpn.ID, tire: now}
	}
	return true
}

// Une cible touchée par un tir direct est-elle sur la ligne de tir ?
func (s *Server) g2eSurLaLigne(c *Client, target *Client, from, to *geom.Vector) bool {
	if s.G2E == nil {
		return true
	}
	if target == c || target.Position == nil {
		return target != c
	}
	return distanceAuSegment(target.Position, from, to) <= margeLigne
}

// Une explosion vient-elle d'un projectile vraiment tiré ?
func (s *Server) g2eExplosionPossible(c *Client, wpn weapon.Weapon, id int32) bool {
	if s.G2E == nil {
		return true
	}
	p, ok := c.g2eProjectiles[id]
	if !ok || p.arme != wpn.ID || time.Since(p.tire) > vieProjectile {
		return false
	}
	delete(c.g2eProjectiles, id)
	return true
}

func distanceAuSegment(p, a, b *geom.Vector) float64 {
	ab := b.Sub(a)
	l2 := ab.X()*ab.X() + ab.Y()*ab.Y() + ab.Z()*ab.Z()
	if l2 < 1e-9 {
		return geom.Distance(p, a)
	}
	ap := p.Sub(a)
	t := (ap.X()*ab.X() + ap.Y()*ab.Y() + ap.Z()*ab.Z()) / l2
	if t < 0 {
		t = 0
	} else if t > 1 {
		t = 1
	}
	proche := geom.NewVector(a.X()+ab.X()*t, a.Y()+ab.Y()*t, a.Z()+ab.Z()*t)
	return geom.Distance(p, proche)
}
