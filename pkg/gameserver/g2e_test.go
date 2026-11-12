package gameserver

import (
	"testing"
	"time"

	"github.com/cfoust/sour/pkg/gameserver/geom"
	"github.com/cfoust/sour/pkg/gameserver/protocol/weapon"
)

func clientEssai() (*Server, *Client) {
	s := &Server{G2E: &G2EHooks{}}
	c := NewClient(0, 1, nil)
	c.SelectedWeapon = weapon.ByID(weapon.Rifle)
	c.Position = geom.NewVector(100, 100, 50)
	return s, c
}

func TestCadence(t *testing.T) {
	s, c := clientEssai()
	depart := geom.NewVector(100, 100, 50)
	if !s.g2eTirPossible(c, weapon.ByID(weapon.Rifle), 1, depart) {
		t.Fatal("le premier tir doit passer")
	}
	if s.g2eTirPossible(c, weapon.ByID(weapon.Rifle), 2, depart) {
		t.Fatal("un deuxième tir du fusil aussitôt doit être refusé")
	}
	c.g2eProchainTir = time.Now().Add(-time.Second)
	if !s.g2eTirPossible(c, weapon.ByID(weapon.Rifle), 3, depart) {
		t.Fatal("un tir après le rechargement doit passer")
	}
}

func TestArmeEtDepart(t *testing.T) {
	s, c := clientEssai()
	if s.g2eTirPossible(c, weapon.ByID(weapon.Shotgun), 1, geom.NewVector(100, 100, 50)) {
		t.Fatal("une arme qui n'est pas en main doit être refusée")
	}
	if s.g2eTirPossible(c, weapon.ByID(weapon.Rifle), 1, geom.NewVector(400, 100, 50)) {
		t.Fatal("un tir parti loin du joueur doit être refusé")
	}
}

func TestLigneDeTir(t *testing.T) {
	s, c := clientEssai()
	cible := NewClient(1, 2, nil)
	cible.Position = geom.NewVector(300, 110, 50)
	if !s.g2eSurLaLigne(c, cible, geom.NewVector(100, 100, 50), geom.NewVector(500, 100, 50)) {
		t.Fatal("une cible sur la ligne de tir doit être touchée")
	}
	cible.Position = geom.NewVector(300, 400, 50)
	if s.g2eSurLaLigne(c, cible, geom.NewVector(100, 100, 50), geom.NewVector(500, 100, 50)) {
		t.Fatal("une cible loin de la ligne de tir doit être refusée")
	}
	if s.g2eSurLaLigne(c, c, geom.NewVector(100, 100, 50), geom.NewVector(500, 100, 50)) {
		t.Fatal("on ne se touche pas soi-même d'un tir direct")
	}
}

func TestExplosionSansTir(t *testing.T) {
	s, c := clientEssai()
	c.SelectedWeapon = weapon.ByID(weapon.RocketLauncher)
	if s.g2eExplosionPossible(c, weapon.ByID(weapon.RocketLauncher), 7) {
		t.Fatal("une explosion sans tir doit être refusée")
	}
	s.g2eTirPossible(c, weapon.ByID(weapon.RocketLauncher), 7, geom.NewVector(100, 100, 50))
	if !s.g2eExplosionPossible(c, weapon.ByID(weapon.RocketLauncher), 7) {
		t.Fatal("l'explosion d'une roquette tirée doit passer")
	}
	if s.g2eExplosionPossible(c, weapon.ByID(weapon.RocketLauncher), 7) {
		t.Fatal("une roquette n'explose qu'une fois")
	}
}
