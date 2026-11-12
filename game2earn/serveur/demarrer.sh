#!/bin/sh
# Game2Earn : démarre le serveur de match. Le port vient d'Edgegap (ARBITRIUM_PORT_WEB_INTERNAL) s'il est donné.
set -e
cd /jeu
PORT="${ARBITRIUM_PORT_WEB_INTERNAL:-${G2E_PORT:-1337}}"
cat > port.yaml <<FIN
server:
  ingress:
    web:
      port: $PORT
FIN
exec ./sour serve config.yaml port.yaml
