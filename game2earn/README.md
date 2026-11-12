# Sour pour Game2Earn

Cette branche (`game2earn`) prépare Sour (Cube 2 : Sauerbraten dans le navigateur, serveur en Go) pour la plateforme
Game2Earn.

## Licences (tri du 12 novembre 2026)

- **Code** : libre, usage commercial permis. Moteur Cube 2 sous licence zlib, Sour (client web et serveur Go) sous MIT.
- **Contenus de Sauerbraten** : chaque pack a sa licence, et la licence du jeu interdit de les reprendre sans la mention
  explicite « tout usage » ou l'accord de l'auteur. Les éléments indispensables sont **non commerciaux** : les cartes
  (`packages/base`, CC BY-NC, BY-NC-SA, BY-NC-ND), les armes vues en main et les personnages (`packages/models`, CC
  BY-NC), les objets (munitions, soins, drapeaux), l'habillage des menus (`data/guiskin.png`...). **Ils ne sont pas
  utilisés par Game2Earn** et ne sont ni compilés ni publiés par la recette `game2earn.yml`.
- Réutilisables (licence permissive, à créditer) : textures `trak5` (MIT), `cloward`, `drakker` (domaine public),
  `lunaran`, `aftas` (partage à l'identique), `tomek` (CC BY), viseurs `crosshairs` (CC0), polices (Bitstream Vera et
  DejaVu).
- **Red Eclipse** (même famille de moteur) n'accepte aucun contenu non commercial : CC BY-SA ou CC BY. Ses textures,
  sons et modèles peuvent remplacer ceux de Sauerbraten (crédits et même licence pour nos dérivés). Ses cartes ne se
  chargent pas dans ce moteur : les cartes de Game2Earn seront faites avec l'éditeur du jeu.

## Recettes

- `.github/workflows/game2earn.yml` : compile le moteur (Emscripten 3.1.8), le client web et le serveur Go (SWIG 4.1.1),
  et en fait une archive (`sour-game2earn.tar.gz`), sans contenu.
