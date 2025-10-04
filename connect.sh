#!/bin/bash
# Script de connexion rapide au serveur
# Usage: ./connect.sh

REMOTE_USER="rgallon"
REMOTE_HOST="195.83.28.108"

echo "🔌 Connexion au serveur ${REMOTE_USER}@${REMOTE_HOST}..."
echo ""

ssh ${REMOTE_USER}@${REMOTE_HOST}
