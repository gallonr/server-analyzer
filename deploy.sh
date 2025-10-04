#!/bin/bash
# Script de déploiement sur serveur distant
# Usage: ./deploy.sh

set -e  # Arrêter en cas d'erreur

# Configuration
REMOTE_USER="rgallon"
REMOTE_HOST="195.83.28.108"
REMOTE_PATH="~/server-analyzer"
LOCAL_PATH="/home/rgallon/Documents/RECHERCHE/GestionServeurIntechmer/server-analyzer"

echo "========================================="
echo "Déploiement Server Analyzer"
echo "========================================="
echo "Serveur: ${REMOTE_USER}@${REMOTE_HOST}"
echo "Chemin distant: ${REMOTE_PATH}"
echo ""

# Vérifier connexion SSH
echo "📡 Vérification connexion SSH..."
if ! ssh -o BatchMode=yes -o ConnectTimeout=5 ${REMOTE_USER}@${REMOTE_HOST} echo "OK" 2>/dev/null; then
    echo "❌ Impossible de se connecter au serveur"
    echo "   Vérifiez votre connexion SSH ou configurez les clés SSH"
    exit 1
fi
echo "✓ Connexion SSH OK"
echo ""

# Créer le dossier distant si nécessaire
echo "📁 Création du répertoire distant..."
ssh ${REMOTE_USER}@${REMOTE_HOST} "mkdir -p ${REMOTE_PATH}"
echo "✓ Répertoire créé"
echo ""

# Synchroniser les fichiers (exclure venv, cache, etc.)
echo "📤 Transfert des fichiers..."
rsync -avz --progress \
    --exclude='venv/' \
    --exclude='__pycache__/' \
    --exclude='.pytest_cache/' \
    --exclude='*.pyc' \
    --exclude='.git/' \
    --exclude='data/' \
    --exclude='logs/' \
    --exclude='config.yaml' \
    ${LOCAL_PATH}/ ${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PATH}/

echo "✓ Fichiers transférés"
echo ""

# Installer/mettre à jour l'environnement Python sur le serveur
echo "🐍 Configuration environnement Python distant..."
ssh ${REMOTE_USER}@${REMOTE_HOST} << 'ENDSSH'
cd ~/server-analyzer

# Vérifier Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 non trouvé sur le serveur"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo "Python version: ${PYTHON_VERSION}"

# Vérifier si python3-venv est installé
echo "Vérification de python3-venv..."
if ! python3 -m venv --help &> /dev/null; then
    echo "⚠️  python3-venv n'est pas installé"
    echo "📦 Installation de python3-venv (nécessite sudo)..."
    
    # Détecter la version de Python
    PYTHON_VER=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    
    # Installer python3-venv
    if sudo apt install -y python3-venv python${PYTHON_VER}-venv 2>/dev/null; then
        echo "✓ python3-venv installé avec succès"
    else
        echo "❌ Impossible d'installer python3-venv automatiquement"
        echo "   Veuillez exécuter manuellement:"
        echo "   sudo apt install python3-venv python${PYTHON_VER}-venv"
        exit 1
    fi
fi

# Créer venv si nécessaire
if [ ! -d "venv" ]; then
    echo "Création environnement virtuel..."
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Échec de la création de l'environnement virtuel"
        exit 1
    fi
    echo "✓ Environnement virtuel créé"
else
    echo "✓ Environnement virtuel déjà présent"
fi

# Vérifier que venv existe bien
if [ ! -f "venv/bin/activate" ]; then
    echo "❌ venv/bin/activate n'existe pas"
    echo "   Suppression et recréation de venv..."
    rm -rf venv
    python3 -m venv venv
    
    if [ $? -ne 0 ]; then
        echo "❌ Échec de la création de l'environnement virtuel"
        echo "   Vérifiez que python3-venv est installé:"
        echo "   sudo apt install python3-venv"
        exit 1
    fi
fi

# Activer et installer dépendances
echo "Installation des dépendances Python..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "❌ Impossible d'activer l'environnement virtuel"
    exit 1
fi

pip install --upgrade pip setuptools wheel -q

if [ $? -ne 0 ]; then
    echo "❌ Échec de mise à jour pip"
    exit 1
fi

pip install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "❌ Échec d'installation des dépendances"
    exit 1
fi

echo "✓ Environnement Python configuré"

# Vérifier config.yaml
if [ ! -f "config.yaml" ]; then
    echo "⚠️  config.yaml non trouvé, copie de l'exemple..."
    cp config.yaml.example config.yaml
    echo "   Pensez à éditer config.yaml avec les bons chemins!"
fi

# Créer les dossiers nécessaires
mkdir -p data/checkpoints data/exports logs

echo "✓ Structure de dossiers créée"
ENDSSH

echo ""
echo "========================================="
echo "✅ Déploiement terminé avec succès!"
echo "========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Connectez-vous au serveur:"
echo "   ssh ${REMOTE_USER}@${REMOTE_HOST}"
echo ""
echo "2. Configurez les chemins à analyser:"
echo "   cd ${REMOTE_PATH}"
echo "   nano config.yaml"
echo ""
echo "3. Testez la configuration:"
echo "   source venv/bin/activate"
echo "   python src/config_validator.py"
echo ""
echo "4. Lancez le scan (Phase 1):"
echo "   python scripts/run_scan.py"
echo ""
