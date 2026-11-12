# Game2Earn : le serveur de match de Sour (même système que la compilation : Ubuntu 24.04) (Cube 2), avec les paquets du jeu (cartes de Game2Earn).
# Construit par .github/workflows/game2earn.yml (job « image »), publié sur ghcr.io/<propriétaire>/g2e-sour-serveur.
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates zlib1g libstdc++6 \
    && rm -rf /var/lib/apt/lists/* && (userdel -r ubuntu 2>/dev/null || true) && useradd -m -u 1000 jeu
WORKDIR /jeu
COPY sour /jeu/sour
COPY paquets /jeu/assets
COPY game2earn/serveur/config.yaml game2earn/serveur/demarrer.sh /jeu/
RUN chmod +x /jeu/sour /jeu/demarrer.sh && chown -R jeu /jeu
USER jeu
# WebSocket des joueurs (et page du jeu, pour les essais)
EXPOSE 1337
CMD ["/jeu/demarrer.sh"]
