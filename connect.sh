#!/bin/bash
# Script de connexion rapide au serveur
# Usage: ./connect.sh

REMOTE_USER="user"
REMOTE_HOST="A DEFINIR"

echo "🔌 Connexion au serveur ${REMOTE_USER}@${REMOTE_HOST}..."
echo ""

ssh ${REMOTE_USER}@${REMOTE_HOST}
