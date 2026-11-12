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
- Réutilisables (licence permissive, à créditer) : textures `trak5` (MIT), `cloward` (tout usage), `drakker`
  (domaine public), `tomek` (CC BY), polices (Bitstream Vera et DejaVu). **Correction du 12 novembre** : `aftas` et
  `lunaran` interdisent l'usage commercial, et les viseurs `crosshairs` n'ont pas de licence claire : exclus.
- **Red Eclipse** (même famille de moteur) n'accepte aucun contenu non commercial : CC BY-SA ou CC BY. Ses textures,
  sons et modèles peuvent remplacer ceux de Sauerbraten (crédits et même licence pour nos dérivés). Ses cartes ne se
  chargent pas dans ce moteur : les cartes de Game2Earn seront faites avec l'éditeur du jeu.

## Contenus (`game2earn/contenus`)

- `fabriquer.py` assemble le dossier du jeu (« racine ») : réglages du moteur (zlib), images de l'interface, icônes,
  effets, ciel et eau **dessinés par programme** (`images.py`, à nous), textures libres, police DejaVu, sons de Red
  Eclipse (`sons.py`, CC BY-SA 4.0), cartes (`cartes/`), crédits (`credits.md`).
- `paquets.py` en fait les paquets du navigateur et du serveur (`.sour` et `.index.source`), sans Emscripten.
- `carte_essai.py` fabrique une arène d'essai ; la version de `cartes/` a son éclairage calculé dans le jeu.
- Le client web n'embarque plus d'images de Sauerbraten : icônes des armes et fond refaits (`images.py --client`).

## Recettes

- `.github/workflows/game2earn.yml` : compile le moteur (Emscripten 3.1.8), le client web et le serveur Go (SWIG 4.1.1),
  et en fait une archive (`sour-game2earn.tar.gz`), sans contenu ; le job `contenus` produit les paquets du jeu.
